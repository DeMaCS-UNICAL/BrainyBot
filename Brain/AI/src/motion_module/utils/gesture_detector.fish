#!/usr/bin/fish
#!ho usato perl... sono molto depresso dalle mie azioni...
adb exec-out getevent -lt | perl -ne '
    if (/\[\s*([\d.]+)\].*ABS_MT_POSITION_X\s+([0-9a-f]+)/) {
        $t=$1; $x=hex($2);
    }
    if (/\[\s*([\d.]+)\].*ABS_MT_POSITION_Y\s+([0-9a-f]+)/) {
        $t=$1; $y=hex($2);
        if (defined $x) {
            printf("[%s] X: %d, Y: %d\n", $t, $x, $y);
            undef $x; # Reset for next touch point
        }
    }'
#!Spero non ci abbiate creduto, lho fatto scrivere a una AI a caso... col ***** che uso perl!