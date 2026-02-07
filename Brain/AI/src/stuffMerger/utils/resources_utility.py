import subprocess
from typing import List

import numpy as np
from PIL import Image

import os
from AI.src.constants import SCREENSHOT_PATH, CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP

from AI.src.stuffMerger.enums import Orientation, Direction


def _run_adb_screencap_to(path: str) -> None:
    with open(path, "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, check=True)


def _run_motionevent(parts: List[str]) -> None:
    subprocess.run(parts, check=True)


def get_custom_image(
        orientation: Orientation = Orientation.DESCENDING,
        direction: Direction = Direction.HORIZONTAL,
        offset: int = 0,
        start_x: int = 540,
        start_y: int = 1200,
        name: str = "screenshot.png",
) -> Image.Image:
    if offset <= 0:
        raise ValueError("offset must be positive")
    end_x = start_x
    end_y = start_y
    if direction == Direction.HORIZONTAL:
        end_x = start_x - offset if orientation == Orientation.DESCENDING else start_x + offset
    else:
        end_y = start_y - offset if orientation == Orientation.DESCENDING else start_y + offset
    
    # _run_motionevent(["adb", "shell", "input", "motionevent", "DOWN", str(start_x), str(start_y)])
    # _run_motionevent(["adb", "shell", "input", "motionevent", "MOVE", str(end_x), str(end_y)])
    # _run_motionevent(["adb", "shell", "input", "motionevent", "UP", str(end_x), str(end_y)])
    
    old_directory: str = os.getcwd()
    os.chdir(CLIENT_PATH)
    os.system(
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {start_x} {start_y} {end_x} {end_y}'")
    os.chdir(old_directory)
    
    return get_image(name)


# def get_custom_image(
#         orientation: Orientation = Orientation.DESCENDING,
#         direction: Direction = Direction.HORIZONTAL,
#         offset: int = 0,
#         start_x: int = 540,
#         start_y: int = 1200,
#         name: str = "screenshot.png"
# ):
#     img = Image.open(name)
#     img.load()
#     return img

def get_image(name: str | None = "screenshot.png") -> Image.Image:
    old_directory: str = os.getcwd()
    os.chdir(SCREENSHOT_PATH)
    _run_adb_screencap_to(name)
    img = Image.open(name)
    img.load()
    os.chdir(old_directory)
    return img

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
        _run_adb_screencap_to("screenshot.png")
        img = Image.open("screenshot.png")
        img.load()
        images.append(img)

    _run_motionevent(["adb", "shell", "input", "motionevent", "UP", str(end_x), str(end_y)])
    return images

def get_image_set(
        perfect: bool = True,
        vertical: bool = False,
        horizontal: bool = False,
        orientation: Orientation = Orientation.DESCENDING,
        save_location: str = "",
):
    """
    Generates image set by simulating motion events and capturing screenshots,
    works best if used with adb for more precise movements
    [REQUIRED] a device with android 13 or higher or that support adb -> motionevent
    [WARNING] if save_location is provided it should end with "/"
    """
    y_steps = [1700] * 5
    x_steps = [600] * 5

    if not vertical and not horizontal:
        raise ValueError("At least one of vertical or horizontal must be True")

    if vertical:
        match (orientation, perfect):
            case (Orientation.DESCENDING, True): y_steps = [1700, 1600, 1500, 1400, 1300]
            case (Orientation.ASCENDING, True): y_steps = [1300, 1400, 1500, 1600, 1700]
            case (Orientation.DESCENDING, False): y_steps = [1700, 1597, 1491, 1394, 1289]
            case (Orientation.ASCENDING, False): y_steps = [1300, 1397, 1491, 1594, 1689]
    if horizontal:
        match (orientation, perfect):
            case (Orientation.DESCENDING, True): x_steps = [600, 500, 400, 300, 200]
            case (Orientation.ASCENDING, True): x_steps = [200, 300, 400, 500, 600]
            case (Orientation.DESCENDING, False): x_steps = [600, 497, 391, 294, 189]
            case (Orientation.ASCENDING, False): x_steps = [200, 297, 391, 494, 589]

    actions = [
        ["adb", "shell", "input", "motionevent", "DOWN", str(x_steps[0]), str(y_steps[0])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[1]), str(y_steps[1])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[2]), str(y_steps[2])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[3]), str(y_steps[3])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[4]), str(y_steps[4])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[0]), str(y_steps[0])],
        ["adb", "shell", "input", "motionevent", "UP", str(x_steps[0]), str(y_steps[0])],
    ]

    # old_prefix: image_prefix = f"{'i_' if not perfect else ''}{'v_' if vertical else ''}{'r_' if orientation != Orientation.DESCENDING else ''}"
    image_prefix = f"{'i_' if not perfect else ''}{'v_' if vertical else ''}{'h_' if horizontal else ''}{'r_' if orientation != Orientation.DESCENDING else ''}"
    
    _run_adb_screencap_to(f"{save_location}{image_prefix}screenshot_0.png")
    _run_motionevent(actions[0])
    for index, action in enumerate(actions[1:-1]):
        _run_motionevent(action)
        _run_adb_screencap_to(f"{image_prefix}screenshot_{index + 1}.png")
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