import os
import re

import cv2
import mahotas
import numpy as np

from setup import RESOURCES_PATH
from src.model.CandyGraph import CandyGraph, PX, PY, ID, TYPE
from src.model.DLVClass import Edge, InputBomb, InputNode, InputHorizontalOrVertical

SPRITE_PATH = os.path.join(RESOURCES_PATH, 'sprites')  # The resource folder path
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
    def __init__(self, matrix, difference: ()):
        self.__matrix = matrix
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


def getInputDLVNodes(graph: CandyGraph) -> []:
    nodesAndInformation = []
    for node in graph.getNodes():

        result = re.search(r"^(\w+)\.(?:png|jpeg|jpg)$", node[TYPE])
        candyType = result.groups()[0]

        # checks if the node2 is not swappable
        if "notTouch" in candyType:
            continue

        if "Bomb" in candyType:
            result = re.search(r"^(\w+)(?:Bomb)$", candyType)
            candyType = result.groups()[0]
            nodesAndInformation.append(InputBomb(node[ID]))

        if "Horizontal" in candyType or "Vertical" in candyType:
            result = re.search(r"^(\w+)(?:Horizontal|Vertical)$", candyType)
            candyType = result.groups()[0]
            nodesAndInformation.append(InputHorizontalOrVertical(node[ID]))

        nodesAndInformation.append(InputNode(node[ID], candyType))

    return nodesAndInformation


def getEdges(graph: CandyGraph) -> [Edge]:
    edges = []
    for n, nbrs in graph.getGraph():
        for nbr, eattr in nbrs.items():
            edges.append(Edge(n[ID], nbr[ID], graph.getPosition(n, nbr)))

    return edges
