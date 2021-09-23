import cv2
from matplotlib import pyplot as plt

from src.candygraph.candygraph import CandyGraph
from src.candygraph.constants import PX, PY, TYPE
from src.detect.detect import MatchingCandy
from src.dlvsolution.dlvsolution import DLVSolution
from src.dlvsolution.helpers import getInputDLVNodes, getEdges, Swap
from src.webservices.helpers import makeJson, requireImageFromURL

def draw(matrixCopy, nodes, color):
    width, height = 110, 110
    cv2.rectangle(matrixCopy, (nodes[PX], nodes[PY]), (nodes[PX] + width, nodes[PY] + height),
                  color,
                  10)


RED = "red"
BLUE = "blue"
YELLOW = "yellow"
GREEN = "green"
PURPLE = "purple"
ORANGE = "orange"
WHITE = "white"
nameColor = {
    RED: (255, 0, 0),
    BLUE: (0, 0, 255),
    YELLOW: (255, 255, 0),
    GREEN: (0, 255, 0),
    PURPLE: (128, 0, 128),
    ORANGE: (255, 165, 0),
    WHITE: (255, 255, 255)
}


def getColor(str) -> ():
    # print(str)
    name = None
    for color in [RED, BLUE, YELLOW, GREEN, PURPLE, ORANGE]:
        if color in str:
            name = color

    if "colourB" in str:
        name = WHITE

    if name in nameColor:
        return nameColor[name]

    return nameColor[RED]


def main():
    # require image from server
    # TODO: change ip!
    serverIp, port = "192.168.0.50", 5432
    serverIp, port = "192.168.43.48", 5432
    try:
        requireImageFromURL(serverIp, port)
        print("REQUIRE OK!")
    except Exception as e:
        print(e)

    # execute template matching
    spriteSize = (110, 110)
    matchingCandy = MatchingCandy(spriteSize)
    matrixCopy = matchingCandy.getMatrix().copy()  # copy img
#    plt.imshow(matrixCopy)
#    plt.title(f"Screenshot")
#    plt.show()

    # take graph
    candyGraph: CandyGraph = matchingCandy.search()
    for node in candyGraph.getNodes():
        color = getColor(node[TYPE])
        draw(matrixCopy, node, color)

#    plt.imshow(matrixCopy)
#    plt.title(f"Matching")
#    plt.show()

    # get nodes and edges of graph for DLV
    nodesAndInformation = getInputDLVNodes(candyGraph)
    edges = getEdges(candyGraph)

    print(f"EDGES --> {edges}")
    print(f"NODES --> {nodesAndInformation}")

    # recall ASP program
    solution = DLVSolution()
    swap: Swap = solution.recallASP(edges, nodesAndInformation)

    # draw
    tmp = matchingCandy.getMatrix().copy()
    node1 = candyGraph.getNode(swap.get_id1())
    node2 = candyGraph.getNode(swap.get_id2())

    draw(tmp, node1, nameColor[WHITE])
    draw(tmp, node2, nameColor[WHITE])
    plt.imshow(tmp)
    plt.title(f"OPTIMUM {node1} --> {node2}.")
    plt.show()

    # make json file
    width, height = 110, 110
    x1,y1,x2,y2 = node1[PX], node1[PY], node2[PX], node2[PY]
    EL = 0  #percent of swipe enlargement
    if (abs(x1-x2) < 10):
	#swipe vertical
        SX1 = (x1+x2)/2+width/2
        SX2 = SX1
        SY1 = min(y1,y2) - height*EL/100  #+height/4
        SY2 = max(y1,y2) + height*(1+EL/100) #+height/4*3
    else:
        # assumiamo swipe orizzontale
        SY1 = (y1+y2)/2+height/2
        SY2 = SY1
        SX1 = min(x1,x2) - width*EL/100  #+width/4
        SX2 = max(x1,x2) + width*(1+EL/100)  #+width/4*3

    makeJson(SX1, SY1, SX2, SY2)
    print("COORD: %d %d %d %d" % (SX1, SY1, SX2, SY2))


if __name__ == '__main__':
    main()
