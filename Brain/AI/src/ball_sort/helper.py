import os
import sys
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.ball_sort.detect.new_detect import MatchingBalls
from AI.src.ball_sort.dlvsolution.dlvsolution import DLVSolution
from AI.src.ball_sort.dlvsolution.helpers import get_colors, get_balls_and_tubes, get_balls_position
from AI.src.abstraction.elementsStack import ElementsStacks


def __get_ball_tube(ball, ons, step):
    for on in ons:
        if on.get_ball_above() == ball and on.get_step() == step:
            return on.get_tube()


def ball_sort(screenshot:str, debug = False):

    matcher = MatchingBalls(screenshot,debug)
    balls_chart = matcher.get_balls_chart()
    colors = get_colors(balls_chart.get_stacks())
    tubes, balls = get_balls_and_tubes(balls_chart.get_stacks())
    empty_stacks = balls_chart.get_empty_stack()
    print(f"{screenshot.split('.')[1]}\t{len(tubes)-len(empty_stacks)}\t{len(empty_stacks)}\t{len(balls)}\t{len(colors)}",file=sys.stderr)
    on = get_balls_position(tubes)
    if(debug):
        balls_chart.Clean()
        return
    solution = DLVSolution()
    moves, ons = solution.call_asp(colors, balls, tubes, on)

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
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x2} {y2}'")
        
