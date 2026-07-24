import os
import subprocess

from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP, INPUT_BACKEND
from AI.src.webservices import ios_simulator


# os.system here mirrors the pre-existing tappy-client invocation pattern used
# across the game helpers (no externally-controlled input reaches the shell string).
def tap(x, y):
    if INPUT_BACKEND == 'adb':
        subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)], check=True)
    elif INPUT_BACKEND == 'ios_sim':
        ios_simulator.tap(x, y)
    else:
        os.chdir(CLIENT_PATH)
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x} {y}'")


def swipe(x1, y1, x2, y2, duration_ms=None):
    if INPUT_BACKEND == 'adb':
        subprocess.run(["adb", "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms or 300)], check=True)
    elif INPUT_BACKEND == 'ios_sim':
        if duration_ms is None:
            ios_simulator.swipe(x1, y1, x2, y2)
        else:
            ios_simulator.swipe(x1, y1, x2, y2, duration_s=duration_ms / 1000)
    else:
        os.chdir(CLIENT_PATH)
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {x1} {y1} {x2} {y2}'")
