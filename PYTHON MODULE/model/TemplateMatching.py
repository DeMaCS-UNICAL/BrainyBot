import os

import cv2
import mahotas
import numpy as np
from matplotlib import pyplot as plt

from CandyGraph import CandyGraph, PX, PY, T, ID
from model.DLVClass import resource_path, Node, DLVSolution, Edge

img_path = os.path.join(resource_path, 'img')  # The resource folder path


def getImg(location):
    im = cv2.imread(location)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


YELLOW = 0
BLUE = 1
ORANGE = 2
PURPLE = 3
RED = 4
GREEN = 5

# newEdge(62,9,0). newEdge(70,50,1).
# newEdge(62,40,1). newEdge(62,48,1).
# newEdge(70,12,1). newEdge(70,72,0).

sprites = {
    YELLOW: getImg(os.path.join(img_path, "yellow.png")),
    BLUE: getImg(os.path.join(img_path, "blue.png")),
    GREEN: getImg(os.path.join(img_path, "green.png")),
    ORANGE: getImg(os.path.join(img_path, "orange.png")),
    PURPLE: getImg(os.path.join(img_path, "purple.png")),
    RED: getImg(os.path.join(img_path, "red.png")),
}

colors = {
    YELLOW: (255, 255, 0),
    BLUE: (0, 0, 255),
    GREEN: (0, 128, 0),
    ORANGE: (255, 165, 0),
    PURPLE: (128, 0, 128),
    RED: (255, 0, 0)
}


def draw(matrixCopy, nodes, c=None, f=10):
    if c is None:
        c = nodes[T]
    cv2.rectangle(matrixCopy, (nodes[PX], nodes[PY]), (nodes[PX] + width, nodes[PY] + height), colors[c], f)


# take image

candyMatrix = getImg(os.path.join(img_path, "candymatrix.png"))
candy = sprites[YELLOW]
height, width, channels = candy.shape

height, width, channels = candy.shape
graph = CandyGraph((width, height))
for color in colors:

    # make a copy
    tmp = candyMatrix.copy()

    # execute template match
    method = eval('cv2.TM_CCOEFF_NORMED')
    res = cv2.matchTemplate(tmp, sprites[color], method)

    # find local maxElem
    locMax = mahotas.regmax(res)

    # modify this to change the algorithm precision
    threshold = 0.90
    loc = np.where((res * locMax) >= threshold)

    # take candy sprite value
    height, width, channels = candy.shape
    graph.setDifference((width, height))

    # draw
    for pt in zip(*loc[::-1]):
        graph.addNode(pt[PX], pt[PY], color)

nodes = []
for node in graph.getNodes():
    nodes.append(Node(node[ID], node[T]))

inputGraph = DLVSolution(nodes)

edges = []

# TODO: scommentare per far stampare i nodi e gli archi
for n, nbrs in graph.getGraph():
    # print(colors[nodes[T]])
    # matrixCopy = candyMatrix.copy()
    # cv2.rectangle(matrixCopy, (n[PX], n[PY]), (n[PX] + width, n[PY] + height), colors[n[T]], -1)
    for nbr, eattr in nbrs.items():
        # print(f"{nodes} -> {nbr} = {graph.getPosition(nodes, nbr)}")
        edges.append(Edge(n[ID], nbr[ID], graph.getPosition(n, nbr)))
        # cv2.rectangle(matrixCopy, (nbr[PX], nbr[PY]), (nbr[PX] + width, nbr[PY] + height), colors[nbr[T]], 2)

    # plt.imshow(matrixCopy)
    # plt.title(n)
    # plt.show()
#
# edgeNotOptimum = [0, 5, 3, 2, 1]
# for elem in edgeNotOptimum:
#     tmp = candyMatrix.copy()
#     node3 = graph.getNode(elem)
#     draw(tmp, node3)
#     plt.imshow(tmp)
#     plt.title(f"DRAW NODE: {elem}")
#     plt.show()
#
#
#
ignore = []
#
while True:
    swap, edgeNotOptimum = inputGraph.recallASP(edges, ignore)
    if swap == None:
        break

    tmp = candyMatrix.copy()
    node1 = graph.getNode(swap.get_id1())
    node2 = graph.getNode(swap.get_id2())

    ignore.append((swap.get_id1(), swap.get_id2()))

    draw(tmp, node1)
    draw(tmp, node2)

    for elem in edgeNotOptimum:
        node3 = graph.getNode(elem.get_id1())
        node4 = graph.getNode(elem.get_id2())
        draw(tmp, node3)
        draw(tmp, node4)

    plt.imshow(tmp)
    plt.title(f"swap {node1} --> {node2}.")
    plt.show()
#
# swap = inputGraph.recallASP(edges, None)
# tmp = candyMatrix.copy()
# node1 = graph.getNode(swap.get_id1())
# node2 = graph.getNode(swap.get_id2())
#
# draw(tmp, node1)
# draw(tmp, node2)
# plt.imshow(tmp)
# plt.title(f"----------- OPTIMUM ---- swap {node1} --> {node2}.")
# plt.show()
