#!/bin/bash

adb shell dumpsys input | grep -E "Touch Input Mapper|X:|Y:"
