import re
import subprocess
from datetime import datetime
from tkinter.constants import N

from AI.src.constants import logger
from processed_phone_screen_data import extract_phone_screen_info


def get_wall_clock():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def run_monitor():
    curr_x = None
    curr_y = None
    active_touch = False
    scale_x, scale_y = extract_phone_screen_info()
    scale_x = scale_x[2]
    scale_y = scale_y[2]

    logger.info("Listening for ordered touch events... (Ctrl+C to stop)")

    cmd = ["adb", "exec-out", "getevent", "-lt"]
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    except FileNotFoundError:
        logger.error("adb not found. Please install it and try again.")
        raise FileNotFoundError

    # Regex patterns for speed
    re_x = re.compile(r"ABS_MT_POSITION_X\s+([0-9a-f]+)")
    re_y = re.compile(r"ABS_MT_POSITION_Y\s+([0-9a-f]+)")
    re_id = re.compile(r"ABS_MT_TRACKING_ID\s+([0-9a-f]+)")
    re_btn = re.compile(r"BTN_TOUCH\s+(DOWN|UP)")

    try:
        for line in process.stdout:
            time_str = get_wall_clock()

            match_x = re_x.search(line)
            if match_x:
                curr_x = int(match_x.group(1), 16) / scale_x

            match_y = re_y.search(line)
            if match_y:
                curr_y = int(match_y.group(1), 16) / scale_y

            match_id = re_id.search(line)
            match_btn = re_btn.search(line)

            is_start = (match_id and match_id.group(1) != "ffffffff") or (
                match_btn and match_btn.group(1) == "DOWN"
            )

            is_end = (match_id and match_id.group(1) == "ffffffff") or (
                match_btn and match_btn.group(1) == "UP"
            )

            if is_start and not active_touch:
                print(f"[{time_str}] 🟢 START TAP")
                active_touch = True

            if active_touch and curr_x is not None and curr_y is not None:
                print(f"[{time_str}] X:{round(curr_x):-4d} Y:{round(curr_y):-4d}")
                curr_x, curr_y = None, None

            if is_end and active_touch:
                print(f"[{time_str}] 🔴 END TAP")
                print("-" * 48)
                active_touch = False
                curr_x = curr_y = None

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        process.terminate()


if __name__ == "__main__":
    run_monitor()
