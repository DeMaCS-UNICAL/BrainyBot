import os
import cv2

from AI.src.puzzle_bubble.constants import SPRITE_PATH
from AI.src.puzzle_bubble.detect.constants import SPRITES
from AI.src.abstraction.helpers import getImg

# take sprites
for file in os.listdir(SPRITE_PATH):
    img = getImg(os.path.join(SPRITE_PATH, file),color_conversion=cv2.COLOR_BGR2RGB)
    bubble_type = os.path.basename(file)
    SPRITES[bubble_type] = img