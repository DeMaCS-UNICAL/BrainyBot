from AI.src.stuffMerger.motion_module import MotionModule
from matplotlib import pyplot as plt
from PIL import Image

from AI.src.stuffMerger.utils.resources_utility import get_image

GAME = "island_empire"
PHONE = "p10lite"

games = {
    "island_empire": [
        f"resources/{PHONE}/islandempire_mask.png",
        f"resources/{PHONE}/islandempire_mask_alpha.png",
    ],
    "minesweeper": [
        f"resources/{PHONE}/minesweeper_mask.png",
        f"resources/{PHONE}/minesweeper_mask_alpha.png",
    ],
}

screensizes = {
    "p10lite": (1080, 1920),
    "pocof7ultra": (1080, 2400),
}

# Should be adjusted phone-game not only phone
# Not every game allows for the same range of motion
motionareas = {
    "p10lite": ((300, 300), (1700, 1700)),
    "pocof7ultra": ((300, 300), (2100, 2100)),
}

if __name__ == "__main__":
    import os
    print(os.getcwd())
    print(os.listdir())
    md = MotionModule(
        image_mask=Image.open(games[GAME][1]),
        screen_size=screensizes[PHONE],
        motion_area=motionareas[PHONE],
    )
    desk = Image.new("RGBA", (3000, 3000), (255, 0, 0))
    image = get_image()
    # desk.paste(image.convert("RGBA"), (0, 0), mask=md.image_mask)
    print(md.move(step_number=(2, 0), destination_offset=(600, 0), desk=desk))
    # print(md.move(step_number=(12, 0), destination_offset=(1200, 0), desk=desk))
    plt.imshow(desk)
    plt.show()
