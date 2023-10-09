import os

import cv2 as cv
import mahotas
import numpy as np


class TemplateMatching:

    def __init__(self, targetImage, threshold, gray_scale= False, regmax= False):
        self.target = targetImage
        self.threshold = threshold
        self.__match_template_method_name = 'cv.TM_CCOEFF_NORMED'
        self.__match_template_method = eval(self.__match_template_method_name)
        if(gray_scale):
            self.target = cv.cvtColor(self.target, cv.COLOR_BGR2GRAY)
        self.regmax=regmax

    def match(self, template):
        res = cv.matchTemplate(self.target,template,self.__match_template_method)
        toFilter = res * mahotas.regmax(res) if self.regmax else res
        loc = np.where(toFilter >= self.threshold)

        return loc