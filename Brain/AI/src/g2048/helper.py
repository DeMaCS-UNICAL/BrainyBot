import os

from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.g2048.detect.new_detect import Matching2048
from AI.src.g2048.abstraction.graph2048 import Graph2048
from AI.src.g2048.dlvsolution.dlvsolution import DLVSolution
from AI.src.webservices.helpers import getScreenshot
from time import sleep
from math import sqrt

def g2048(screenshot, debug = False, validation=None,iteration=0):
    print("START 2048")
    matcher = Matching2048(screenshot,debug,validation,iteration)
    cx = matcher.get_image_width() // 2
    cy = matcher.get_image_height() // 2
    l = matcher.find_numbers_multithread()
    n = int(sqrt(len(l)))
    g = Graph2048(n)
    solver = DLVSolution()
    solver.start_asp("encoding.asp", g.nodes, g.superior, g.left)
    while not solver.isGameOver():
        print("New Screenshot taken")
        getScreenshot()
        matcher.set_image(screenshot)
        l = matcher.find_numbers_multithread()
        print(l)
        value = g.get_value(l)
        print("Numeri Letti")
        sw = solver.recall_asp(value)
        print("Mossa Trovata")
        acting(sw, cx, cy)
        sleep(1)

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
    
