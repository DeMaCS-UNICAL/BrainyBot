import os

import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

from AI.src.ball_sort.constants import SPRITE_PATH
from AI.src.ball_sort.detect.helpers import getImg
from AI.src.ball_sort.ballschart.elementStack import ElementsStacks
from AI.src.constants import SCREENSHOT_PATH
from AI.common_facilities.template_matching import TemplateMatching
from AI.common_facilities.balls_detection import BallsDetection
class MatchingBalls:

    TUBES_DISTANCE_RATIO = 8

    def __init__(self, debug = False):
        if not debug:
            screenshot = 'screenshot.png'
        else:
            print("Debug mode: using test screenshot")
            screenshot = 'testScreenshotBS.jpg'

        self.__image = getImg(os.path.join(SCREENSHOT_PATH, screenshot))
        self.__output = self.__image.copy()  # Used to display the result
        self.__tubeTemplates = {}
        for file in os.listdir(SPRITE_PATH):
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                print(f"Found Tube sprite {fullname}")
                img = getImg(fullname,0)
                self.__tubeTemplates[fullname]  = img
        self.balls_detector = BallsDetection(self.__image)
        self.template_matcher = TemplateMatching(self.__image, 0.8, True)
        self.__ball_chart = ElementsStacks()

    def detect_balls(self):
        circles = self.balls_detector.detect_balls()
        # ensure at least some circles were found
        if circles is not None:
            balls = []
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r, color) in circles:
                # get the color of pixel (x, y) form the blurred image
                print(f"Found ball:({x}, {y}): {color}")
                # draw the circle
                cv.circle(self.__output, (x, y), r,(0,255,0), 2)
                cv.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                cv.putText(self.__output, f"({x}, {y})", (x + 10, y), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                balls.append([x, y, color])

            self.__ball_chart.setup_non_empty_stack(balls)

    def detect_empty_tube(self):
        for name in self.__tubeTemplates:
            print(f"Trying to detect empty tube {name}")
            match = self.__empty_tube(self.__tubeTemplates[name])
            print(f"Matches:{len(match)}")
            if len(match) > 0:
                break

        self.__show_result()
        self.__ball_chart.setup_empty_stack(match)

    def __empty_tube(self, template):
        width = self.__image.shape[1]
        print(f"Template size: {template.shape}")
        w, h = template.shape[::-1]
        loc = self.template_matcher.match(template)
        match = []
        for p in zip(*loc[::-1]):
            if all(abs(p[0] - m[0]) > (width/MatchingBalls.TUBES_DISTANCE_RATIO) for m in match):
                match.append(p)

        match = [(int(m[0] + w / 2), int(m[1] + h / 2)) for m in match]

        # draw the empty tubes
        for p in match:
            cv.rectangle(self.__output, (int(p[0] - w/2), int(p[1] - h/2)), (int(p[0] + w/2), int(p[1] + h/2)), (0, 0, 255), 3)
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
        edges = cv.Canny(self.__image, 300, 600)
        edges = cv.cvtColor(edges, cv.COLOR_GRAY2RGB)
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'edges.png'), edges)
        resized_input = cv.cvtColor(cv.resize(self.__image, dim, interpolation=cv.INTER_AREA), cv.COLOR_BGR2RGB)
        resized_edges = cv.cvtColor(cv.resize(edges, dim, interpolation=cv.INTER_AREA), cv.COLOR_BGR2RGB)
        resized_output = cv.cvtColor(cv.resize(self.__output, dim, interpolation=cv.INTER_AREA), cv.COLOR_BGR2RGB)
        #####resized_blurred = cv.cvtColor(cv.resize(self.__blurred, dim, interpolation=cv.INTER_AREA), cv.COLOR_BGR2RGB)
        #####result = np.concatenate((resized_input, resized_edges, resized_output, resized_blurred), axis=1)
        result = np.concatenate((resized_input, resized_edges, resized_output), axis=1)
        plt.figure(dpi=300)
        plt.imshow(result)
        plt.show()
        cv.waitKey(0)
