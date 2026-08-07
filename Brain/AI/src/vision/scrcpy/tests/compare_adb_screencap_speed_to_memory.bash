#!/bin/bash

echo -n "Png: "
time adb exec-out "screencap -p" > /dev/null

echo -n "Raw: "
time adb exec-out "screencap" > /dev/null

for lv in 1 2 3 4 5 6 7 8 9; do
    echo -n "Level -$lv: "
    time adb exec-out "screencap | gzip -$lv" > /dev/null
done
