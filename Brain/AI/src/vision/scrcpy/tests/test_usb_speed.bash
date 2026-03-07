#!/bin/bash
# 1. Create a 100MB dummy file
dd if=/dev/urandom of=test_file.bin bs=1M count=100

# 2. Push it to the phone to check the speed
adb push test_file.bin /sdcard/
