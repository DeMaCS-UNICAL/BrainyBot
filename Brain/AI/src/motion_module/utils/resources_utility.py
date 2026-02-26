import subprocess
import random
from contextlib import AbstractContextManager
from typing import List
import struct

import numpy as np
from PIL import Image

import os
from AI.src.constants import SCREENSHOT_PATH, CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP, logger
from AI.src.motion_module.enums import Orientation, Direction
from AI.src.webservices.helpers import get_screenshot


def _run_motionevent(parts: List[str] | str) -> None:
    if isinstance(parts, str):
        os.system(parts)
    else:
        subprocess.run(parts, check=True)

def get_custom_image_set(
        orientation: Orientation = Orientation.DESCENDING,
        direction: Direction = Direction.HORIZONTAL,
        offset: int = 100,
        step_number: int = 4,
        start_x: int = 540,
        start_y: int = 1200,
) -> List[Image.Image]:
    if offset <= 0:
        raise ValueError("offset must be positive")
    if step_number < 1:
        raise ValueError("step_number must be at least 1")

    end_x = start_x
    end_y = start_y
    images: List[Image.Image] = []

    _run_motionevent(["adb", "shell", "input", "motionevent", "DOWN", str(start_x), str(start_y)])
    for i in range(step_number):
        if direction == Direction.HORIZONTAL:
            end_x = start_x + offset * (i + 1) if orientation == Orientation.DESCENDING else start_x - offset * (i + 1)
        else:
            end_y = start_y + offset * (i + 1) if orientation == Orientation.DESCENDING else start_y - offset * (i + 1)
        _run_motionevent(["adb", "shell", "input", "motionevent", "MOVE", str(end_x), str(end_y)])
        get_screenshot(
            save_path=os.getcwd(),
            filename=f"screenshot.png",
        )
        img = Image.open("screenshot.png")
        img.load()
        images.append(img)

    _run_motionevent(["adb", "shell", "input", "motionevent", "UP", str(end_x), str(end_y)])
    return images

def generate_steps(
        start: int,
        step_size: int,
        count: int,
        perfect: bool,
        orientation: Orientation
) -> List[int]:
    steps = [start]
    current = start
    direction = -1 if orientation == Orientation.DESCENDING else 1

    for _ in range(count):
        delta = step_size
        if not perfect:
            noise = random.randint(-5, 5)
            delta += noise

        current += delta * direction
        steps.append(current)
    return steps

def get_image_set(
        perfect: bool = True,
        vertical: bool = False,
        horizontal: bool = False,
        orientation: Orientation = Orientation.DESCENDING,
        save_location: str = "",
        step_size: int = 100,
        start_x: int | None = None,
        start_y: int | None = None,
):
    """
    Generates image set by simulating motion events and capturing screenshots,
    works best if used with adb for more precise movements
    [REQUIRED] a device with android 13 or higher or that support adb -> motionevent
    [WARNING] if save_location is provided it should end with "/"
    """
    if start_x is None:
        start_x = 200 if horizontal and orientation == Orientation.ASCENDING else 600
    if start_y is None:
        start_y = 1300 if vertical and orientation == Orientation.ASCENDING else 1700

    count = 5

    if not vertical and not horizontal:
        raise ValueError("At least one of vertical or horizontal must be True")

    # if vertical:
    #     match (orientation, perfect):
    #         case (Orientation.DESCENDING, True): y_steps = [1700, 1600, 1500, 1400, 1300]
    #         case (Orientation.ASCENDING, True): y_steps = [1300, 1400, 1500, 1600, 1700]
    #         case (Orientation.DESCENDING, False): y_steps = [1700, 1597, 1491, 1394, 1289]
    #         case (Orientation.ASCENDING, False): y_steps = [1300, 1397, 1491, 1594, 1689]
    # if horizontal:
    #     match (orientation, perfect):
    #         case (Orientation.DESCENDING, True): x_steps = [600, 500, 400, 300, 200]
    #         case (Orientation.ASCENDING, True): x_steps = [200, 300, 400, 500, 600]
    #         case (Orientation.DESCENDING, False): x_steps = [600, 497, 391, 294, 189]
    #         case (Orientation.ASCENDING, False): x_steps = [200, 297, 391, 494, 589]

    # actions = [
    #     ["adb", "shell", "input", "motionevent", "DOWN", str(x_steps[0]), str(y_steps[0])],
    #     ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[1]), str(y_steps[1])],
    #     ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[2]), str(y_steps[2])],
    #     ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[3]), str(y_steps[3])],
    #     ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[4]), str(y_steps[4])],
    #     ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[0]), str(y_steps[0])],
    #     ["adb", "shell", "input", "motionevent", "UP", str(x_steps[0]), str(y_steps[0])],
    # ]
    
    x_steps = [start_x] * count
    y_steps = [start_y] * count
    
    if vertical:
        y_steps = generate_steps(start_y, step_size, count, perfect, orientation)
    if horizontal:
        x_steps = generate_steps(start_x, step_size, count, perfect, orientation)

    actions = [
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {start_x} {start_y} {end_x} {end_y}'"
        for start_x, start_y, end_x, end_y in zip(x_steps, y_steps, x_steps[1:], y_steps[1:])
    ]
    actions.append(
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {x_steps[-1]} {y_steps[-1]} {x_steps[0]} {y_steps[0]}'"
    )
    
    image_prefix = f"{'i_' if not perfect else ''}{'v_' if vertical else ''}{'h_' if horizontal else ''}{'r_' if orientation != Orientation.DESCENDING else ''}"
    
    get_screenshot(save_path=save_location, filename=f"{image_prefix}screenshot_0.png")
    for index, action in enumerate(actions[1:]):
        with DoStuffElsewhere(CLIENT_PATH):
            _run_motionevent(action)
        get_screenshot(save_path=save_location, filename=f"{image_prefix}screenshot_{index + 1}.png")
    _run_motionevent(actions[-1])

def make_alpha_mask_from_bw(_img: Image.Image, name: str = "ignoreZone") -> Image.Image:
    img = _img.convert("RGBA")
    arr = np.array(img)
    # mask True per pixel completamente bianchi (R=G=B=A=255)
    white_mask = np.all(arr == 255, axis=2)
    arr[~white_mask, 3] = 0
    result = Image.fromarray(arr)
    result.save(f"{name}.png")
    return result


class DoStuffElsewhere(AbstractContextManager):
    """
    Allows you to run code in a different directory
    When you use with 'with', it will restore the previous directory on exit
    """
    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.old_directory)
    
    def __enter__(self):
        self.old_directory = os.getcwd()
        try:
            os.chdir(self.location)
        except Exception as e:
            logger.error(f"Failed to change directory to {self.location}: {e}")
            raise e
        return self
    
    def __init__(self, location: str) -> None:
        self.location = location
        self.old_directory: str
        
        

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bw_image", type=str, help="Path to the black and white image to generate the alpha mask from")
    parser.add_argument("--save_location", type=str, default="", help="Path to save the generated alpha mask")
    parser.add_argument("--name", type=str, default="ignoreZone", help="Name of the generated alpha mask")
    args = parser.parse_args()
    if args.bw_image:
        make_alpha_mask_from_bw(Image.open(args.bw_image), args.name if args.save_location == "" else f"{args.save_location}/{args.name}")
        logger.info("Alpha mask generated successfully")
    sys.exit(0)