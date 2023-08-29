import os

import cv2 as cv
import mahotas
import numpy as np


class BallsDetection:

    def __init__(self, targetImage, BALLS_DISTANCE_RATIO=30,RADIUS_RATIO=50):
        self.BALLS_DISTANCE_RATIO =BALLS_DISTANCE_RATIO
        self.TUBES_DISTANCE_RATIO = TUBES_DISTANCE_RATIO
        self.RADIUS_RATIO = RADIUS_RATIO
        self.target = targetImage
        self.__blurred = cv.GaussianBlur(self.target, (65, 65), 0)
        self.__hough_circles_method_name = 'cv.HOUGH_GRADIENT'
        self.__hough_circles_method = eval(self.__hough_circles_method_name)

    def detect_balls(self):
        height = self.target.shape[0]
        gray = cv.cvtColor(self.target, cv.COLOR_BGR2GRAY)  # Used to find the balls

        circles = cv.HoughCircles(gray, self.__hough_circles_method, dp=1, minDist=int(height / self.BALLS_DISTANCE_RATIO),
                                  param1= 100, param2=15, minRadius=int(height / self.RADIUS_RATIO),
                                  maxRadius=int(height / self.RADIUS_RATIO + 10))
        circles = np.round(circles[0, :]).astype("int")
        colored_circles=[]
        for (x,y,r) in circles:
            color = self.__blurred[y, x]
            scalar_color = (int(color[0]), int(color[1]), int(color[2]))
            colored_circles.append((x,y,r,scalar_color))
        return colored_circles