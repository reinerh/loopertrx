#!/usr/bin/env python3
#
# loopertrx: import/export audio data from some looper pedals.
#
# Copyright (C) 2017  Reiner Herrmann <reiner@reiner-h.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import random
import struct
import sys
import argparse
import usb.core
import usb.util

LOOPER_VID = 0x0483
LOOPER_PID = 0x572a

ENDPOINT_IN  = 0x81
ENDPOINT_OUT = 0x01

COMMAND_SIZE = 0xfe
COMMAND_DATA = 0xff


class USBLooper():
    def __init__(self):
        self.dev = usb.core.find(idVendor=LOOPER_VID, idProduct=LOOPER_PID)
        if not self.dev:
            raise FileNotFoundError("Device not found.")
        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)
        self.dev.set_configuration()

    def random_tag(self):
        return random.randint(0, 1 << 32 - 1)

    def mass_storage_header(self, data_len, cdb_len, tag=None):
        header = "USBC".encode('ascii')
        if not tag:
            tag = self.random_tag()
        flags = 0x80
        target = 0x00
        header += struct.pack('<iiBBB', tag, data_len, flags, target, cdb_len)
        return header

    def command_header(self, command, data_len, flag1, flag2, tag=None):
        cdb = bytes([0xcb, command, flag1, 0x00, flag2, 0x00, 0x00, 0x00, 0x00, 0x00])
        header = self.mass_storage_header(data_len, len(cdb), tag) + cdb
        header += bytes([0x00 for padding in range(31-len(header))])
        return header

    def ack_data(self):
        self.dev.read(ENDPOINT_IN, 32)

    def get_size(self):
        header = self.command_header(COMMAND_SIZE, 5, 0x00, 0x01)
        self.dev.write(ENDPOINT_OUT, header)
        length = self.dev.read(ENDPOINT_IN, 100)
        self.ack_data()
        if length[0] == 1:
            return 0
        return length[1] + (length[2] << 8) + (length[3] << 16) + (length[4] << 24)

    def submit_data_len(self, size, tag=None):
        header = self.command_header(COMMAND_SIZE, 5, 0x00, 0x00, tag)
        data_size = struct.pack('<bi', 0x00, size)
        self.dev.write(ENDPOINT_OUT, header)
        self.dev.write(ENDPOINT_OUT, data_size)
        self.ack_data()

    def get_data(self, nbytes):
        header = self.command_header(COMMAND_DATA, nbytes, 0x01, 0x01)
        self.dev.write(ENDPOINT_OUT, header)
        buf = self.dev.read(ENDPOINT_IN, nbytes)
        self.ack_data()
        return buf

    def send_data(self, data, tag=None):
        header = self.command_header(COMMAND_DATA, len(data), 0x01, 0x00, tag)
        self.dev.write(ENDPOINT_OUT, header)
        self.dev.write(ENDPOINT_OUT, data)
        self.ack_data()

    def write_wav_header(self, outfile, data_size):
        header_size = 44
        header = "RIFF".encode('ascii')
        header += struct.pack('<i', data_size + header_size - 8)
        header += "WAVE".encode('ascii')
        header += "fmt ".encode('ascii')
        fmt = 0x01  # PCM
        nchan = 1
        rate = 48000
        fsize = 3
        bps = rate * fsize
        bits = 24
        header += struct.pack('<ihhiihh', 16, fmt, nchan, rate, bps, fsize, bits)
        header += "data".encode('ascii')
        header += struct.pack('<i', data_size)
        outfile.write(header)

    def receive_file(self, filename):
        size = self.get_size()
        if size == 0:
            print("No data available.")
            sys.exit(0)

        with open(filename, 'wb') as outfile:
            self.write_wav_header(outfile, size)
            print("Receiving ", end='', flush=True)
            while size > 0:
                bufsize = (size >= 65536) and 65536 or size
                # data needs to be transferred in multiples of 1k blocks
                padding = (1024 - (bufsize % 1024)) % 1024

                buf = self.get_data(bufsize + padding)
                print('.', end='', flush=True),
                outfile.write(buf[:bufsize])
                size -= bufsize
            print(" Done.")

    def transmit_file(self, filename):
        with open(filename, 'rb') as infile:
            content = infile.read()
            tag = self.random_tag()
            # skip first 44 bytes for now; we assume valid file. TODO: validate
            content = content[44:]
            content_size = len(content)
            print("Transmitting ", end='', flush=True)
            while len(content) > 0:
                buf = content[:65536]
                padsize = (1024 - (len(buf) % 1024)) % 1024
                buf += b'\x00' * padsize

                self.send_data(buf, tag)
                print('.', end='', flush=True),
                content = content[65536:]
            self.submit_data_len(content_size, tag)
            print(" Done.")


def main():
    argp = argparse.ArgumentParser()
    argp.add_argument('action', choices=['rx', 'tx'])
    argp.add_argument('filename')
    args = argp.parse_args()

    try:
        dev = USBLooper()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    if args.action == 'rx':
        dev.receive_file(args.filename)
    elif args.action == 'tx':
        dev.transmit_file(args.filename)


if __name__ == "__main__":
    main()
