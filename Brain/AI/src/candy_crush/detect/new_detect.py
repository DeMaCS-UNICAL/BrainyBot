import os
import cv2

from AI.src.candy_crush.candygraph.candygraph import CandyGraph, PX, PY
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.ball_sort.detect.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder


class MatchingCandy:
    def __init__(self, difference:(), debug=False):
        #
        # Use Matrix2.png for testing
        #
        print("In new detect")
        if debug:
            screenshot = 'testScreenshotCCS.png'
            self.finder = ObjectsFinder(cv2.COLOR_BGR2RGB,debug,'testScreenshotCCS.png')
        else:
            screenshot = 'screenshot.png'
            self.finder = ObjectsFinder(cv2.COLOR_BGR2RGB)
        
        self.__matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=cv2.COLOR_BGR2RGB)
        self.__graph = CandyGraph(difference)

    def search(self) -> CandyGraph:
        candies_found = self.finder.find_all(SPRITES)
        for typeCandy in candies_found.keys():
            height, width, _ = SPRITES[typeCandy].shape
            self.__graph.set_difference((width, height))
            for match in candies_found[typeCandy]:
                self.__graph.add_another_node(match[PX], match[PY], typeCandy)

        return self.__graph

    def get_matrix(self):
        return self.__matrix
