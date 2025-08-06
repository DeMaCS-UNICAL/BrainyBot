import os
import sys
import time
import cv2 
from matplotlib import pyplot as plt
from contextlib import redirect_stdout
from collections import defaultdict

from AI.src.candy_crush.constants import WHITE, nameColor, SPRITE_PATH
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.candy_crush.detect.new_detect import MatchingCandy,draw, DISTANCE
from AI.src.candy_crush.dlvsolution.dlvsolution import DLVSolution
from AI.src.candy_crush.dlvsolution.helpers import Swap, get_input_dlv_cells, ACTUAL_GAME
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.vision.feedback import Feedback
from AI.src.validation.validation import Validation
from AI.src.benchmark.benchmark_utils import BenchmarkUtils
from AI.src.candy_crush.constants import SRC_PATH
from languages.asp.asp_mapper import ASPMapper
from AI.src.abstraction.helpers import getImg


class CCSValidation:
    def __init__(self,tuning):
         self.current_vision_false_negative={}
         self.current_vision_false_positive={}
         self.current_vision_thresholds=retrieve_config(1 if tuning else 0.65)
         self.previous_distances={}
         self.previous_thresholds={}


def check_CCS(outputs,validationInfo:CCSValidation,tuning):
    for_printing={k:{"fn":[],"fp":[]} for k in SPRITES}
    if validationInfo==None:
        validationInfo = CCSValidation(tuning)
    total_fn, total_fp = vision_validation(outputs, for_printing)    
    abstraction_validation(outputs)

    done=True
    if tuning:
        done = tune_vision_thresholds(validationInfo, for_printing, total_fn, total_fp)

    
    validationInfo.current_vision_false_negative=total_fn
    validationInfo.current_vision_false_positive=total_fp
    return not done,validationInfo

def abstraction_validation(outputs):
    with open(os.path.join(SRC_PATH,"abstraction_results.csv"), 'w') as f:
        with redirect_stdout(f):
            print("False Positive,False Negative")
            for out in outputs:
                print(out[1][0],",",out[1][1])
    

    

def tune_vision_thresholds(validationInfo, for_printing, total_fn, total_fp):
    done=True
    print("Vision False negative:")
    for key in total_fn:
        if total_fn[key]>0 and (key not in validationInfo.current_false_negative or total_fn[key]<= validationInfo.current_false_negative[key]):
            done=False
            validationInfo.current_thresholds[key] = round(validationInfo.current_thresholds[key]-0.01,2)
            print(key,total_fn[key])
        elif total_fn[key]>0:
            print(key,total_fn[key], "impossible to decrease")

    print("Vision False positive:")
        
    for key in total_fp:
        if total_fp[key]>0:
            print(key,total_fp[key])
    for key in for_printing:
        if key not in validationInfo.current_thresholds:
            validationInfo.current_thresholds[key]=1
        
    if done:
        for key in total_fn:
                #Tuning is finished, if there are still false negative, it means that at the previous threshold it was better
            if total_fn[key]>0:
                validationInfo.current_thresholds[key] = round(validationInfo.current_thresholds[key]+0.01,2)
    update_config(validationInfo.current_thresholds)
    return done

def vision_validation(outputs, for_printing):
    total_fn=defaultdict(int)
    total_fp=defaultdict(int)
    for key in for_printing:
        for out in outputs:
            if key in out[0][0]:
                for_printing[key]["fn"].append( out[0][0][key])
                total_fn[key]+=out[0][0][key]
            else:
                for_printing[key]["fn"].append(-1)
            if key in out[0][1]:
                for_printing[key]["fp"].append(out[0][1][key])
                total_fp[key]+=out[0][1][key]
            else:
                for_printing[key]["fp"].append(-1)
     
    print_validation_output(for_printing,'vision_results.csv')
    return total_fn,total_fp

def print_validation_output(for_printing,file_name):
    with open(os.path.join(SRC_PATH,file_name), 'w') as f:
        with redirect_stdout(f):
            for key in for_printing:
                line = [key]
                for fp_val, fn_val in zip(for_printing[key]["fp"], for_printing[key]["fn"]):
                    line.extend([",",fp_val, fn_val])
                print(*line)

def retrieve_config(default_value=0.65):
        result_dict=defaultdict(lambda:default_value)

        try:
            with open(os.path.join(SRC_PATH,"config_"+ACTUAL_GAME), 'r') as file:
                for line in file:
                    line = line.strip()
                    key, value = line.split()
                    result_dict[key] = float(value)
        except:
            # print("no configuration file found") TODO: uncomment
            pass
        return result_dict

def update_config(thresholds:dict):
    current = retrieve_config()
    for key in thresholds.keys():
        current[key]=thresholds[key]
    with open(os.path.join(SRC_PATH,"config_"+ACTUAL_GAME), 'w') as file:
        for key in current:
            file.write(f"{key} {current[key]}\n")


def asp_input(matrix):
    to_return = get_input_dlv_cells(matrix)
    return to_return


