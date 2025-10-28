import os
import time

from matplotlib.transforms import offset_copy

from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from PIL import ImageDraw, Image
import matplotlib.pyplot as plt
from enum import Enum

# north, east, south, west
# ox, dx, oy, dy
actions_coefficient = (
    (1, 1, .25, 1.25),
    (1.25, .25, 1, 1),
    (1, 1, 1.25, .25),
    (.25, 1.25, 1, 1),
)
ac = actions_coefficient


actions_direction = (
    (0, 100),
    (-100, 0),
    (0, -100),
    (100, 0),
)
ad = actions_direction


offsets = 0, 0

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


direction = 0

if __name__ == "__main__":
    os.chdir("resources")


    for x in range(4):
        direction = (x+1)%4

        os.system("adb exec-out screencap -p > screenshot.png")
        with Image.open("screenshot.png") as im:
            size = (im.size[0], im.size[1])
            # ox, dx, oy, dy = im.width//2*ac[direction][0]+offsets[0], im.width//2*ac[direction][1]+offsets[0], im.height//2*ac[direction][2]+offsets[1], im.height//2*ac[direction][3]+offsets[1]
            ox, dx, oy, dy = im.width//2+offsets[0], im.width//2+ad[direction][0]+offsets[0], im.height//2+offsets[1], im.height//2+ad[direction][1]+offsets[1]

            # Display
            draw = ImageDraw.Draw(im)
            draw.line((ox, oy, dx, dy), fill="red", width=4)
            draw.circle((ox, oy), radius=14, fill="green", width=4)
            draw.circle((ox, oy), radius=10, fill="blue", width=4)
            draw.circle((dx, dy), radius=24, fill="green", width=4)
            draw.circle((dx, dy), radius=20, fill="blue", width=4)
            plt.imshow(im)
            plt.show()

            # Action
            os.chdir(CLIENT_PATH)

            movements = [
                f"adb shell input motionevent DOWN {ox} {oy}",
                f"adb shell input motionevent MOVE {dx} {dy}",
                "sleep 0.10\n",
                f"adb shell input motionevent UP {dx} {dy}"
            ]
            movementsClient = [
                f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'down {ox} {oy}'",
                f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'move {dx} {dy}'",
                f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'up {dx} {dy}'"
            ]
            
            for move in movementsClient:
                print(move)
                os.system(move)
            # os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {int(ox)} {int(oy)} {int(dx)} {int(dy)}'")
            # os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {int(ox)} {int(oy)} {int(dx)} {int(dy)}'")
    time.sleep(1)
    os.system("adb exec-out screencap -p > screenshot.png")
    with Image.open("screenshot.png") as im:
        plt.imshow(im)
        plt.show()
