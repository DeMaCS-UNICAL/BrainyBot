import matplotlib.pyplot as plt
from AI.src.stuffMerger.enums import *
from AI.src.stuffMerger.utils.resources_utility import *
from AI.src.stuffMerger.utils.image_processing_utility import *


"""
_img0: image to match
_img1: image to check
_mask: mask for both images (only check alpha values, can be generated from a black and white image with make_alpha_mask_from_bw)
base_shift: how much the check image is shifted from the first image (can be negative)
check_range: range of offset to check (a, b) a->b (a can be negative)
check_step: how many pixels between each check (1 = every pixel)
direction: change the direction of the shift (0 = horizontal, 1 = vertical)
"""
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
    mask = np.array(_mask, dtype=np.int32)
    img0 = apply_mask_make_transparent(np.array(_img0, dtype=np.int32), mask)
    img1 = apply_mask_make_transparent(np.array(_img1, dtype=np.int32), mask)

    best_score = float("inf")
    best_shift = base_shift

    for delta in range(check_range[0], check_range[1] + 1, check_step):
        shift = base_shift + (delta if orientation == Orientation.DESCENDING else -delta)

        if orientation == Orientation.DESCENDING:
            if direction == Direction.HORIZONTAL:
                crop1 = np.roll(img1, shift, axis=1)
                crop1[:, :shift] = 0
            else:
                crop1 = np.roll(img1, shift, axis=0)
                crop1[:shift, :] = 0
        else:
            if direction == Direction.HORIZONTAL:
                crop1 = np.roll(img1, shift, axis=1)
                crop1[:, shift:] = 0
            else:
                crop1 = np.roll(img1, shift, axis=0)
                crop1[shift:, :] = 0

        # if direction == Direction.HORIZONTAL:
        #     crop1 = np.roll(img1, shift, axis=1)
        #     if orientation == Orientation.DESCENDING:
        #         crop1[:, :shift] = 0
        #     else:
        #         crop1[:, -shift:] = 0
        # else:
        #     crop1 = np.roll(img1, shift, axis=0)
        #     if orientation == Orientation.DESCENDING:
        #         crop1[:shift, :] = 0
        #     else:
        #         crop1[-shift:, :] = 0

        score, n_valid = compare_images_alpha_overlap(img0, crop1)

        if n_valid == 0:
            continue

        print(f"Score at {delta}: {score!r}")
        if score < best_score:
            best_score = score
            best_shift = shift

    return best_shift, best_score

STEP = 100  # px
TOTAL = 400  # px
CHECK_RANGE = 30  # px
CHECK_FREQUENCY = 1  # px
DIRECTION = Direction.HORIZONTAL # 0 = horizontal, 1 = vertical
PERFECT = True
CAPTURE = False
ORIENTATION = Orientation.ASCENDING # 0 = descending, 1 = ascending

if __name__ == "__main__":
    os.chdir("resources")
    if CAPTURE:
        get_image_set(
            perfect = PERFECT,
            vertical = DIRECTION == Direction.VERTICAL,
            orientation = ORIENTATION,
        )

    images = [Image.open(f"{'i_' if (not PERFECT) else ''}{'v_' if DIRECTION == Direction.VERTICAL else ''}{'r_' if ORIENTATION == Orientation.ASCENDING else ''}screenshot_{index}.png") for index in range(5)]
    ignoreZone = make_alpha_mask_from_bw(Image.open("ignoreZoneIsland.png"))


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

    for i in range(4):
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

        print(f"Best shift: {best_shift} px (delta vs STEP: {delta} px), score: {best_score:.4f}")

        offsets.append(best_shift)


    for i in range(4):
        prev_offset+=offsets[i]
        desk.paste(images[i+1],
                (prev_offset, 0) if DIRECTION == Direction.HORIZONTAL else
                (0, prev_offset),
                mask=ignoreZone
            )

    w, h = desk.size
    dpi = 100
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(np.asarray(desk))
    plt.show()