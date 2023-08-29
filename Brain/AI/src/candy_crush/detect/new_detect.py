import os
import cv2

from AI.src.abstraction.object_graph import ObjectGraph, PX, PY
from AI.src.abstraction.abstraction import Abstraction
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder


class MatchingCandy:
    def __init__(self, screenshot,difference:(), debug=False):
        #
        # Use Matrix2.png for testing
        #
        self.finder = ObjectsFinder(screenshot,cv2.COLOR_BGR2RGB)
        
        self.__matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=cv2.COLOR_BGR2RGB)
        self.__difference = difference
        self.__graph=None

    def search(self) -> ObjectGraph:
        candies_found = self.finder.find_all(SPRITES)
        gridifier = Abstraction()
        self.__graph = gridifier.ToGraph(candies_found,self.__difference)
        return self.__graph

    def get_matrix(self):
        return self.__matrix
