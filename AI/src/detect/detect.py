import os

import cv2
import mahotas
import numpy as np

from src.candygraph.candygraph import CandyGraph, PX, PY
from src.constants import RESOURCES_PATH
from src.detect import SPRITES, getImg


class MatchingCandy:
    def __init__(self, difference: ()):
        self.__matrix = getImg(os.path.join(RESOURCES_PATH, 'matrix.png'))
        self.__methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__method = eval(self.__methodName)
        self.__graph = CandyGraph(difference)

    def __searchByName(self, typeCandy) -> None:
        # execute template match
        res = cv2.matchTemplate(self.__matrix, SPRITES[typeCandy], self.__method)

        # find regional maxElem
        regMax = mahotas.regmax(res)

        # modify this to change the algorithm precision
        threshold = 0.85
        loc = np.where((res * regMax) >= threshold)

        # take candy sprites value
        height, width, _ = SPRITES[typeCandy].shape
        self.__graph.setDifference((width, height))

        # add node2 and edge
        for pt in zip(*loc[::-1]):
            self.__graph.addNode(pt[PX], pt[PY], typeCandy)

    def search(self) -> CandyGraph:
        for typeCandy in SPRITES.keys():
            self.__searchByName(typeCandy)

        return self.__graph

    def getMatrix(self):
        return self.__matrix
