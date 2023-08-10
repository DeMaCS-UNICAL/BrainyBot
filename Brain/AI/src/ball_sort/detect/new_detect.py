import os

import cv2
import numpy as np
from matplotlib import pyplot as plt

from AI.src.ball_sort.constants import SPRITE_PATH
from AI.src.ball_sort.detect.helpers import getImg
from AI.src.ball_sort.ballschart.ballschart import BallsChart
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder


class MatchingBalls:

    BALLS_DISTANCE_RATIO = 30
    TUBES_DISTANCE_RATIO = 8
    RADIUS_RATIO = 50

    def __init__(self, debug = False):
        if debug:
            screenshot = 'testScreenshotBS.jpg'
            self.finder = ObjectsFinder(cv2.COLOR_BGR2RGB,debug,'testScreenshotBS.jpg')
        else:
            screenshot = 'screenshot.png'
            self.finder = ObjectsFinder(cv2.COLOR_BGR2RGB)
        
        self.__image = getImg(os.path.join(SCREENSHOT_PATH, screenshot))
        self.__tubeTemplates = {}
        for file in os.listdir(SPRITE_PATH):
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                print(f"Found Tube sprite {fullname}")
                img = getImg(fullname,0)
                self.__tubeTemplates[fullname]  = img
        self.__ball_chart = BallsChart()

    def detect_balls(self):
        height = self.__image.shape[0]
        min_dist = int(height / MatchingBalls.BALLS_DISTANCE_RATIO)
        minRadius=int(height / MatchingBalls.RADIUS_RATIO)
        maxRadius=int(height / MatchingBalls.RADIUS_RATIO + 10)
        balls = self.finder.find_circles(min_dist,minRadius,maxRadius)
        self.__ball_chart.setup_full_tubes(balls)

    def detect_empty_tube(self):
        for name in self.__tubeTemplates:
            print(f"Trying to detect empty tube {name}")
            match = self.__empty_tube(self.__tubeTemplates[name])
            print(f"Matches:{len(match)}")
            if len(match) > 0:
                break

        self.__show_result()
        self.__ball_chart.setup_empty_tubes(match)

    def __empty_tube(self, template):
        width = self.__image.shape[1]
        tubes = self.finder.find_matches(template,False)
        w, h = template.shape[::-1]
        match = []
        for p in tubes:
            if all(abs(p[0] - m[0]) > (width/MatchingBalls.TUBES_DISTANCE_RATIO) for m in match):
                match.append(p)

        match = [(int(m[0] + w / 2), int(m[1] + h / 2)) for m in match]

        # draw the empty tubes
        for p in match:
            cv2.rectangle(self.__output, (int(p[0] - w/2), int(p[1] - h/2)), (int(p[0] + w/2), int(p[1] + h/2)), (0, 0, 255), 3)
        return match

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
        resized_input = cv2.cvtColor(cv2.resize(self.__image, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized_edges = cv2.cvtColor(cv2.resize(edges, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized_output = cv2.cvtColor(cv2.resize(self.__output, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized_blurred = cv2.cvtColor(cv2.resize(self.__blurred, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        result = np.concatenate((resized_input, resized_edges, resized_output, resized_blurred), axis=1)
        plt.figure(dpi=300)
        plt.imshow(result)
        plt.show()
        cv2.waitKey(0)
