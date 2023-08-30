import os

import cv2
import numpy as np
from matplotlib import pyplot as plt

from AI.src.ball_sort.constants import SPRITE_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.stack import Stack
from AI.src.abstraction.elementsStack import ElementsStacks


class MatchingBalls:

    BALLS_DISTANCE_RATIO = 30
    TUBES_DISTANCE_RATIO = 8
    RADIUS_RATIO = 50

    def __init__(self, screenshot_path, debug = False):
        self.finder = ObjectsFinder(screenshot_path,debug=debug)
        
        self.__image = getImg(os.path.join(SCREENSHOT_PATH, screenshot_path))
        self.__output = self.__image.copy()  # Used to display the result
        self.__tubeTemplates = {}
        self.__balls=[]
        for file in os.listdir(SPRITE_PATH):
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                print(f"Found Tube sprite {fullname}")
                img = getImg(fullname,channel=0)
                self.__tubeTemplates[fullname]  = img
        self.__ball_chart = ElementsStacks()
        self.img_width = self.__image.shape[1]
        
    def get_balls_chart(self)->ElementsStacks:      
        abstraction = Abstraction()
        self.__balls = self.detect_balls()
        stacks = abstraction.Stack(self.__balls.copy())
        self.__ball_chart.add_stacks(stacks)
        template,tubes = self.detect_empty_tube()
        width = self.img_width
        matcher_width, matcher_height = template.shape[::-1]
        empty_stacks = abstraction.Empty_Stacks(tubes,width,matcher_width, matcher_height,MatchingBalls.TUBES_DISTANCE_RATIO)
        print(f"Matches:{len(empty_stacks)}")
        self.__ball_chart.add_stacks(empty_stacks)
        # draw the empty tubes
        for p in empty_stacks:
            cv2.rectangle(self.__output, (int(p.get_x() - matcher_width/2), int(p.get_y() - matcher_height/2)), 
                          (int(p.get_x() + matcher_width/2), int(p.get_y() + matcher_height/2)), (0, 0, 255), 3)
        

        self.__show_result()
        return self.__ball_chart

    def detect_balls(self)->list:
        height = self.__image.shape[0]
        min_dist = int(height / MatchingBalls.BALLS_DISTANCE_RATIO)
        minRadius=int(height / MatchingBalls.RADIUS_RATIO)
        maxRadius=int(height / MatchingBalls.RADIUS_RATIO + 10)
        self.balls = self.finder.find_circles(min_dist,minRadius,maxRadius)
        return self.balls
        #self.__ball_chart.setup_non_empty_stack(self.balls.copy())

    def detect_empty_tube(self)->(int,list):
        for name in self.__tubeTemplates:
            print(f"Trying to detect empty tube {name}")
            matches = self.finder.find_matches(cv2.cvtColor(self.__image, cv2.COLOR_BGR2GRAY),self.__tubeTemplates[name],False)
            if len(matches) > 0:
                return self.__tubeTemplates[name],matches
        #self.__ball_chart.setup_empty_stack(match)
        return None,[]
        

    def get_image(self):
        return self.__image

    def __show_result(self):
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'output.png'), self.__output)
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'blurred.png'), self.__blurred)
        # print detecting result
        width = int(self.__image.shape[1] * 0.3)
        height = int(self.__image.shape[0] * 0.3)
        dim = (width, height)
        edges = cv2.Canny(self.__image, 300, 600)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'edges.png'), edges)
        for tube in self.__ball_chart.get_stacks():
            for (x, y, r,c) in tube.get_elements():
                    # draw the circle
                    cv2.circle(self.__output, (x, y), r, (c[0],c[1], c[2]), 10)
                    cv2.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                    cv2.putText(self.__output, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        resized_input = cv2.cvtColor(cv2.resize(self.__image, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        #resized_edges = cv2.cvtColor(cv2.resize(edges, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized_output = cv2.cvtColor(cv2.resize(self.__output, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        #resized_blurred = cv2.cvtColor(cv2.resize(self.__blurred, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        result = np.concatenate((resized_input, resized_output), axis=1)
        plt.figure(dpi=300)
        plt.imshow(result)
        plt.show()
        cv2.waitKey(0)
