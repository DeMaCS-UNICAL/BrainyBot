#!/usr/bin/perl
use strict;
use warnings;

my ($x, $y);

while (<STDIN>) {
    #print;
    chomp;
    my @parts = /.*: ([0-9a-fA-F]{4}) ([0-9a-fA-F]{4}) ([0-9a-fA-F]{8})/;

    next unless @parts >= 3;

    my ($event_type, $event_code, $event_value_hex) = @parts;
    my $event_value = hex($event_value_hex);

    # Check if the event is for ABS_MT_POSITION_X
    if ($event_type eq "0003" && $event_code eq "0035") {
        $x = $event_value;
        #print "X: $x\n";
    }
    # Check if the event is for ABS_MT_POSITION_Y
    elsif ($event_type eq "0003" && $event_code eq "0036") {
        $y = $event_value;
        #print "Y: $y\n";
    }
    # If both X and Y are captured and there's a SYN event, consider it a tap
    elsif (defined $x && defined $y && $event_type eq "0000" && $event_code eq "0000") {
        print "TAP $x $y\n";
        undef $x;
        undef $y;
    }
}
