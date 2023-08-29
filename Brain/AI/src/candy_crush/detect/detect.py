import os

import mahotas
import numpy as np
import cv2

from AI.src.abstraction.object_graph import ObjectGraph, PX, PY
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.candy_crush.detect.helpers import get_img
from AI.src.constants import SCREENSHOT_PATH
from AI.common_facilities.template_matching import TemplateMatching

class MatchingCandy:
    def __init__(self, difference:(), debug=False):
        #
        # Use Matrix2.png for testing
        #
        if debug:
            screenshot = 'testScreenshotCCS.png'
        else:
            screenshot = 'screenshot.png'
        #####self.__match_template_method_name = 'cv.TM_CCOEFF_NORMED'
        #####self.__match_template_method = eval(self.__match_template_method_name)
        self.__matrix = get_img(os.path.join(SCREENSHOT_PATH, screenshot)) 
        self.templateMatcher = TemplateMatching(self.__matrix, 0.8, False, True)
        self.__graph = ObjectGraph(difference)

    def __search_by_name(self, typeCandy) -> None:

        # print("Matching %s" % typeCandy)

        # execute template match
        ######res = cv2.matchTemplate(self.__matrix, SPRITES[typeCandy], self.__method)

        #        print ("Found %d matches." % len(res))

        # find regional maxElem
        ######regMax = mahotas.regmax(res)

        # modify this to change the algorithm precision
        ######threshold = 0.8
        ######loc = np.where((res * regMax) >= threshold)
        loc = self.templateMatcher.match(SPRITES[typeCandy])

        # take candy sprites value
        height, width, _ = SPRITES[typeCandy].shape
        self.__graph.set_difference((width, height))

        # add node2 and edge
        count = 0
        for pt in zip(*loc[::-1]):
            self.__graph.add_another_node(pt[PX], pt[PY], typeCandy)
            count += 1
        print ("Found %d matches for %s" % (count,typeCandy))

    def search(self) -> ObjectGraph:
        for typeCandy in SPRITES.keys():
            self.__search_by_name(typeCandy)

        return self.__graph

    def get_matrix(self):
        return self.__matrix
