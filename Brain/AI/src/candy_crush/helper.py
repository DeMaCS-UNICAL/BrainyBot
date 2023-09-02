import os
import time

import cv2 as cv
from matplotlib import pyplot as plt

from AI.src.candy_crush.candygraph.candygraph import CandyGraph
from AI.src.candy_crush.candygraph.constants import PX, PY, TYPE
from AI.src.candy_crush.constants import RED, YELLOW, PURPLE, GREEN, BLUE, WHITE, nameColor, ORANGE
from AI.src.candy_crush.detect.detect import MatchingCandy
from AI.src.candy_crush.dlvsolution.dlvsolution import DLVSolution
from AI.src.candy_crush.dlvsolution.helpers import get_input_dlv_nodes, get_edges, Swap
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP


def draw(matrixCopy, nodes, color):
    width, height = 110, 110
    cv.rectangle(matrixCopy, (nodes[PX], nodes[PY]), (nodes[PX] + width, nodes[PY] + height), color, 10)


def get_color(strg) -> ():
    # print(strg)
    name = None
    for color in [RED, BLUE, YELLOW, GREEN, PURPLE, ORANGE]:
        if color in strg:
            name = color

    if "colourB" in strg:
        name = WHITE

    if name in nameColor:
        return nameColor[name]

    return nameColor[RED]


def candy_crush(debug = False):
    # execute template matching
    spriteSize = (110, 110)
    matchingCandy = MatchingCandy(spriteSize,debug)
    matrixCopy = matchingCandy.get_matrix().copy()  # copy img

    plt.ion()

    plt.imshow(matrixCopy)
    plt.title(f"Screenshot")
    plt.show()
    if not debug:
        plt.pause(0.1)

    # take graph
    candyGraph: CandyGraph = matchingCandy.search()
    for node in candyGraph.get_nodes():
        color = get_color(node[TYPE])
        draw(matrixCopy, node, color)

    plt.imshow(matrixCopy)
    plt.title(f"Matching")
    plt.show()
    if not debug: 
        plt.pause(0.5)


    # get nodes and edges of graph for DLV
    nodesAndInformation = get_input_dlv_nodes(candyGraph)
    edges = get_edges(candyGraph)

    print(f"EDGES --> {edges}")
    print(f"NODES --> {nodesAndInformation}")

    # recall ASP program
    solution = DLVSolution()
    swap: Swap = solution.recall_asp(edges, nodesAndInformation)

    if swap is None:
        print("No moves found. Maybe there is no candy on screen?")
    else:
        # draw
        tmp = matchingCandy.get_matrix().copy()
        node1 = candyGraph.get_node(swap.get_id1())
        node2 = candyGraph.get_node(swap.get_id2())

        draw(tmp, node1, nameColor[WHITE])
        draw(tmp, node2, nameColor[WHITE])
        plt.imshow(tmp)
        plt.title(f"OPTIMUM {node1} --> {node2}.")
        plt.show()
        if not debug:
            plt.pause(0.5)


        #
        # Enlarges swipe coordinates so to start swiping not from the center of the candy but from the border
        #
        width, height = 110, 110
        x1,y1,x2,y2 = node1[PX], node1[PY], node2[PX], node2[PY]
        EL = 20  #pixels of swipe offset
        
        if (abs(x1-x2) < 10):
	    #swipe vertical
            SX1 = int( (x1+x2)/2+width/2 )
            SX2 = SX1
            SY1 = int(min(y1,y2)+EL) 
            SY2 = int(max(y1,y2) + height+EL) 
        else:
        # assumiamo swipe orizzontale
            SY1 = int((y1+y2)/2+height/2)
            SY2 = int(SY1)
            SX1 = int(min(x1,x2)+EL) 
            SX2 = int(max(x1,x2) + width + EL)  


        os.chdir(CLIENT_PATH)
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {SX1} {SY1} {SX2} {SY2}'")
    
    
