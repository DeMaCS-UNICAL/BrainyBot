from PIL import Image
from matplotlib import pyplot as plt

from AI.src.stuffMerger.motion_module import MotionModule

games = [
    ["resources/islandempire_mask.png", "resources/islandempire_mask_alpha.png"],
    ["resources/minesweeper_mask.png", "resources/minesweeper_mask_alpha.png"]
]

GAME = 0

if __name__ == "__main__":
    md = MotionModule(
        image_mask = Image.open(games[GAME][1]),
        screen_size = (1080, 2400),
        motion_area=(300, 300, 2100, 2100)
    )
    desk = Image.new("RGBA", (3000, 3000), (255, 0, 0))
    print(
        md.move(
            step_number = (12, 0),
            destination_offset= (1200, 0),
            desk = desk
        )
    )
    plt.imshow(desk)
    plt.show()

