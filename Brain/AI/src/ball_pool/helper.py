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
    Matcher = MatchingBalls(screenshot, debug, validation,iteration)
    balls_chart = Matcher.get_balls_chart()
