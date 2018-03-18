#!/bin/bash

signed_kext_status=$(csrutil status)
if [[ $signed_kext_status = *"enabled"* ]]; then
  echo "**MAC OSX ERROR** Unsigned kernex extentions not allowed! To allow them restart in recovery OS by restarting and holding Cmd+R, open a shell and run 'csrutil disable'"
  exit 1
fi
