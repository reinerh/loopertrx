#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KEXT_PATH="/System/Library/Extensions/AmmoonLooperUsb.kext/Contents/"

${SCRIPT_DIR}/osx_check.sh

mkdir -p "${KEXT_PATH}"
cp "${SCRIPT_DIR}"/resources/Info.plist "${KEXT_PATH}"

kextload /System/Library/Extensions/AmmoonLooperUsb.kext
touch /System/Library/Extensions

