import os

import numpy as np
from PIL import Image

from AI.src.stuffMerger.enums import Orientation


def get_perfect_horizontal_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = [
        600,
        500,
        400,
        300,
        200
    ]
    if orientation != 0:
        steps = steps[::-1]
    actions = [
        f"adb shell input motionevent DOWN {steps[0]} 1700",
        f"adb shell input motionevent MOVE {steps[1]} 1700",
        f"adb shell input motionevent MOVE {steps[2]} 1700",
        f"adb shell input motionevent MOVE {steps[3]} 1700",
        f"adb shell input motionevent MOVE {steps[4]} 1700",
        f"adb shell input motionevent MOVE {steps[0]} 1700",
        f"adb shell input motionevent UP {steps[0]} 1700"
    ]

    os.system(f"adb exec-out screencap -p > {'r_' if orientation != Orientation.DESCENDING else ''}screenshot_{0}.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > {'r_' if orientation != Orientation.DESCENDING else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_imperfect_horizontal_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = [
        600,
        497,
        391,
        294,
        189
    ] if orientation == 0 else [
        200,
        297,
        391,
        494,
        589
    ]
    actions = [
        f"adb shell input motionevent DOWN {steps[0]} 1700",
        f"adb shell input motionevent MOVE {steps[1]} 1700",
        f"adb shell input motionevent MOVE {steps[2]} 1700",
        f"adb shell input motionevent MOVE {steps[3]} 1700",
        f"adb shell input motionevent MOVE {steps[4]} 1700",
        f"adb shell input motionevent MOVE {steps[0]} 1700",
        f"adb shell input motionevent UP {steps[0]} 1700"
    ]

    os.system(f"adb exec-out screencap -p > i_{'r_' if orientation != Orientation.DESCENDING else ''}screenshot_0.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > i_{'r_' if orientation != Orientation.DESCENDING else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_perfect_vertical_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = [
        1700,
        1600,
        1500,
        1400,
        1300
    ]
    if orientation != 0:
        steps = steps[::-1]
    actions = [
        f"adb shell input motionevent DOWN 600 {steps[0]}",
        f"adb shell input motionevent MOVE 600 {steps[1]}",
        f"adb shell input motionevent MOVE 600 {steps[2]}",
        f"adb shell input motionevent MOVE 600 {steps[3]}",
        f"adb shell input motionevent MOVE 600 {steps[4]}",
        f"adb shell input motionevent MOVE 600 {steps[0]}",
        f"adb shell input motionevent UP 600 {steps[0]}"
    ]

    os.system(f"adb exec-out screencap -p > v_{'r_' if orientation != Orientation.DESCENDING else ''}screenshot_{0}.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > v_{'r_' if orientation != Orientation.DESCENDING else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_imperfect_vertical_dataset(orientation: Orientation = Orientation.DESCENDING):
    steps = [
        1700,
        1597,
        1491,
        1394,
        1289
    ] if orientation == 0 else [
        1300,
        1397,
        1491,
        1594,
        1689
    ]
    actions = [
        f"adb shell input motionevent DOWN 600 {steps[0]}",
        f"adb shell input motionevent MOVE 600 {steps[1]}",
        f"adb shell input motionevent MOVE 600 {steps[2]}",
        f"adb shell input motionevent MOVE 600 {steps[3]}",
        f"adb shell input motionevent MOVE 600 {steps[4]}",
        f"adb shell input motionevent MOVE 600 {steps[0]}",
        f"adb shell input motionevent UP 600 {steps[0]}"
    ]
    os.system(f"adb exec-out screencap -p > i_v_{'r_' if orientation != Orientation.DESCENDING else ''}screenshot_0.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > i_v_{'r_' if orientation != Orientation.DESCENDING else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_image_set(
        perfect: bool = True,
        vertical: bool = False,
        orientation: Orientation = Orientation.DESCENDING,
):
    y_steps = [1700] * 5
    x_steps = [600] * 5

    if vertical:
        y_steps = ([ # top to bottom
        1700,
        1600,
        1500,
        1400,
        1300
    ] if orientation == Orientation.DESCENDING else [ # bottom to top
        1300,
        1400,
        1500,
        1600,
        1700
    ]) if perfect else ([ # top to bottom with errors
        1700,
        1597,
        1491,
        1394,
        1289
    ] if orientation == Orientation.DESCENDING else [ # bottom to top with errors
        1300,
        1397,
        1491,
        1594,
        1689
    ])
    else:
        x_steps = ([ # right to left
        600,
        500,
        400,
        300,
        200
    ] if orientation == Orientation.DESCENDING else [ # left to right
        200,
        300,
        400,
        500,
        600
    ]) if perfect else ([ # right to left with errors
        600,
        497,
        391,
        294,
        189
    ] if orientation == Orientation.DESCENDING else [ # left to right with errors
        200,
        297,
        391,
        494,
        589
    ])

    actions = [
        f"adb shell input motionevent DOWN {x_steps[0]} {y_steps[0]}",
        f"adb shell input motionevent MOVE {x_steps[1]} {y_steps[1]}",
        f"adb shell input motionevent MOVE {x_steps[2]} {y_steps[2]}",
        f"adb shell input motionevent MOVE {x_steps[3]} {y_steps[3]}",
        f"adb shell input motionevent MOVE {x_steps[4]} {y_steps[4]}",
        f"adb shell input motionevent MOVE {x_steps[0]} {y_steps[0]}",
        f"adb shell input motionevent UP {x_steps[0]} {y_steps[0]}"
    ]

    image_prefix = f"{'i_' if not perfect else ''}{'v_' if vertical else ''}{'r_' if orientation != Orientation.DESCENDING else ''}"
    os.system(f"adb exec-out screencap -p > {image_prefix}screenshot_0.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > {image_prefix}screenshot_{index+1}.png")
    os.system(actions[-1])

def make_alpha_mask_from_bw(_img: Image.Image, name: str = "ignoreZone") -> Image.Image:
    img = _img.convert('RGBA')
    arr = np.array(img)
    # mask True per pixel completamente bianchi (R=G=B=A=255)
    white_mask = np.all(arr == 255, axis=2)
    arr[~white_mask, 3] = 0
    result = Image.fromarray(arr)
    result.save(f'{name}_alpha.png')
    return result