import os
import cv2
import sys

from AI.src.candy_crush.constants import SPRITE_PATH
from AI.src.candy_crush.detect.constants import SPRITES,DISTANCE
from AI.src.abstraction.helpers import getImg

# take sprites

for file in os.listdir(SPRITE_PATH):
    if os.path.isfile(os.path.join(SPRITE_PATH, file)): 
        img = getImg(os.path.join(SPRITE_PATH, file),color_conversion=cv2.COLOR_BGR2RGB)
        typeCandy = os.path.basename(file)
        SPRITES[typeCandy] = img
        height, width, _ = img.shape
        if width < DISTANCE[0]:
            DISTANCE[0]=width
        if height < DISTANCE[1]:
            DISTANCE[1]=height