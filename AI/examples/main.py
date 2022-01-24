import cv2
import sys
from matplotlib import pyplot as plt

from src.candygraph.candygraph import CandyGraph
from src.candygraph.constants import PX, PY, TYPE
from src.detect.detect import MatchingCandy
from src.dlvsolution.dlvsolution import DLVSolution
from src.dlvsolution.helpers import getInputDLVNodes, getEdges, Swap
from src.webservices.helpers import makeJson, requireImageFromURL
from time import sleep

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

def roundM(base,offset,n):
    return round((n-offset)/base)*base+offset

def main():
    # require image from server
    # TODO: change ip!
    serverIp, port = "192.168.0.50", 5432
#    serverIp, port = "192.168.43.48", 5432
    try:
        requireImageFromURL(serverIp, port)
        print("SCREENSHOT TAKEN.")
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

#    print(f"EDGES --> {edges}")
#    print(f"NODES --> {nodesAndInformation}")

    # call ASP program
    solution = DLVSolution()
    swap: Swap = solution.recallASP(edges, nodesAndInformation)

    if swap is None:
        print ("No moves found. Maybe there is no candy on screen?")
        quit()
    # draw
    tmp = matchingCandy.getMatrix().copy()
    node1 = candyGraph.getNode(swap.get_id1())
    node2 = candyGraph.getNode(swap.get_id2())

    draw(tmp, node1, nameColor[WHITE])
    draw(tmp, node2, nameColor[WHITE])
    plt.imshow(tmp)
    plt.title(f"OPTIMUM {node1} --> {node2}.")
#   plt.ion()

    # make json file
    width, height = 110, 110
    #
    # For candy crush level 1 demo:
    #
    topX = 325
    topY = 645
    #
    # All coordinates are assumed to be at the center of the candy
    #
    x1,y1,x2,y2 = node1[PX]+width/2, node1[PY]+height/2, node2[PX]+width/2, node2[PY]+height/2
    #
    # Rounds to the nearest multiple of 110
    #
    x1 = roundM(width,topX,x1)
    y1 = roundM(height,topY,y1)
    x2 = roundM(width,topX,x2)
    y2 = roundM(height,topY,y2)
    startEL = 20  #pixels of swipe elongation from the candy's center
    endEL = 55
    if (abs(x1-x2) < 10):
	# swipe vertical
        SX1 = (x1+x2)/2
        SX2 = SX1
        SY1 = min(y1,y2) - startEL
        SY2 = max(y1,y2) + endEL 
    else:
        # swipe horizontal
        SY1 = (y1+y2)/2
        SY2 = SY1
        SX1 = min(x1,x2) - startEL 
        SX2 = max(x1,x2) + endEL 

    makeJson(SX1, SY1, SX2, SY2)
    print("COORD: %d %d %d %d" % (SX1, SY1, SX2, SY2))
    sys.stdout.flush()
    plt.show()
    plt.pause(1)


if __name__ == '__main__':
    plt.ion()
    for i in range(0,15):
        main()
        sleep(10)
#    input("Press any key to continue")
