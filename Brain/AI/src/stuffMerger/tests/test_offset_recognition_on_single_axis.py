from logging import DEBUG, INFO, Formatter
from threading import Thread
import matplotlib.pyplot as plt
import logging
import subprocess

from AI.src.stuffMerger.enums import *
from AI.src.stuffMerger.utils.resources_utility import *
from AI.src.stuffMerger.utils.image_processing_utility import *

from AI.src.constants import logger

logger.setLevel(logging.INFO)

TOTAL = 400  # px
STAGES = 4
STEP = TOTAL//STAGES  # px
CHECK_RANGE = 30  # px
CHECK_FREQUENCY = 1  # px
DIRECTION = Direction.HORIZONTAL # 0 = horizontal, 1 = vertical
ORIENTATION = Orientation.DESCENDING # 0 = descending, 1 = ascending
PERFECT = False
CAPTURE = False

class Runner(Thread):
    def __init__(self, img0, crop1, shift):
        super().__init__()
        self.img0 = img0
        self.crop1 = crop1
        self.shift = shift
        self.score = None
        self.n_valid = None

    def run(self):
        self.score, self.n_valid = np_absolute_distance_image_comparison(self.img0, self.crop1)
        logger.log(DEBUG, f"Score at shift {self.shift}: {self.score!r}")


def find_best_offset(
    _img0: Image.Image,
    _img1: Image.Image,
    _mask: Image.Image,
    base_shift: int,
    check_range: tuple[int, int], # min -> max
    check_step: int,
    direction: Direction = Direction.HORIZONTAL, # 0 = horizontal, 1 = vertical
    orientation: Orientation = Orientation.DESCENDING
):
    """
    _img0: image to match
    _img1: image to check
    _mask: mask for both images (only check alpha values, can be generated from a black and white image with make_alpha_mask_from_bw)
    base_shift: how much the check image is shifted from the first image (can be negative)
    check_range: range of offset to check (a, b) a->b (a can be negative)
    check_step: how many pixels between each check (1 = every pixel)
    direction: change the direction of the shift (0 = horizontal, 1 = vertical)
    orientation: change the orientation of the shift (basically if the delta is positive or negative)
    """
    mask = np.array(_mask, dtype=np.int32)
    img0 = apply_mask_make_transparent(np.array(_img0, dtype=np.int32), mask)
    img1 = apply_mask_make_transparent(np.array(_img1, dtype=np.int32), mask)

    best_score = float("inf")
    best_shift = base_shift

    threads = []

    for delta in range(check_range[0], check_range[1] + 1, check_step):
        shift = base_shift + (delta if orientation == Orientation.DESCENDING else -delta)

        if direction == Direction.HORIZONTAL:
            crop1 = np.roll(img1, shift, axis=1)
            if orientation == Orientation.DESCENDING:
                crop1[:, :shift] = 0
            else:
                crop1[:, -shift:] = 0
        else:
            crop1 = np.roll(img1, shift, axis=0)
            if orientation == Orientation.DESCENDING:
                crop1[:shift, :] = 0
            else:
                crop1[-shift:, :] = 0

        t = SimilarityThread(img0, crop1, shift)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    for t in threads:
        if t.score < best_score:
            best_score = t.score
            best_shift = t.shift
            if best_shift in check_range:
                logger.log(logging.WARNING, f"The shift is at the border of the check_range, probably the search was a failure")

    logger.log(
        DEBUG,
        f"result: {best_shift} {best_score}"
    )

    return best_shift, best_score


if __name__ == "__main__":
    os.chdir("resources/cache")
    if CAPTURE:
        get_image_set(
            perfect = PERFECT,
            vertical = DIRECTION == Direction.VERTICAL,
            horizontal = DIRECTION == Direction.HORIZONTAL,
            orientation = ORIENTATION,
            save_location = "single_axis/"
        )

    images = [Image.open(f"single_axis/{'i_' if (not PERFECT) else ''}{'v_' if DIRECTION == Direction.VERTICAL else ''}{'r_' if ORIENTATION == Orientation.ASCENDING else ''}screenshot_{index}.png") for index in range(5)]
    ignoreZone = make_alpha_mask_from_bw(Image.open("isandempire_mask.png"))

    desk = Image.new("RGBA",
            (images[0].width+TOTAL+CHECK_RANGE, images[0].height) if DIRECTION == Direction.HORIZONTAL else
            (images[0].width, images[0].height+TOTAL+CHECK_RANGE),
            (255, 0, 0, 255)
        )

    prev_offset = desk.width-images[0].width if DIRECTION == Direction.HORIZONTAL else desk.height-images[0].height
    if ORIENTATION == Orientation.DESCENDING:
        prev_offset = 0

    desk.paste(
        images[0].convert("RGBA"),
        (0, 0) if ORIENTATION == Orientation.DESCENDING else (
            (desk.width-images[0].width, 0) if DIRECTION == Direction.HORIZONTAL else
            (0, desk.height-images[0].height)
        ),
        mask=ignoreZone
    )

    offsets = []

    for i in range(STAGES):
        best_shift, best_score = find_best_offset(
            _img0= images[i],
            _img1= images[i+1],
            _mask= ignoreZone,
            base_shift = STEP if ORIENTATION == Orientation.DESCENDING else -STEP,
            check_range = (-CHECK_RANGE, CHECK_RANGE),
            check_step = CHECK_FREQUENCY,
            direction = DIRECTION,
            orientation = ORIENTATION
        )
        delta = best_shift + (-STEP if ORIENTATION == Orientation.DESCENDING else STEP)
        logger.log(INFO, f"Best shift: {best_shift} px (delta vs STEP: {delta} px), score: {best_score:.4f}")
        offsets.append(best_shift)


    for i in range(STAGES):
        prev_offset+=offsets[i]
        desk.paste(images[i+1],
                (prev_offset, 0) if DIRECTION == Direction.HORIZONTAL else
                (0, prev_offset),
                mask=ignoreZone
            )

    logger.log(INFO, f"Total Distance x:{sum(offsets) if DIRECTION == Direction.HORIZONTAL else 0} y:{0 if DIRECTION == Direction.HORIZONTAL else sum(offsets)}")

    w, h = desk.size
    dpi = 100
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(np.asarray(desk))
    plt.show()