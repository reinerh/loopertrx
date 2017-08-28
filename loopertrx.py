#!/usr/bin/env python3

import random
import struct
import sys
import usb.core
import usb.util

LOOPER_VID = 0x0483
LOOPER_PID = 0x572a

ENDPOINT_IN  = 0x81
ENDPOINT_OUT = 0x01

COMMAND_SIZE = 0xfe
COMMAND_DATA = 0xff

def mass_storage_header(data_len, cdb_len):
    header = "USBC".encode('ascii')
    tag = random.randint(0, 1<<32 - 1)
    flags = 0x80
    target = 0x00
    header += struct.pack('<iiBBB', tag, data_len, flags, target, cdb_len)
    return header

def command_header(command, data_len, flag1, flag2):
    cdb = bytes([0xcb, command, flag1, 0x00, flag2, 0x00, 0x00, 0x00, 0x00, 0x00])
    header = mass_storage_header(data_len, len(cdb)) + cdb
    header += bytes([0x00 for padding in range(31-len(header))])
    return header

def ack_data(dev):
    dev.read(ENDPOINT_IN, 32)

def get_size(dev):
    header = command_header(COMMAND_SIZE, 5, 0x00, 0x01)
    dev.write(ENDPOINT_OUT, header)
    length = dev.read(ENDPOINT_IN, 100)
    ack_data(dev)
    if length[0] == 1:
        return 0
    return length[1] + (length[2] << 8) + (length[3] << 16) + (length[4] << 24)

def get_data(dev, nbytes):
    header = command_header(COMMAND_DATA, nbytes, 0x01, 0x01)
    dev.write(ENDPOINT_OUT, header)
    buf = dev.read(ENDPOINT_IN, nbytes)
    ack_data(dev)
    print('.', end='', flush=True),
    return buf

def send_data(dev, data):
    header = command_header(COMMAND_DATA, len(data), 0x01, 0x00)
    dev.write(ENDPOINT_OUT, header)
    #dev.read(ENDPOINT_IN, 100)
    dev.write(ENDPOINT_OUT, data)

def send_stop(dev):
    header = command_header(COMMAND_SIZE, 5, 0x00, 0x00)

def write_wav_header(outfile, data_size):
    header_size = 44
    header = "RIFF".encode('ascii')
    header += struct.pack('<i', data_size + header_size - 8)
    header += "WAVE".encode('ascii')
    header += "fmt ".encode('ascii')
    fmt = 0x01 # PCM
    nchan = 1
    rate = 48000
    fsize = 3
    bps = rate * fsize
    bits = 24
    header += struct.pack('<ihhiihh', 16, fmt, nchan, rate, bps, fsize, bits)
    header += "data".encode('ascii')
    header += struct.pack('<i', data_size)
    outfile.write(header)

dev = usb.core.find(idVendor=LOOPER_VID, idProduct=LOOPER_PID)
if not dev:
    print("Device not found.")
    sys.exit(1)
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)
dev.set_configuration()

size = get_size(dev)
if size == 0:
    print("No data available.")
    sys.exit(0)

with open("/tmp/dump.wav", 'wb') as outfile:
    write_wav_header(outfile, size)
    print("Receiving ", end='', flush=True)
    while size > 0:
        bufsize = (size >= 65536) and 65536 or size
        # data needs to be transferred in multiples of 1k blocks
        padding = (1024 - (bufsize % 1024)) % 1024

        buf = get_data(dev, bufsize + padding)
        outfile.write(buf[:bufsize])
        size -= bufsize
    print(" Done.")
