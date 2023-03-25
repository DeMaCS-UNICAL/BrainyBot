import os

import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

from AI.src.ball_sort.constants import SPRITE_PATH
from AI.src.ball_sort.detect.helpers import getImg
from AI.src.ball_sort.ballschart.ballschart import BallsChart
from AI.src.constants import SCREENSHOT_PATH


class MatchingBalls:

    BALLS_DISTANCE_RATIO = 30
    TUBES_DISTANCE_RATIO = 8
    RADIUS_RATIO = 50

    def __init__(self):
        self.__image = getImg(os.path.join(SCREENSHOT_PATH, 'screenshot.png'))
        self.__output = self.__image.copy()  # Used to display the result
        self.__blurred = cv.GaussianBlur(self.__image, (65, 65), 0)  # Used to find the color of the balls
        self.__tubeTemplates = []
        for file in os.listdir(SPRITE_PATH):
            if file.endswith('.png'):
                img = getImg(os.path.join(SPRITE_PATH, file))
                self.__tubeTemplates.append(img)
        #self.__first_template = getImg(os.path.join(SPRITE_PATH, 'tube.png'), 0)
        #self.__second_template = getImg(os.path.join(SPRITE_PATH, 'tall_tube.png'), 0)
        self.__hough_circles_method_name = 'cv.HOUGH_GRADIENT'
        self.__hough_circles_method = eval(self.__hough_circles_method_name)
        self.__match_template_method_name = 'cv.TM_CCOEFF_NORMED'
        self.__match_template_method = eval(self.__match_template_method_name)
        self.__ball_chart = BallsChart()

    def detect_balls(self):
        height = self.__image.shape[0]
        gray = cv.cvtColor(self.__image, cv.COLOR_BGR2GRAY)  # Used to find the balls

        circles = cv.HoughCircles(gray, self.__hough_circles_method, dp=1, minDist=int(height / MatchingBalls.BALLS_DISTANCE_RATIO),
                                  param1= 100, param2=15, minRadius=int(height / MatchingBalls.RADIUS_RATIO),
                                  maxRadius=int(height / MatchingBalls.RADIUS_RATIO + 10))

        # ensure at least some circles were found
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            balls = []
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                # get the color of pixel (x, y) form the blurred image
                color = np.array(self.__blurred[y, x])
                # print(f"({x}, {y}): {color}")
                # draw the circle
                cv.circle(self.__output, (x, y), r, (0, 255, 0), 2)
                cv.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                cv.circle(self.__blurred, (x, y), r, (0, 255, 0), 2)
                cv.circle(self.__blurred, (x, y), 6, (0, 0, 0), 1)
                cv.putText(self.__output, f"({x}, {y})", (x + 10, y), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                balls.append([x, y, color.tolist()])

            self.__ball_chart.setup_full_tubes(balls)

    def detect_empty_tube(self):
        for template in self.__tubeTemplates:
            match = self.__empty_tube(template)
            if match:
                break
        #match = self.__empty_tube(self.__first_template)
        #if not match:
        #    match = self.__empty_tube(self.__second_template)

        self.__show_result()
        self.__ball_chart.setup_empty_tubes(match)

    def __empty_tube(self, template):
        width = self.__image.shape[1]

        image_gray = cv.cvtColor(self.__image, cv.COLOR_BGR2GRAY)
        w, h = template.shape[::-1]
        res = cv.matchTemplate(image_gray, template, cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)
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
        resized_blurred = cv.cvtColor(cv.resize(self.__blurred, dim, interpolation=cv.INTER_AREA), cv.COLOR_BGR2RGB)
        result = np.concatenate((resized_input, resized_edges, resized_output, resized_blurred), axis=1)
        plt.figure(dpi=300)
        plt.imshow(result)
        plt.show()
        cv.waitKey(0)
