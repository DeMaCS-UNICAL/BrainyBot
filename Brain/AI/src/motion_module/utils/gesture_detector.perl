#!/usr/bin/perl
use strict;
use warnings;
use Time::HiRes qw(gettimeofday);

# Force immediate output
$| = 1;

my ($curr_x, $curr_y, $active_touch);
$active_touch = 0;

print "Listening for ordered touch events... (Ctrl+C to stop)\n";

# Using exec-out for direct binary stream
open(my $adb, "adb exec-out 'getevent -lt' |") or die "Error: $!";

while (<$adb>) {
    my $line = $_;
    my $time = get_wall_clock();

    # 1. Capture Coordinates into variables (don't print yet)
    if ($line =~ /ABS_MT_POSITION_X\s+([0-9a-f]+)/) {
        $curr_x = hex($1);
    }
    if ($line =~ /ABS_MT_POSITION_Y\s+([0-9a-f]+)/) {
        $curr_y = hex($1);
    }

    # 2. Detect START Signal
    if (($line =~ /ABS_MT_TRACKING_ID\s+([0-9a-f]+)/ && $1 ne "ffffffff") || $line =~ /BTN_TOUCH\s+DOWN/) {
        if (!$active_touch) {
            print "[$time] 🟢 START TAP\n";
            $active_touch = 1;
            # If coordinates arrived in the same millisecond as the start, print them now
            flush_coords($time);
        }
    }

    # 3. If we are already in a touch, print coordinates as they change
    if ($active_touch && defined $curr_x && defined $curr_y) {
        flush_coords($time);
    }

    # 4. Detect END Signal
    if ($line =~ /ABS_MT_TRACKING_ID\s+ffffffff/ || $line =~ /BTN_TOUCH\s+UP/) {
        if ($active_touch) {
            # Print any final coordinates before closing
            flush_coords($time) if (defined $curr_x && defined $curr_y);
            print "[$time] 🔴 END TAP\n";
            print "------------------------------------------------\n";
            $active_touch = 0;
            undef $curr_x; undef $curr_y;
        }
    }
}

sub flush_coords {
    my ($time) = @_;
    if (defined $curr_x && defined $curr_y) {
        printf "[%s] X:%-4d Y:%-4d\n", $time, $curr_x, $curr_y;
        undef $curr_x; undef $curr_y; # Clear so we don't double-print
    }
}

sub get_wall_clock {
    my ($s, $usec) = gettimeofday();
    my ($sec, $min, $hour) = localtime($s);
    return sprintf("%02d:%02d:%02d.%03d", $hour, $min, $sec, $usec / 1000);
}
