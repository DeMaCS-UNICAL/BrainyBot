import os
import sys
import time
import re
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.ball_sort.detect.new_detect import MatchingBalls
from AI.src.ball_sort.dlvsolution.dlvsolution import DLVSolution,Ball,Color,Tube
from AI.src.ball_sort.dlvsolution.helpers import get_colors, get_balls_and_tubes, get_balls_position
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_sort.constants import SRC_PATH
from AI.src.vision.output_game_object import OutputCircle
from AI.src.vision.feedback import Feedback
from AI.src.validation.validation import Validation



def __get_ball_tube(ball, ons, step):
    for on in ons:
        if on.get_ball_above() == ball and on.get_step() == step:
            return on.get_tube()

def asp_input(balls_chart):
    colors = get_colors(balls_chart.get_stacks())
    tubes, balls = get_balls_and_tubes(balls_chart.get_stacks())
    
    input=colors.copy()
    input.extend(tubes)
    input.extend(balls)
    on,on_for_feedback = get_balls_position(tubes)
    input.extend(on)
    empty_stacks = balls_chart.get_empty_stack()
    input.extend(empty_stacks)
    return input,colors,tubes,balls,on,on_for_feedback

def check_if_to_revalidate(output,last_output):
    not_done=True
    distance_sum=0
    threshold = output[0][1]
    for o in output:
        distance_sum+=o[0]
    if last_output==None or len(last_output)==0:
        last_output=[10000,0]
    last_distance_sum=last_output[0]
    last_threshold = last_output[1]
    print("distance sum:",distance_sum,"threshold:",threshold)
    if distance_sum <2:
        persist_threshold(threshold)
        not_done= False
    elif distance_sum>last_distance_sum :
        print("distance sum:",distance_sum,"last distance:",last_distance_sum)
        persist_threshold(last_threshold)
        not_done= False
    return not_done,[distance_sum,threshold]


def persist_threshold(value):
    f = open(os.path.join(SRC_PATH,"config"), "r")
    x=f.read()
    f.close()
    f = open(os.path.join(SRC_PATH,"config"), "w")
    f.write(re.sub('CANNY_THRESHOLD=([^\n]+)', 'CANNY_THRESHOLD='+str(value), x,flags=re.M))
    print("threshold set to:", value)

def read_validation_data(validation_input):
    tubes={"empty":[],"no_empty":[]}
    balls:list[OutputCircle]=[]
    with open(validation_input) as file:
        for line in file:
            
            if "empty" in line:
                split=line.split()
                if "not_empty" in line:
                    tubes["no_empty"].append((split[0],split[1]))
                else:
                    tubes["empty"].append((split[0],split[1]))
            else:
                split_color = line.split("[")
                print(split_color)
                coord_radius = split_color[0]
                split_color[1]=split_color[1].lstrip()
                split_color[1]=split_color[1].lstrip("]")###################
                color = split_color[1].split(",")
                balls.append(OutputCircle(coord_radius[0],coord_radius[1],coord_radius[2],color))
    for k in tubes.keys():
        print(tubes[k])
    for ball in balls:
        print(ball.color)
    return tubes,balls

def ball_sort(screenshot, debug = False, vision_val=None, abstraction=None,iteration=0):
    matcher = MatchingBalls(screenshot,debug,vision_val!=None,iteration)
    balls_chart = matcher.get_balls_chart()
    balls : list[OutputCircle]=[]
    
    if balls_chart!=None:
        #'''TEMP
        for tube in balls_chart.get_stacks():
            print((int)(tube.get_x()),(int)(tube.get_y()),end=" ")
            if len(tube.get_elements())==0:
                print("Empty")
            else:
                print("Not_empty")
                for ball in tube.get_elements():
                    balls.append(ball)
        for ball in balls:
            print(ball.x,ball.y,ball.radius,ball.color)
        #'''
        input,colors,tubes,balls,on,on_feedback = asp_input(balls_chart)
    else:
        input=[]
        tubes=[]
    distance=0
    if vision_val!=None:
        read_validation_data(vision_val)
        '''
        validator = Validation()
        validate=[]
        validate.extend(tubes)
        distance = validator.validate_stacks(validate,read_validation_data(vision_val))
        '''
        return distance, matcher.canny_threshold
    recompute=True
    while recompute:
        solution = DLVSolution()
        moves, ons, ans = solution.call_asp(colors,balls,tubes,on)

        moves.sort(key=lambda x: x.get_step())
        ons.sort(key=lambda x: x.get_step())

        os.chdir(CLIENT_PATH)

        coordinates = []
        x1, y1, x2, y2 = 0, 0, 0, 0
        if len(moves)==0:
            print("No moves found.")
            return
        feedback=Feedback()
        for i in range(len(moves)):
            step=i
            move=moves[i]
            previous_tube = __get_ball_tube(move.get_ball(), ons, move.get_step())
            next_tube = move.get_tube()
            for tube in tubes:
                if tube.get_id() == previous_tube:
                    x1 = tube.get_x()
                    y1 = tube.get_y()
                elif tube.get_id() == next_tube:
                    x2 = tube.get_x()
                    y2 = tube.get_y()
            coordinates.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
            os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x1} {y1}'")
            time.sleep(0.25)
            os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x2} {y2}'")
            time.sleep(0.25)
            success,_,(_,colors,tubes,balls,on,on_feedback) = feedback.request_feedback(matcher.vision,matcher.abstraction,asp_input,ans[step])
            print("Success?",success)
            if not success:
                break
            if i==len(moves)-1:
                recompute=False
        
        
        