import subprocess
from typing import List

import numpy as np
from PIL import Image

from AI.src.stuffMerger.enums import Orientation, Direction


def _run_adb_screencap_to(path: str) -> None:
    with open(path, "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, check=True)



def _run_motionevent(parts: List[str]) -> None:
    subprocess.run(parts, check=True)


def get_perfect_horizontal_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = [600, 500, 400, 300, 200]
    if orientation != Orientation.DESCENDING:
        steps = steps[::-1]
    actions = [
        ["adb", "shell", "input", "motionevent", "DOWN", str(steps[0]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[1]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[2]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[3]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[4]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[0]), "1700"],
        ["adb", "shell", "input", "motionevent", "UP", str(steps[0]), "1700"],
    ]

    prefix = "r_" if orientation != Orientation.DESCENDING else ""
    _run_adb_screencap_to(f"{prefix}screenshot_0.png")
    _run_motionevent(actions[0])
    for index, action in enumerate(actions[1:-1]):
        _run_motionevent(action)
        _run_adb_screencap_to(f"{prefix}screenshot_{index + 1}.png")
    _run_motionevent(actions[-1])


def get_imperfect_horizontal_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = (
        [600, 497, 391, 294, 189]
        if orientation == Orientation.DESCENDING
        else [200, 297, 391, 494, 589]
    )
    actions = [
        ["adb", "shell", "input", "motionevent", "DOWN", str(steps[0]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[1]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[2]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[3]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[4]), "1700"],
        ["adb", "shell", "input", "motionevent", "MOVE", str(steps[0]), "1700"],
        ["adb", "shell", "input", "motionevent", "UP", str(steps[0]), "1700"],
    ]

    prefix = f"i_{'r_' if orientation != Orientation.DESCENDING else ''}"
    _run_adb_screencap_to(f"{prefix}screenshot_0.png")
    _run_motionevent(actions[0])
    for index, action in enumerate(actions[1:-1]):
        _run_motionevent(action)
        _run_adb_screencap_to(f"{prefix}screenshot_{index + 1}.png")
    _run_motionevent(actions[-1])


def get_perfect_vertical_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = [1700, 1600, 1500, 1400, 1300]
    if orientation != Orientation.DESCENDING:
        steps = steps[::-1]
    actions = [
        ["adb", "shell", "input", "motionevent", "DOWN", "600", str(steps[0])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[1])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[2])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[3])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[4])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[0])],
        ["adb", "shell", "input", "motionevent", "UP", "600", str(steps[0])],
    ]

    prefix = f"v_{'r_' if orientation != Orientation.DESCENDING else ''}"
    _run_adb_screencap_to(f"{prefix}screenshot_0.png")
    _run_motionevent(actions[0])
    for index, action in enumerate(actions[1:-1]):
        _run_motionevent(action)
        _run_adb_screencap_to(f"{prefix}screenshot_{index + 1}.png")
    _run_motionevent(actions[-1])


def get_imperfect_vertical_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = (
        [1700, 1597, 1491, 1394, 1289]
        if orientation == Orientation.DESCENDING
        else [1300, 1397, 1491, 1594, 1689]
    )
    actions = [
        ["adb", "shell", "input", "motionevent", "DOWN", "600", str(steps[0])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[1])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[2])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[3])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[4])],
        ["adb", "shell", "input", "motionevent", "MOVE", "600", str(steps[0])],
        ["adb", "shell", "input", "motionevent", "UP", "600", str(steps[0])],
    ]
    prefix = f"i_v_{'r_' if orientation != Orientation.DESCENDING else ''}"
    _run_adb_screencap_to(f"{prefix}screenshot_0.png")
    _run_motionevent(actions[0])
    for index, action in enumerate(actions[1:-1]):
        _run_motionevent(action)
        _run_adb_screencap_to(f"{prefix}screenshot_{index + 1}.png")
    _run_motionevent(actions[-1])


