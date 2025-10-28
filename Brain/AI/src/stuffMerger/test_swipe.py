import os
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP

if __name__ == "__main__":
    size = (1080, 2400)
    ox, dx = int(size[0] / 2 * 1), int(size[0] / 2 * 1)
    oy, dy = int(size[1] / 2 * 1.5), int(size[1] / 2 * 0.5)

    os.chdir(CLIENT_PATH)

    movements = [
        "adb shell input motionevent DOWN 600 1700",
        "adb shell input motionevent MOVE 500 1700",
        "adb shell input motionevent MOVE 400 1700",
        "adb shell input motionevent MOVE 300 1700",
        "adb shell input motionevent MOVE 200 1700",
        "adb shell input motionevent UP 200 1700"
    ]

    # something = f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {675} {1700} {135} {1700}'",

    movementsClient = [
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'down {675} {1700}'",
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'move {135} {1700}'",
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'up {135} {1700}'"
        # "python3 client3.py --url http://127.0.0.1:8000 --light 'down 540 1200'",
        # "python3 client3.py --url http://127.0.0.1:8000 --light 'move 540 1200'",
    ]

    for move in movements:
        os.system(move)

    # os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {ox} {oy} {dx} {dy}'")