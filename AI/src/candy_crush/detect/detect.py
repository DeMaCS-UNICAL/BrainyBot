import os

import mahotas
import numpy as np
import cv2

from src.candy_crush.candygraph.candygraph import CandyGraph, PX, PY
from src.candy_crush.detect.constants import SPRITES
from src.candy_crush.detect.helpers import get_img
from src.constants import SCREENSHOT_PATH


class MatchingCandy:
    def __init__(self, difference: ()):
        self.__matrix = get_img(os.path.join(SCREENSHOT_PATH, 'Matrix2.png')) # TODO: modify name
        self.__methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__method = eval(self.__methodName)
        self.__graph = CandyGraph(difference)

    def __search_by_name(self, typeCandy) -> None:

        # print("Matching %s" % typeCandy)

        # execute template match
        res = cv2.matchTemplate(self.__matrix, SPRITES[typeCandy], self.__method)

        #        print ("Found %d matches." % len(res))

        # find regional maxElem
        regMax = mahotas.regmax(res)

        # modify this to change the algorithm precision
        threshold = 0.85
        loc = np.where((res * regMax) >= threshold)

        # take candy sprites value
        height, width, _ = SPRITES[typeCandy].shape
        self.__graph.set_difference((width, height))

        # add node2 and edge
        count = 0
        for pt in zip(*loc[::-1]):
            self.__graph.add_another_node(pt[PX], pt[PY], typeCandy)
            count += 1
        print ("Found %d matches for %s" % (count,typeCandy))

    def search(self) -> CandyGraph:
        for typeCandy in SPRITES.keys():
            self.__search_by_name(typeCandy)

        return self.__graph

    def get_matrix(self):
        return self.__matrix
