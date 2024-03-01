import os
import sys
import time

from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.ball_sort.detect.new_detect import MatchingBalls
from AI.src.ball_sort.dlvsolution.dlvsolution import DLVSolution,Ball,Color,Tube
from AI.src.ball_sort.dlvsolution.helpers import get_colors, get_balls_and_tubes, get_balls_position
from AI.src.abstraction.elementsStack import ElementsStacks

from AI.src.vision.feedback import Feedback
from AI.src.validation.validation import Validation


def __get_ball_tube(ball, ons, step):
    for on in ons:
        if on.get_ball_above() == ball and on.get_step() == step:
            return on.get_tube()

def asp_input(balls_chart):
    input = get_colors(balls_chart.get_stacks())
    tubes, balls = get_balls_and_tubes(balls_chart.get_stacks())
    input.extend(tubes)
    input.extend(balls)
    on = get_balls_position(tubes)
    input.extend(on)
    empty_stacks = balls_chart.get_empty_stack()
    input.extend(empty_stacks)
    return input,tubes

def ball_sort(screenshot, debug = False, validation=None):

    matcher = MatchingBalls(screenshot,debug,validation)
    balls_chart = matcher.get_balls_chart()
    input,tubes = asp_input(balls_chart)
    validator = Validation()
    if validation!=None:
        validate=[]
        validate.extend(tubes)
        validator.validate_stacks(validate,validation)
    if(debug):
        Ball.reset()
        Tube.reset()
        Color.reset()
        balls_chart.Clean()
        return
    solution = DLVSolution()
    moves, ons = solution.call_asp(input)

    moves.sort(key=lambda x: x.get_step())
    ons.sort(key=lambda x: x.get_step())

    os.chdir(CLIENT_PATH)

    coordinates = []
    x1, y1, x2, y2 = 0, 0, 0, 0
    for move in moves:
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
        
