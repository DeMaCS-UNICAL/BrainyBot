import os
import sys
import time
import re
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
#from AI.src.ball_sort.detect.new_detect import MatchingBalls
from AI.src.ball_sort.dlvsolution.dlvsolution import DLVSolution,Ball,Color,Tube
from AI.src.ball_sort.dlvsolution.helpers import get_colors, get_balls_and_tubes, get_balls_position
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_sort.constants import SRC_PATH

from AI.src.vision.feedback import Feedback
from Brain.AI.src.ball_pool.detect.new_detect import MatchingBalls



def ball_pool(screenshot, debug = False, validation=None,iteration=0):
    matcher = MatchingBalls(screenshot, debug, validation,iteration)
    pool_table = matcher.get_balls_chart()


    balls_chart =  #prende l'immagine e restituisce la lista di palle e container
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
        
        
