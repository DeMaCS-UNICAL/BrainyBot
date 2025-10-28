import os
from nis import match
from threading import Thread

from PIL import ImageDraw, Image
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage

from AI.src.candy_crush.object_graph.constants import HORIZONTAL


# 0 = descending, 1 = ascending
def get_perfect_horizontal_dataset(orientation: int = 0):
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

    os.system(f"adb exec-out screencap -p > {'r_' if orientation != 0 else ''}screenshot_{0}.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > {'r_' if orientation != 0 else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_imperfect_horizontal_dataset(orientation: int = 0):
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

    os.system(f"adb exec-out screencap -p > i_{'r_' if orientation != 0 else ''}screenshot_0.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > i_{'r_' if orientation != 0 else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_perfect_vertical_dataset(orientation: int = 0):
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

    os.system(f"adb exec-out screencap -p > v_{'r_' if orientation != 0 else ''}screenshot_{0}.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > v_{'r_' if orientation != 0 else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def get_imperfect_vertical_dataset(orientation: int = 0):
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
    os.system(f"adb exec-out screencap -p > i_v_{'r_' if orientation != 0 else ''}screenshot_0.png")
    os.system(actions[0])
    for index, action in enumerate(actions[1:-1]):
        os.system(action)
        os.system(f"adb exec-out screencap -p > i_v_{'r_' if orientation != 0 else ''}screenshot_{index+1}.png")
    os.system(actions[-1])

def makeAlphaIgnoreZone(_img: Image, name: str = "ignoreZone") -> Image:
    img = _img.convert('RGBA')
    arr = np.array(img)
    # mask True per pixel completamente bianchi (R=G=B=A=255)
    white_mask = np.all(arr == 255, axis=2)
    arr[~white_mask, 3] = 0
    result = Image.fromarray(arr)
    result.save(f'{name}_alpha.png')
    return result

def find_best_offset(
        img0: Image,
        img1: Image,
        ignore_zone: Image,
        base: int,
        check_range: tuple[int, int], # min -> max
        check_step: int,
        direction: int = 0, # 0 = horizontal, 1 = vertical
):
    arr0 = np.array(img0, dtype=np.int32)
    arr1 = np.array(img1, dtype=np.int32)

    iz = np.array(ignore_zone)
    if iz.ndim == 3 and iz.shape[2] == 4:
        rgb = iz[:, :, :3]
        alpha = iz[:, :, 3]
    elif iz.ndim == 3 and iz.shape[2] == 3:
        rgb = iz
        alpha = None
    else:
        # Che gli hai passato per avere sta roba bro??? non ti do un errore solo perché non voglio
        rgb = None
        alpha = None

    if rgb is not None:
        white_mask = np.all(rgb == 255, axis=2)
    else:
        white_mask = (iz == 255)

    alpha_mask = (alpha == 255) if alpha is not None else np.zeros_like(white_mask, dtype=bool)
    mask_full = white_mask | alpha_mask

    h0, w0 = arr0.shape[:2]
    h1, w1 = arr1.shape[:2]

    if mask_full.shape != (h0, w0):
        mask_img = PILImage.fromarray((mask_full.astype('uint8') * 255))
        mask_img = mask_img.resize((w0, h0), resample=PILImage.NEAREST)
        mask_full = (np.array(mask_img) > 0)

    best_score = float("inf")
    best_shift = base

    for delta in range(check_range[0], check_range[1] + 1, check_step):
        shift = base + delta

        if direction == 0:
            # orizzontale
            left = max(0, shift)
            right = min(w0, shift + w1)
            if right <= left:
                continue

            x1_left = left - shift
            x1_right = x1_left + (right - left)

            crop0 = arr0[:, left:right, :]
            crop1 = arr1[:, x1_left:x1_right, :]
            crop_mask = mask_full[:, left:right]
        else:
            # verticale
            top = max(0, shift)
            bottom = min(h0, shift + h1)
            if bottom <= top:
                continue

            y1_top = top - shift
            y1_bottom = y1_top + (bottom - top)

            crop0 = arr0[top:bottom, :, :]
            crop1 = arr1[y1_top:y1_bottom, :, :]
            crop_mask = mask_full[top:bottom, :]

        n_valid = np.count_nonzero(crop_mask)
        if n_valid == 0:
            continue

        diff = np.abs(crop0 - crop1).astype(np.float64)
        per_pixel_diff = diff.mean(axis=2)  # shape (h, w)

        masked_values = per_pixel_diff[crop_mask]
        if masked_values.size == 0:
            continue

        score = masked_values.mean()

        print(f"Score at {delta}: {score!r}")
        if score < best_score:
            best_score = score
            best_shift = shift

    return best_shift, best_score

STEP = 100  # px
TOTAL = 400  # px
CHECK_RANGE = 30  # px
CHECK_FREQUENCY = 1  # px
DIRECTION = 0 # 0 = horizontal, 1 = vertical
PERFECT = True
CAPTURE = True
ORIENTATION = 1 # 0 = descending, 1 = ascending

if __name__ == "__main__":
    os.chdir("resources")

    match (PERFECT, DIRECTION, CAPTURE):
        case (True, 0, True):
            get_perfect_horizontal_dataset(ORIENTATION)
        case (True, 1, True):
            get_perfect_vertical_dataset(ORIENTATION)
        case (False, 0, True):
            get_imperfect_horizontal_dataset(ORIENTATION)
        case (False, 1, True):
            get_imperfect_vertical_dataset(ORIENTATION)

    images = [Image.open(f"{'i_' if (not PERFECT) else ''}{'v_' if DIRECTION == 1 else ''}{'r_' if ORIENTATION != 0 else ''}screenshot_{index}.png") for index in range(5)]
    ignoreZone = makeAlphaIgnoreZone(Image.open("ignoreZoneIsland.png"))

    prev_offset = 0

    desk = Image.new("RGBA",
                     (images[0].width+TOTAL+CHECK_RANGE, images[0].height) if DIRECTION == 0 else
                     (images[0].width, images[0].height+TOTAL+CHECK_RANGE),
                     (255, 0, 0, 255)
                     )
    desk.paste(
        images[0].convert("RGBA"),
        (0, 0) if ORIENTATION == 0 else (
            (desk.width-images[0].width, 0) if DIRECTION == 0 else (0, desk.height-images[0].height)
        ),
        mask=ignoreZone
    )

    for i in range(4):
        img0 = images[i].convert("RGB")
        img1 = images[i+1].convert("RGB")
        w0, h0 = img0.size
        w1, h1 = img1.size

        best_shift, best_score = find_best_offset(
            img0,
            img1,
            ignoreZone,
            STEP,
            (-CHECK_RANGE, CHECK_RANGE),
            CHECK_FREQUENCY,
            DIRECTION
        )
        delta = best_shift - STEP

        print(f"Best shift: {best_shift} px (delta vs STEP: {delta} px), score: {best_score:.4f}")

        prev_offset+=best_shift
        desk.paste(img1.convert("RGBA"),
                (prev_offset, 0) if DIRECTION == 0 else
                (0, prev_offset),
                mask=ignoreZone
            )

    w, h = desk.size
    dpi = 100
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(np.asarray(desk))
    plt.show()