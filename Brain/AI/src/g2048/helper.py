from AI.src.g2048.detect.new_detect import Matching2048
from AI.src.g2048.abstraction.graph2048 import Graph2048
from AI.src.g2048.dlvsolution.dlvsolution import DLVSolution
from AI.src.webservices.helpers import getScreenshot
from time import sleep
from math import sqrt

def g2048(screenshot, debug = False, validation=None,iteration=0):
    print("START 2048")
    matcher = Matching2048(screenshot,debug,validation,iteration)
    l = matcher.find_numbers()
    print(l)
    n = int(sqrt(len(l)))
    g = Graph2048(n)
    solver = DLVSolution()
    solver.start_asp("encoding.asp", g.nodes, g.superior, g.left)
    while not matcher.isOver():
        print("New Screenshot taken")
        getScreenshot()
        matcher.set_image(screenshot)
        l = matcher.find_numbers()
        value = g.get_value(l)
        solver.recall_asp(value)
        sleep(4)