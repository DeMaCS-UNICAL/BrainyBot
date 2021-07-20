import os

import cv2
import mahotas
import numpy as np

from model.CandyGraph import CandyGraph, PX, PY, ID, TYPE
from model.DLVClass import resource_path, Node

SPRITE_PATH = os.path.join(resource_path, 'sprite')  # The resource folder path
SPRITES = {}


def getImg(file):
    try:
        im = cv2.imread(file)
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    except:
        raise Exception(f"NO {file} FOUND. \n")


for file in os.listdir(SPRITE_PATH):
    img = getImg(os.path.join(SPRITE_PATH, file))
    typeCandy = os.path.basename(file)
    SPRITES[typeCandy] = img


class MatchingCandy:
    def __init__(self, fileLocation):
        self.__matrix = getImg(fileLocation)
        self.__methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__method = eval(self.__methodName)
        self.__graph = CandyGraph()
        self.__nodes = []

    def __serachByName(self, typeCandy) -> None:
        # execute template match
        res = cv2.matchTemplate(self.__matrix, SPRITES[typeCandy], self.__method)

        # find local maxElem
        locMax = mahotas.regmax(res)

        # modify this to change the algorithm precision
        threshold = 0.90
        loc = np.where((res * locMax) >= threshold)

        # take candy sprite value
        height, width, _ = SPRITES[typeCandy].shape
        self.__graph.setDifference((width, height))

        # add node and edge
        for pt in zip(*loc[::-1]):
            self.__graph.addNode(pt[PX], pt[PY], typeCandy)

    def search(self) -> CandyGraph:
        for typeCandy in SPRITES.keys():
            self.__serachByName(typeCandy)

        return self.__graph

    def getNodes(self) -> [Node]:
        for node in self.__graph.getNodes():
            self.__nodes.append(Node(node[ID], node[TYPE]))

        return self.__nodes