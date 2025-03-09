import os

from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.g2048.detect.new_detect import Matching2048
from AI.src.g2048.abstraction.graph2048 import Graph2048
from AI.src.g2048.dlvsolution.dlvsolution import DLVSolution
from AI.src.webservices.helpers import getScreenshot
from time import sleep
from math import sqrt

def g2048(screenshot, debug = False, vision_validation=None, abstraction_validation=None, iteration=0, benchmark=False):
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
    