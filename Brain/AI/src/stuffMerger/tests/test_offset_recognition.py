import os
from PIL import ImageDraw, Image
import matplotlib.pyplot as plt
from enum import Enum
import numpy as np
import subprocess
def getPerfectDataset():
    actions = [
        "adb shell input motionevent DOWN 600 1700",
        "adb shell input motionevent MOVE 500 1700",
        "adb shell input motionevent MOVE 400 1700",
        "adb shell input motionevent MOVE 300 1700",
        "adb shell input motionevent MOVE 200 1700",
        "adb shell input motionevent MOVE 600 1700",
        "adb shell input motionevent UP 200 1700"
    ]

    subprocess.run(f"adb exec-out screencap -p > screenshot_{0}.png")
    subprocess.run(actions[0])
    for index, action in enumerate(actions[1:-1]):
        subprocess.run(action)
        subprocess.run(f"adb exec-out screencap -p > screenshot_{index+1}.png")
    subprocess.run(actions[-1])

def getInperfectDataset():
    actions = [
        "adb shell input motionevent DOWN 600 1700",
        "adb shell input motionevent MOVE 497 1700", #103
        "adb shell input motionevent MOVE 391 1700", #109-3 = 106
        "adb shell input motionevent MOVE 294 1700", #106-6 = 100
        "adb shell input motionevent MOVE 189 1700", #111-0 = 111
        "adb shell input motionevent MOVE 600 1700",
        "adb shell input motionevent UP 200 1700"
    ]

    subprocess.run(f"adb exec-out screencap -p > i_screenshot_0.png")
    subprocess.run(actions[0])
    for index, action in enumerate(actions[1:-1]):
        subprocess.run(action)
        subprocess.run(f"adb exec-out screencap -p > i_screenshot_{index+1}.png")
    subprocess.run(actions[-1])

def makeAlphaIgnoreZone(_img: Image) -> Image:
    img = _img.convert('RGBA')
    arr = np.array(img)
    # mask True per pixel completamente bianchi (R=G=B=A=255)
    white_mask = np.all(arr == 255, axis=2)
    arr[~white_mask, 3] = 0
    result = Image.fromarray(arr)
    result.save('islandempire_mask_alpha.png')
    return result

def find_best_offset(
        img0: Image,
        img1: Image,
        ignore_zone: Image,
        base: int,
        check_range: tuple[int, int], # min -> max
        step: int
):
    import numpy as np
    from PIL import Image as PILImage

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
        mask_img = mask_img.resize((w0, h0), resample=PILImage.Resampling.NEAREST)
        mask_full = (np.array(mask_img) > 0)

    best_score = float("inf")
    best_shift = base

    for delta in range(check_range[0], check_range[1] + 1, step):
        shift = base + delta
        left = max(0, shift)
        right = min(w0, shift + w1)
        if right <= left:
            continue

        x1_left = left - shift
        x1_right = x1_left + (right - left)

        crop0 = arr0[:, left:right, :]
        crop1 = arr1[:, x1_left:x1_right, :]

        crop_mask = mask_full[:, left:right]
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
CHECK_RANGE = 10  # px
CHECK_FREQUENCY = 1  # px

if __name__ == "__main__":
    os.chdir("../resources")
    # getPerfectDataset()
    # getInperfectDataset()
    images = [Image.open(f"screenshot_{index}.png") for index in range(5)]
    ignoreZone = makeAlphaIgnoreZone(Image.open("minesweeper_mask.png"))

    prev_offset = 0

    desk = Image.new("RGBA", (images[0].width+TOTAL+CHECK_RANGE, images[0].height), (255, 0, 0, 255))
    desk.paste(images[0].convert("RGBA"), (0, 0))

    for i in range(4):
        img0 = images[i].convert("RGB")
        img1 = images[i+1].convert("RGB")
        w0, h0 = img0.size
        w1, h1 = img1.size

        best_shift, best_score = find_best_offset(img0, img1, ignoreZone, STEP, (0, CHECK_RANGE), CHECK_FREQUENCY)
        delta = best_shift - STEP

        print(f"Best shift: {best_shift} px (delta vs STEP: {delta} px), score: {best_score:.4f}")

        prev_offset+=best_shift
        desk.paste(img1.convert("RGBA"), (prev_offset, 0))

    plt.imshow(desk)
    plt.axis("off")
    plt.show()
