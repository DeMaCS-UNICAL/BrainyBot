import matplotlib.pyplot as plt
from AI.src.constants import logger
from AI.src.motion_module.enums import *
from AI.src.motion_module.utils.image_processing_utility import *
from AI.src.motion_module.utils.resources_utility import *

logger.propagate = False

TOTAL = 400  # px
STAGES = 4  # The number of moves we want to make
STEP = TOTAL // STAGES  # px
CHECK_RANGE = 30  # px
CHECK_FREQUENCY = 1  # px
VERTICAL = False
HORIZONTAL = True
ORIENTATION = Orientation.DESCENDING  # 0 = descending, 1 = ascending (0->100, 100->0)
PERFECT = True
CAPTURE = False


if __name__ == "__main__":
    os.chdir("../resources/test_material")
    if "multiple_axis" not in os.listdir():
        os.mkdir("multiple_axis/")

    if CAPTURE:
        get_image_set(
            perfect=PERFECT,
            vertical=VERTICAL,
            horizontal=HORIZONTAL,
            orientation=ORIENTATION,
            save_location="multiple_axis/",
            step_size=200,
            start_x=900,
            start_y=1000,
        )

    image_prefix = f"{'i_' if not PERFECT else ''}{'v_' if VERTICAL else ''}{'h_' if HORIZONTAL else ''}{'r_' if ORIENTATION != Orientation.DESCENDING else ''}"

    images = [
        Image.open(f"multiple_axis/{image_prefix}screenshot_{index}.png")
        for index in range(5)
    ]
    mask = make_alpha_mask_from_bw(Image.open("../p10lite/islandempire_mask_alpha.png"))

    # TOTAL*2 and TOTAL inside the desk gives us additional margin to paste the images without worrying about going out of bounds, while CHECK_RANGE gives us the necessary space to check for offsets in both directions.

    desk = Image.new(
        "RGBA",
        (
            images[0].width + TOTAL * 2 + CHECK_RANGE,
            images[0].height + TOTAL * 2 + CHECK_RANGE,
        ),
        (255, 0, 0, 255),
    )

    desk.paste(
        images[0].convert("RGBA"),
        (0, 0)
        if ORIENTATION == Orientation.DESCENDING
        else (
            desk.width - images[0].width - TOTAL,
            desk.height - images[0].height - TOTAL,
        ),
        mask,
    )

    offsets = {"x": 0, "y": 0}
    deltas = []

    for i in range(len(images) - 1):
        img_a = to_uint8(images[i])
        img_b = to_uint8(images[i + 1])
        #
        # img_b = np.roll(img_b, offsets["x"], axis=1)
        # img_b = np.roll(img_b, offsets["y"], axis=0)
        # img_b[:, :offsets["x"]] = 0
        # img_b[:offsets["y"], :] = 0

        # dx, dy, confidence = find_offset_orb(img_a, img_b, mask)
        # img_a = apply_mask_make_transparent(img_a, mask)
        # img_b = apply_mask_make_transparent(img_b, mask)
        mask = invert_mask_alpha_channel(mask)

        img, (dx, dy, confidence) = visualize_orb_matches(img_a, img_b, mask)

        plt.figure()
        plt.imshow(img)
        plt.title(f"Pair {i}-{i + 1}: dx={dx}, dy={dy}, conf={confidence}")
        plt.show()

        offsets["x"] -= round(dx)
        offsets["y"] -= round(dy)

        logger.info(f"Pair {i}-{i + 1}: dx={dx}, dy={dy}, conf={confidence}")
    logger.info(f"Total offset: x={offsets['x']} y={offsets['y']}")
