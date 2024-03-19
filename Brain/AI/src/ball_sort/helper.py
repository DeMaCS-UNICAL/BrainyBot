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

from AI.src.vision.feedback import Feedback


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
    on = get_balls_position(tubes)
    input.extend(on)
    empty_stacks = balls_chart.get_empty_stack()
    input.extend(empty_stacks)
    return input,colors,tubes,balls,on

def check_if_to_revalidate(output,last_output):
    not_done=True
    distance_sum=0
    threshold = output[0][1]
    for o in output:
        distance_sum+=o[0]
    if len(last_output)==0:
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


def ball_sort(screenshot, debug = False, validation=None,iteration=0):
    matcher = MatchingBalls(screenshot,debug,validation,iteration)
    balls_chart = matcher.get_balls_chart()
    if balls_chart!=None:
        input,colors,tubes,balls,on = asp_input(balls_chart)
    else:
        input=[]
        tubes=[]
    if(debug):
        return matcher.canny_threshold
    solution = DLVSolution()
    moves, ons = solution.call_asp(colors,balls,tubes,on)

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
        
        