import os

from AI.src.ball_sort.constants import CLIENT_PATH
from AI.src.ball_sort.detect.detect import MatchingBalls
from AI.src.ball_sort.dlvsolution.dlvsolution import DLVSolution
from AI.src.ball_sort.dlvsolution.helpers import get_colors, get_balls_and_tubes, get_balls_position
from AI.src.ball_sort.ballschart.ballschart import BallsChart
from AI.src.webservices.helpers import make_json, require_image_from_url


def __get_ball_tube(ball, ons, step):
    for on in ons:
        if on.get_ball_above() == ball and on.get_step() == step:
            return on.get_tube()


def main():

     # TODO: change ip!
    server_ip, port = "192.168.85.45", 5432
    try:
        require_image_from_url(server_ip, port)
        print("SCREENSHOT TAKEN.")
    except Exception as e:
        print(e)

    matching_tubes = MatchingBalls()
    matching_tubes.detect_balls()
    matching_tubes.detect_empty_tube()

    ball_chart = BallsChart()
    colors = get_colors(ball_chart.get_tubes())
    tubes, balls = get_balls_and_tubes(ball_chart.get_tubes())
    on = get_balls_position(tubes)

    '''
    for color in colors:
        print(f"Colore {color.get_id()}")

    for ball in balls:
        print(f"Pallina {ball.get_id()} di colore {ball.get_color()}")

    for tube in tubes:
        print(f"Il tubo {tube.get_id()} ha coordinate {tube.get_x()} , {tube.get_y()} e le seguenti palline:")
        for ball in tube.get_balls():
            print(f"Id: {ball.get_id()}, colore: {ball.get_color()}")
    
    for o in on:
        print(f"La pallina {o.get_ball_above()} sta sulla pallina {o.get_ball_below()} nel tubo {o.get_tube()} allo step {o.get_step()}")
    '''

    solution = DLVSolution()
    moves, ons = solution.call_asp(colors, balls, tubes, on)

    moves.sort(key=lambda x: x.get_step())
    ons.sort(key=lambda x: x.get_step())

    for move in moves:
        print(f"Sposto la pallina {move.get_ball()} nel tubo {move.get_tube()} allo step {move.get_step()}")

    '''
    for on in ons:
        print(f"La pallina {on.get_ball_above()} si trova sulla pallina {on.get_ball_below()} nel tubo {on.get_tube()} allo step {on.get_step()}")
    '''

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

    make_json(coordinates)


if __name__ == '__main__':
    main()
