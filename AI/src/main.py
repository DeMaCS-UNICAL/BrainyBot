import argparse
import os

from AI.src.ball_sort.ballschart.ballschart import BallsChart
from AI.src.ball_sort.constants import CLIENT_PATH
from AI.src.ball_sort.detect.detect import MatchingBalls
from AI.src.ball_sort.dlvsolution.helpers import get_colors, get_balls_position, get_balls_and_tubes
from AI.src.webservices.helpers import require_image_from_url
from AI.src.ball_sort.dlvsolution.dlvsolution import DLVSolution

def __get_ball_tube(ball, ons, step):
    for on in ons:
        if on.get_ball_above() == ball and on.get_step() == step:
            return on.get_tube()
        
        
def ball_sort():
    matching_tubes = MatchingBalls()
    matching_tubes.detect_balls()
    matching_tubes.detect_empty_tube()
    
    ball_chart = BallsChart()
    colors = get_colors(ball_chart.get_tubes())
    tubes, balls = get_balls_and_tubes(ball_chart.get_tubes())
    on = get_balls_position(tubes)

    solution = DLVSolution()
    moves, ons = solution.call_asp(colors, balls, tubes, on)

    moves.sort(key=lambda x: x.get_step())
    ons.sort(key=lambda x: x.get_step())

    for move in moves:
        print(f"Sposto la pallina {move.get_ball()} nel tubo {move.get_tube()} allo step {move.get_step()}")

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
        # TODO: change ip!
        os.system(f"python2 client.py --url http://192.168.85.37:8000 --light 'tap {x1} {y1}'")
        os.system(f"python2 client.py --url http://192.168.85.37:8000 --light 'tap {x2} {y2}'")

def candy_crush():
    pass

if __name__ == '__main__':

    msg = "Description"
    
    # Initialize parser
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g", "--games", type=str, help="Name of the games", choices = ["ball_sort", "candy_crush"], required=True)
    parser.parse_args()
    game = parser.parse_args()

    # TODO: change ip!
    server_ip, port = "192.168.1.33", 5432
    try:
        require_image_from_url(server_ip, port)
        print("SCREENSHOT TAKEN.")
    except Exception as e:
        print(e)
        
    if game.__eq__("ball_sort"):
        ball_sort()
    elif game.__eq__("candy_crush"):
        candy_crush()
        