def get_image_set(
        perfect: bool = True,
        vertical: bool = False,
        orientation: Orientation = Orientation.DESCENDING,
):
    y_steps = [1700] * 5
    x_steps = [600] * 5

    if vertical:
        y_steps = (
            [1700, 1600, 1500, 1400, 1300]
            if orientation == Orientation.DESCENDING
            else [1300, 1400, 1500, 1600, 1700]
        ) if perfect else (
            [1700, 1597, 1491, 1394, 1289]
            if orientation == Orientation.DESCENDING
            else [1300, 1397, 1491, 1594, 1689]
        )
    else:
        x_steps = (
            [600, 500, 400, 300, 200]
            if orientation == Orientation.DESCENDING
            else [200, 300, 400, 500, 600]
        ) if perfect else (
            [600, 497, 391, 294, 189]
            if orientation == Orientation.DESCENDING
            else [200, 297, 391, 494, 589]
        )

    actions = [
        ["adb", "shell", "input", "motionevent", "DOWN", str(x_steps[0]), str(y_steps[0])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[1]), str(y_steps[1])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[2]), str(y_steps[2])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[3]), str(y_steps[3])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[4]), str(y_steps[4])],
        ["adb", "shell", "input", "motionevent", "MOVE", str(x_steps[0]), str(y_steps[0])],
        ["adb", "shell", "input", "motionevent", "UP", str(x_steps[0]), str(y_steps[0])],
    ]

    image_prefix = f"{'i_' if not perfect else ''}{'v_' if vertical else ''}{'r_' if orientation != Orientation.DESCENDING else ''}"
    _run_adb_screencap_to(f"{image_prefix}screenshot_0.png")
    _run_motionevent(actions[0])
    for index, action in enumerate(actions[1:-1]):
        _run_motionevent(action)
        _run_adb_screencap_to(f"{image_prefix}screenshot_{index + 1}.png")
    _run_motionevent(actions[-1])


# def get_custom_image(
#         orientation: Orientation = Orientation.DESCENDING,
#         direction: Direction = Direction.HORIZONTAL,
#         offset: int = 0,
#         start_x: int = 540,
#         start_y: int = 1200,
#         name: str = "screenshot.png",
# ) -> Image.Image:
#     if offset <= 0:
#         raise ValueError("offset must be positive")
#     end_x = start_x
#     end_y = start_y
#     if direction == Direction.HORIZONTAL:
#         end_x = start_x - offset if orientation == Orientation.DESCENDING else start_x + offset
#     else:
#         end_y = start_y - offset if orientation == Orientation.DESCENDING else start_y + offset
#
#     _run_motionevent(["adb", "shell", "input", "motionevent", "DOWN", str(start_x), str(start_y)])
#     _run_motionevent(["adb", "shell", "input", "motionevent", "MOVE", str(end_x), str(end_y)])
#     _run_motionevent(["adb", "shell", "input", "motionevent", "UP", str(end_x), str(end_y)])
#     _run_adb_screencap_to(name)
#     img = Image.open(name)
#     img.load()
#     return img

def get_custom_image(
        orientation: Orientation = Orientation.DESCENDING,
        direction: Direction = Direction.HORIZONTAL,
        offset: int = 0,
        start_x: int = 540,
        start_y: int = 1200,
        name: str = "screenshot.png"
):
    img = Image.open(name)
    img.load()
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


def get_image() -> Image.Image:
    # _run_adb_screencap_to("screenshot.png")
    img = Image.open("x_0.png")
    img.load()
    return img


def make_alpha_mask_from_bw(_img: Image.Image, name: str = "ignoreZone") -> Image.Image:
    img = _img.convert("RGBA")
    arr = np.array(img)
    # mask True per pixel completamente bianchi (R=G=B=A=255)
    white_mask = np.all(arr == 255, axis=2)
    arr[~white_mask, 3] = 0
    result = Image.fromarray(arr)
    result.save(f"{name}.png")
    return result
