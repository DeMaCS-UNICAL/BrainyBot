import os

from src.candy_crush.constants import SPRITE_PATH
from src.candy_crush.detect.constants import SPRITES
from src.candy_crush.detect.helpers import get_img

# take sprites
for file in os.listdir(SPRITE_PATH):
    img = get_img(os.path.join(SPRITE_PATH, file))
    typeCandy = os.path.basename(file)
    SPRITES[typeCandy] = img
    # print(typeCandy)
