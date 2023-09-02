import sys

#
# Decodes tapping events from ADB. To be invoked connecting a phone in developer mode and invoking from PC
# adb shell getevent | <this_script>
#

x = None
y = None

for line in sys.stdin:
    parts = line.strip().split()

    if len(parts) < 3:
        continue
    print (parts)
    event_type = parts[0]
    event_code = parts[1]
    event_value = int(parts[2], 16)

    # Check if the event is for ABS_MT_POSITION_X
    if event_type == "0003" and event_code == "0035":
        x = event_value

    # Check if the event is for ABS_MT_POSITION_Y
    elif event_type == "0003" and event_code == "0036":
        y = event_value

    # If both X and Y are captured and there's a SYN event, consider it a tap
    elif x is not None and y is not None and event_type == "0000" and event_code == "0000":
        print(f"TAP {x} {y}")
        x, y = None, None
