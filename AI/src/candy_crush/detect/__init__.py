import os

from src.detect.constants import SPRITE_PATH, SPRITES
from src.detect.helpers import getImg

# take sprites
for file in os.listdir(SPRITE_PATH):
    img = getImg(os.path.join(SPRITE_PATH, file))
    typeCandy = os.path.basename(file)
    SPRITES[typeCandy] = img
    #print(typeCandy)
