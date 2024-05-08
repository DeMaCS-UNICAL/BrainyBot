import os
import sys
import time

import cv2 as cv
from matplotlib import pyplot as plt

from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.objectsMatrix import ObjectMatrix,ObjectCell, TypeOf
from AI.src.candy_crush.object_graph.constants import PX, PY, TYPE
from AI.src.candy_crush.constants import RED, YELLOW, PURPLE, GREEN, BLUE, WHITE, nameColor, ORANGE
from AI.src.candy_crush.detect.new_detect import MatchingCandy,draw
from AI.src.candy_crush.dlvsolution.dlvsolution import DLVSolution
from AI.src.candy_crush.dlvsolution.helpers import get_input_dlv_nodes, get_edges, Swap, get_input_dlv_cells
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.vision.feedback import Feedback



def asp_input(matrix):
    #to_return = get_input_dlv_nodes(graph)
    #to_return.extend(get_edges(graph))
    to_return = get_input_dlv_cells(matrix)
    return to_return

def candy_crush(screenshot,debug = False):
    # execute template matching
    spriteSize = (110, 110)
    matchingCandy = MatchingCandy(screenshot,spriteSize,debug)
    if not debug:
        plt.ion()
    '''
    

    plt.imshow(matrixCopy)
    plt.title(f"Screenshot")
    plt.show()
    if not debug:
        plt.pause(0.1)
    '''

    # take graph
    #candyGraph: ObjectGraph = matchingCandy.search()
    candyMatrix : ObjectMatrix = matchingCandy.search()
   


    # get nodes and edges of graph for DLV
    input = asp_input(candyMatrix)

    success = True
    #print(f"EDGES --> {edges}")
    #print()
    #print(f"NODES --> {nodesAndInformation}")
    if(debug):
        return

    while success:
        # recall ASP program
        solution = DLVSolution()
        swap1,answer_set = solution.recall_asp(input)
        swap: Swap = swap1
        if swap is None:
            print("No moves found. Maybe there is no candy on screen?")
            candyMatrix = MatchingCandy(screenshot,spriteSize,debug).search()
        else:
            # draw
            tmp = matchingCandy.get_matrix().copy()
            #node1 = candyGraph.get_node(swap.get_id1())
            #node2 = candyGraph.get_node(swap.get_id2())
            cell1 = candyMatrix.get_cell(swap.get_id1())
            cell2 = candyMatrix.get_cell(swap.get_id2())
            draw(tmp, (cell1.x,cell1.y,cell2.get_value(),cell1.get_id()), nameColor[WHITE])
            draw(tmp, (cell2.x,cell2.y,cell2.get_value(),cell2.get_id()), nameColor[WHITE])
            plt.imshow(tmp)
            plt.title(f"OPTIMUM {cell1} --> {cell2}.")
            plt.show()
            if not debug:
                plt.pause(0.5)
            #
            # Enlarges swipe coordinates so to start swiping not from the center of the candy but from the border
            #
            width, height = 110, 110
            x1,y1,x2,y2 = cell1.x, cell1.y, cell2.x, cell2.y
            EL = 20  #pixels of swipe offset
            SX1 = x1
            SX2 = x2
            SY1 = y1
            SY2 = y2
            '''
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
            '''

            os.chdir(CLIENT_PATH)
            os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {SX1} {SY1} {SX2} {SY2}'")
            time.sleep(1)
            feedback = Feedback()
            success,candyMatrix,input = feedback.request_feedback(matchingCandy.vision,matchingCandy.abstraction,asp_input,answer_set)

    