def candy_crush_benchmark(resource_path, tuning):
    benchmark_utils = BenchmarkUtils("candy_crush", resource_path)
    screenshot = benchmark_utils.get_screenshot_path()
    matchingCandy = MatchingCandy(screenshot, retrieve_config(1 if tuning else 0.65), False, False)

    while not benchmark_utils.is_game_finished():
        while not benchmark_utils.is_level_finished():
            print(f"{benchmark_utils.get_level_name()}, {benchmark_utils.get_step_name()} - cache")
            benchmark_utils.start_timer()
            matchingCandy.search(benchmark=True)
            benchmark_utils.stop_timer()
            benchmark_utils.save_time(level=benchmark_utils.get_level_name(), step=benchmark_utils.get_step_name(), type="cache")
            benchmark_utils.load_new_step()
        benchmark_utils.load_new_level()
        matchingCandy = MatchingCandy(screenshot, retrieve_config(1 if tuning else 0.65), False, False)

    matchingCandy = MatchingCandy(screenshot, retrieve_config(1 if tuning else 0.65), False, False)
    benchmark_utils.restart()

    while not benchmark_utils.is_game_finished():
        while not benchmark_utils.is_level_finished():
            print(f"{benchmark_utils.get_level_name()}, {benchmark_utils.get_step_name()} - no cache")
            benchmark_utils.start_timer()
            matchingCandy.search(benchmark=True)
            benchmark_utils.stop_timer()
            matchingCandy = MatchingCandy(screenshot, retrieve_config(1 if tuning else 0.65), False, False)
            benchmark_utils.save_time(level=benchmark_utils.get_level_name(), step=benchmark_utils.get_step_name(), type="no cache")
            benchmark_utils.load_new_step()
        benchmark_utils.load_new_level()

    benchmark_utils.end_benchmark()

        
def candy_crush(screenshot,debug = False, vision_validation=None,abstraction_validation=None,iteration=0,tuning=False, benchmark=False):

    # execute template matching
    spriteSize = DISTANCE

    if benchmark:
        candy_crush_benchmark(screenshot, tuning)
        return

    matchingCandy = MatchingCandy(screenshot, retrieve_config(1 if tuning else 0.65), debug, vision_validation != None)
    if not debug:
        plt.ion()

    template_matches_list,candyMatrix,_ = matchingCandy.search()
    #for m in sorted(template_matches_list,key=lambda x : x.x):
        #print(m.x,m.y,m.label)
    if candyMatrix is not None:
        input = asp_input(candyMatrix)
        #for e in input:
            #print(e.x, e.y)
            #print(ASPMapper.get_instance().get_string(e) + ".")
    success = True

    
    if vision_validation!=None:
        validation_abstraction=[]
        abstraction_result=[]
        validation_vision = {}
        validation_info = CCSValidation(tuning)
        if(vision_validation!=None):
            validation_vision,validation_abstraction=read_validation_data(vision_validation, abstraction_validation)
        if candyMatrix is not None:
            for e in input:
                abstraction_result.append(ASPMapper.get_instance().get_string(e) + ".")
        validator = Validation()
        #validator.validate_matches(template_matches_list,validation_vision)
        #validator.validate_matrix(input,validation_abstraction)#TODO: ABSTRACTION VALIDATION
        #   with open(RESOURCES_PATH+"/"+screenshot+".txt",'w+') as f:
        tolerance = 0 if candyMatrix is None else candyMatrix.delta[0]*0.3
        return (validator.validate_matches(template_matches_list,validation_vision, tolerance),(validator.validate_facts(abstraction_result,validation_abstraction)))#TODO: ABSTRACTION VALIDATION
    if debug:
        for r in candyMatrix.matrix:
            for c in r:
                print(c,end='\t')
            print()
    while True:
        # recall ASP program
        solution = DLVSolution()
        swap1,answer_set = solution.recall_asp(input)
        swap: Swap = swap1
        if swap == None:
            print("No moves found. Maybe there is no candy on screen?")
            template_matches_list,candyMatrix,_ = MatchingCandy(screenshot,spriteSize,retrieve_config(),debug,vision_validation!=None).search()
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
            os.chdir(CLIENT_PATH)
            os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {SX1} {SY1} {SX2} {SY2}'")
            time.sleep(1)
            feedback = Feedback()
            success,candyMatrix,input = feedback.request_feedback(matchingCandy.vision,matchingCandy.abstraction,asp_input,answer_set)

def read_validation_data(vision_validation, abstraction_validation):
    validation_vision=[]
    validation_abstraction=[]
    try:
        with open(vision_validation,'r') as file:
                for line in file:
                    line=line.strip()
                    split = tuple(line.split())
                    if len(split)==2:
                        split=(split[0],split[1],"")
                    validation_vision.append(((int(split[0]),int(split[1])),split[2]))
    except:
        print("no vision file found for",vision_validation)
    try:
        with open(abstraction_validation,'r') as file:
                for line in file:
                    line=line.strip()
                    validation_abstraction.append(line)
    except:
        print("no abstraction file found for",vision_validation)

    return validation_vision,validation_abstraction

    
def init_sprites(path=SPRITE_PATH):
    print("templates at",path)
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and not file.endswith(".ini"): 
            img = getImg(os.path.join(path, file),color_conversion=cv2.COLOR_BGR2RGB)
            typeCandy = os.path.basename(file)
            SPRITES[typeCandy] = img
            height, width, _ = img.shape
            if width < DISTANCE[0]:
                DISTANCE[0]=width
            if height < DISTANCE[1]:
                DISTANCE[1]=height