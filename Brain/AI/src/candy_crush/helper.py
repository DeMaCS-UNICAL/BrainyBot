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
from AI.src.validation.validation import Validation
from AI.src.constants import RESOURCES_PATH
from AI.src.candy_crush.constants import SRC_PATH

from languages.asp.asp_mapper import ASPMapper
class CCSValidation:
    def __init__(self):
         self.current_false_negative={}
         self.current_false_positive={}
         self.current_thresholds=retrieve_config()
         self.previous_distances={}
         self.previous_thresholds={}

def asp_input(matrix):
    #to_return = get_input_dlv_nodes(graph)
    #to_return.extend(get_edges(graph))
    to_return = get_input_dlv_cells(matrix)
    return to_return

def check_CCS(outputs,validationInfo:CCSValidation):
    print("checking")
    if validationInfo==None:
        validationInfo = CCSValidation()
    total_fn={}
    total_fp={}
    for out in outputs:
        for key in out[0][0]:
            if total_fn.get(key)==None:
                total_fn[key]=0
            total_fn[key] += out[0][0][key]
        for key in out[0][1]:
            if total_fp.get(key)==None:
                total_fp[key]=0
            total_fp[key] += out[0][1][key]
    validationInfo.current_false_negative=total_fn
    validationInfo.current_false_positive=total_fp
    print("Vision False negative:")
    for key in validationInfo.current_false_negative:
        validationInfo.current_thresholds[key] = round(validationInfo.current_thresholds[key]-0.01,2)
        print(key,validationInfo.current_false_negative[key])
    print("Vision False positive:")
    for key in validationInfo.current_false_positive:
        print(key,validationInfo.current_false_positive[key])


    update_config(validationInfo.current_thresholds)
    fp_a=0
    fn_a=0
    for out in outputs:
        fp_a+=out[1][0]
        fn_a+=out[1][1]
    print("Abstraction ---- False positive:",fp_a,"False negative:",fn_a)
    return len(validationInfo.current_false_negative.keys())>0,validationInfo

def retrieve_config():
        result_dict={}
        with open(os.path.join(SRC_PATH,"config"), 'r') as file:
            for line in file:
                line = line.strip()
                key, value = line.split()
                result_dict[key] = float(value)
        return result_dict

def update_config(thresholds:dict):
    current = retrieve_config()
    for key in thresholds.keys():
        current[key]=thresholds[key]
    with open(os.path.join(SRC_PATH,"config"), 'w') as file:
        for key in current:
            file.write(f"{key} {current[key]}\n")

     
        
def candy_crush(screenshot,debug = False, vision_validation=None,abstraction_validation=None,it=0):
    # execute template matching
    spriteSize = (110, 110)
    
    matchingCandy = MatchingCandy(screenshot,spriteSize,retrieve_config(),debug,vision_validation!=None)
    if not debug:
        plt.ion()

    template_matches_list,candyMatrix = matchingCandy.search()
   
    input = asp_input(candyMatrix)
    #for e in input:
        #print(ASPMapper.get_instance().get_string(e) + ".")
    success = True
    
    if vision_validation!=None:
        validation_abstraction=[]
        abstraction_result=[]
        validation_vision = {}
        validation_info = CCSValidation()
        if(vision_validation!=None):
            validation_vision,validation_abstraction=read_validation_data(vision_validation, abstraction_validation)
        for e in input:
            abstraction_result.append(ASPMapper.get_instance().get_string(e) + ".")
        validator = Validation()
        #validator.validate_matches(template_matches_list,validation_vision)
        #validator.validate_matrix(input,validation_abstraction)#TODO: ABSTRACTION VALIDATION
    #if(debug):
     #   with open(RESOURCES_PATH+"/"+screenshot+".txt",'w+') as f:
      #      print(validator.stringfy(objects_matrix),file=f)
        return (validator.validate_matches(template_matches_list,validation_vision, spriteSize[0]*0.1),(validator.validate_facts(abstraction_result,validation_abstraction)))#TODO: ABSTRACTION VALIDATION

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

def read_validation_data(vision_validation, abstraction_validation):
    validation_vision=[]
    validation_abstraction=[]
    with open(vision_validation,'r') as file:
            for line in file:
                line=line.strip()
                split = tuple(line.split())
                validation_vision.append(((int(split[0]),int(split[1])),split[2]))
    with open(abstraction_validation,'r') as file:
            for line in file:
                line=line.strip()
                validation_abstraction.append(line)
    return validation_vision,validation_abstraction

    
