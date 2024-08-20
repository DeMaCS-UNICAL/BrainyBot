
import math
import os
import time

from matplotlib import pyplot as plt

from AI.src.abstraction.helpers import getImg
from AI.src.constants import CLIENT_PATH, SCREENSHOT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.puzzle_bubble.detect.new_detect import MatchingBubblePuzzle
from AI.src.puzzle_bubble.dlvsolution.dlvsolution import DLVSolution
from AI.src.puzzle_bubble.dlvsolution.helpers import get_input_dlv_grid, get_input_dlv_player
from AI.src.webservices.helpers import getScreenshot

def asp_input(exagonal_matrix,player_bubbles):
    #call methods to return our list of ASP input class objects
    input = get_input_dlv_grid(exagonal_matrix)
    input.extend(get_input_dlv_player(player_bubbles))
    return input

def Shoot_bubble(bubble_info,move):

    os.chdir(CLIENT_PATH)

    br = bubble_info[2]

    SX1 = bubble_info[0]
    SY1 = bubble_info[1]

    #swaps player bubble based on which bubble is used in the Move predicate
    #da testare una volta collegato il cellulare
    TX1 = bubble_info[0]
    TY1 = bubble_info[1] + br * 4

    for i in range(move.get_index()):
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {TX1} {TY1}'")

    SY2 = bubble_info[1] - br * 3
    SX2 = int(SX1 + ((SY1 - SY2) / math.tan(math.radians(move.get_angle()))))

    os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {SX1} {SY1} {SX2} {SY2}'")
    time.sleep(2.5)

def get_input(matcher):
    #Takes exagonal_matrix and player bubbles
    exagonal_matrix,player_bubbles = matcher.SearchGrid()

    return exagonal_matrix,player_bubbles

def puzzle_bubble(screenshot, debug = False):
    matcher = MatchingBubblePuzzle(screenshot,debug)

    exagonal_matrix,player_bubbles = get_input(matcher)

    input = asp_input(exagonal_matrix,player_bubbles)

    #getting the player bubble coords and radius
    if(len(player_bubbles) > 0):
        bubble_info = player_bubbles[0]
    else:
        print("Error while recovering data about player bubbles, no player bubbles detected at the start?")
        return
    
    for element in input:
        print(element, end="")

    #how the solution will be
    while(True):
        
        solution = DLVSolution()
        move = solution.recall_asp(input)

        if move is None:
            print("No possible move found.")
            return
        
        Shoot_bubble(bubble_info,move)

        if not getScreenshot():
            print("Screenshot Not Taken")
            return
        
        for element in input:
            print(element)

        exagonal_matrix,player_bubbles = get_input(matcher)
        input = asp_input(exagonal_matrix,player_bubbles)

