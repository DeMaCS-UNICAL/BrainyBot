import os
import sys
import time
import cv2 as cv
from matplotlib import pyplot as plt

from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.objectsMatrix import ObjectMatrix,ObjectCell, TypeOf
from AI.src.candy_crush.object_graph.constants import PX, PY, TYPE
from AI.src.candy_crush.constants import RED, YELLOW, PURPLE, GREEN, BLUE, WHITE, nameColor, ORANGE
from AI.src.candy_crush.detect.new_detect import MatchingCandy,draw, DISTANCE
from AI.src.candy_crush.dlvsolution.dlvsolution import DLVSolution
from AI.src.candy_crush.dlvsolution.helpers import get_input_dlv_nodes, get_edges, Swap, get_input_dlv_cells
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.vision.feedback import Feedback
from AI.src.validation.validation import Validation
from AI.src.constants import RESOURCES_PATH
from AI.src.constants import BENCHMARK_PATH
from AI.src.benchmark.benchmark_utils import BenchmarkUtils
from AI.src.candy_crush.constants import SRC_PATH
from languages.asp.asp_mapper import ASPMapper



def asp_input(input):
    matrix = input[1]
    to_return = get_input_dlv_cells(matrix)
    return to_return


def retrieve_config():
        result_dict={}
        with open(os.path.join(SRC_PATH,"config"), 'r') as file:
            for line in file:
                line = line.strip()
                key, value = line.split()
                result_dict[key] = float(value)
        return result_dict

      
def candy_crush(screenshot,debug = False, vision_validation=None,abstraction_validation=None,it=0, benchmark=False):
    # execute template matching
    spriteSize = (110, 110)

    matchingCandy = MatchingCandy(screenshot,spriteSize,retrieve_config(),debug,vision_validation!=None)
    if not debug:
        plt.ion()

    template_matches_list,candyMatrix,_ = matchingCandy.search()
    input = asp_input(("",candyMatrix))
    #for e in input:
        #print(ASPMapper.get_instance().get_string(e) + ".")
    success = True

    
    if debug:
        for r in candyMatrix.matrix:
            for c in r:
                print(c,end='\t')
            print()
    solution = DLVSolution()
    while True:
        # recall ASP program
        swap1,answer_set = solution.recall_asp(input)
        swap: Swap = swap1
        if swap == None:
            print("No moves found. Maybe there is no candy on screen?")
            _,candyMatrix,_ = MatchingCandy(screenshot,spriteSize,retrieve_config(),debug,vision_validation!=None).search()
        else:
            # draw
            
            cell1 = candyMatrix.get_cell(swap.get_id1())
            cell2 = candyMatrix.get_cell(swap.get_id2())
            matrix_copy=matchingCandy.get_matrix().copy()
            width, height = candyMatrix.delta[0],candyMatrix.delta[1]
            if  not vision_validation:
                draw(matrix_copy, (cell1.x,cell1.y),f"{swap.get_id1()}",width,height,nameColor[WHITE])
                draw(matrix_copy, (cell2.x,cell2.y),f"{swap.get_id1()}",width,height,nameColor[WHITE])
                plt.imshow( matrix_copy)
                plt.title(f"VISION")
                plt.show()
                if not debug:
                    plt.pause(0.1)
            #
            # Enlarges swipe coordinates so to start swiping not from the center of the candy but from the border
            #
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
            success,abstraction,input = feedback.request_feedback(matchingCandy.vision,matchingCandy.abstraction,asp_input,answer_set)
            matrix = abstraction[1]

