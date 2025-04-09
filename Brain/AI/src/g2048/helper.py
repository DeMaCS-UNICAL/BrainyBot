import os

from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.g2048.detect.new_detect import Matching2048
from AI.src.g2048.abstraction.graph2048 import Graph2048
from AI.src.g2048.dlvsolution.dlvsolution import DLVSolution
from AI.src.webservices.helpers import getScreenshot
from AI.src.benchmark.benchmark_utils import BenchmarkUtils
from time import sleep
from math import sqrt

def g2048(screenshot, debug = False, vision_validation=None, abstraction_validation=None, iteration=0, benchmark=False):

    if benchmark:
        g2048_benchmark(screenshot)
        return

    print("START 2048")
    matcher = Matching2048(screenshot,debug,vision_validation,iteration)
    cx = matcher.get_image_width() // 2
    cy = matcher.get_image_height() // 2
    l = matcher.find_numbers()
    print(l)
    n = int(sqrt(len(l)))
    g = Graph2048(n)
    solver = DLVSolution()
    solver.start_asp("encoding.asp", g.nodes, g.superior, g.left)
    value = g.get_value(l)
    sw, output = solver.recall_asp(value)
    cache = setCache(output, len(l))
    acting(sw, cx, cy)
    while True:
        if not getScreenshot():
            print("Screenshot Not Taken")
            return
        matcher.set_image(screenshot)
        l = matcher.find_numbers_with_cache(cache)
        print(l)
        value = g.get_value(l)
        sw, output = solver.recall_asp(value)
        if solver.isGameOver():
            break
        cache = setCache(output, len(l))
        acting(sw, cx, cy)
    print("END GAME")


def g2048_benchmark(screenshot):
    benchmark_utils = BenchmarkUtils("2048")
    matching2048 = Matching2048(screenshot)

    while not benchmark_utils.is_game_finished():
        while not benchmark_utils.is_level_finished():
            print(f"Level {benchmark_utils.get_level_name()}, {benchmark_utils.get_step_name()} - cache")
            benchmark_utils.start_timer()
            l = matching2048.find_numbers()
            benchmark_utils.stop_timer()
            print(l)
            benchmark_utils.save_time(level=benchmark_utils.get_level_name(), step=benchmark_utils.get_step_name(), type="cache")
            benchmark_utils.load_new_step()
            matching2048.set_image(screenshot)
        benchmark_utils.load_new_level()
        matching2048.set_image(screenshot)
        matching2048 = Matching2048(screenshot)

    benchmark_utils.restart()
    benchmark_utils.load_current_level()

    matching2048 = Matching2048(screenshot, calculate_metadata=False)

    while not benchmark_utils.is_game_finished():
        while not benchmark_utils.is_level_finished():
            print(f"Level {benchmark_utils.get_level_name()}, {benchmark_utils.get_step_name()} - no cache")
            benchmark_utils.start_timer()
            l = matching2048.find_numbers()
            benchmark_utils.stop_timer()
            print(l)
            benchmark_utils.save_time(level=benchmark_utils.get_level_name(), step=benchmark_utils.get_step_name(), type="no cache")
            benchmark_utils.load_new_step()
            matching2048 = Matching2048(screenshot, calculate_metadata=False)
        benchmark_utils.load_new_level()
        matching2048 = Matching2048(screenshot, calculate_metadata=False)

    benchmark_utils.end_benchmark()

def acting(swipe_direction, cx, cy):
    offset_eo = 175
    offset = 125
    SX1 = SX2 = SY1 = SY2 = 0
    if swipe_direction == None:
        return
    if swipe_direction==1:
        SX1 = SX2 = cx
        SY1 = cy + offset
        SY2 = cy - offset
    if swipe_direction==2:
        SX1 = SX2 = cx
        SY1 = cy - offset
        SY2 = cy + offset
    if swipe_direction==3:
        SY1 = SY2 = cy
        SX1 = cx + offset_eo
        SX2 = cx - offset_eo
    if swipe_direction==4:
        SY1 = SY2 = cy
        SX1 = cx - offset_eo
        SX2 = cx + offset_eo
    os.chdir(CLIENT_PATH)
    os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {SX1} {SY1} {SX2} {SY2}'")

def setCache(output, l):
    cache = [0 for i in range(l)]
    for o in output:
        cache[o.get_node()] = o.get_value()
    return cache
    