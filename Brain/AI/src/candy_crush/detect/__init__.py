import os
import cv2
import sys

from AI.src.candy_crush.constants import SPRITE_PATH
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.abstraction.helpers import getImg

# take sprites
for file in os.listdir(SPRITE_PATH):
    img = getImg(os.path.join(SPRITE_PATH, file),color_conversion=cv2.COLOR_BGR2RGB)
    typeCandy = os.path.basename(file)
    SPRITES[typeCandy] = img