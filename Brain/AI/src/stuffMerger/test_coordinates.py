import os
from PIL import ImageDraw, Image
import matplotlib.pyplot as plt

if __name__ == "__main__":
    os.chdir("resources")
    os.system("adb exec-out screencap -p > screenshot.png")

    with Image.open("screenshot.png") as im:
        size = (im.size[0], im.size[1])

        ox, dx = int(size[0] / 2 * 1), int(size[0] / 2 * 1)
        oy, dy = int(size[1] / 2 * 1.5), int(size[1] / 2 * 0.5)

        # Display swipe from point 1 to point b (origin to destination)

        draw = ImageDraw.Draw(im)
        draw.line((ox, oy, dx, dy), fill="red", width=4)
        draw.circle((ox, oy), radius=14, fill="green", width=4)
        draw.circle((ox, oy), radius=10, fill="blue", width=4)
        draw.circle((dx, dy), radius=24, fill="green", width=4)
        draw.circle((dx, dy), radius=20, fill="blue", width=4)
        plt.imshow(im)
        plt.show()




