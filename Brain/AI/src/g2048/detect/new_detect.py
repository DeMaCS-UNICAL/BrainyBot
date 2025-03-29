from AI.src.vision.objectsFinder import ObjectsFinder
import cv2
import numpy as np
from math import sqrt
from AI.src.vision.input_game_object import Rectangle,TextRectangle, OutputRectangle

class Matching2048:
    def __init__(self, screenshot_path, debug = False,validation=None,iteration=0, calculate_metadata = True):
        self.__finder = ObjectsFinder(screenshot_path)
        self.__debug = debug
        self.__matrix = None
        self.__numbers_boxes = None
        self.__blank_box_color = None
        if calculate_metadata:
            self.__calculate_metadata()
    
    def get_image_width(self):
        return self.__finder.get_image_width()
    
    def get_image_height(self):
        return self.__finder.get_image_height()
    
    def set_image(self, screenshot_path, recalculate_metadata = False):
        self.__finder = ObjectsFinder(screenshot_path)
        if recalculate_metadata:
            self.__calculate_metadata()

    def __calculate_metadata(self):
        boxes, hierarchy = self.__finder.find(Rectangle(True))
        matrix_index = self.__find_matrix(boxes, hierarchy)
        if matrix_index == None:
            return False
        self.__matrix = cv2.boundingRect(boxes[matrix_index])
        self.__numbers_boxes = self.__find_numbers_boxes(boxes, hierarchy, matrix_index)

    def get_numbers(self):
        for i in range(len(self.__numbers_boxes)):
            x, y, w, h = self.__numbers_boxes[i]
            elem = self.__finder.find(TextRectangle(OutputRectangle(x,y,w,h),numeric=True))


    def __find_matrix(self, boxes, hierarchy):
        dictionary = {}
        for h in hierarchy:
            if h[3] != -1:
                if h[3] in dictionary:
                    dictionary[h[3]] += 1
                else:
                    dictionary[h[3]] = 1
        possibleMatrix = []
        for key in dictionary:
            if sqrt(dictionary[key]).is_integer() and dictionary[key] > 3:
                possibleMatrix.append(key)
        if len(possibleMatrix) == 0:
            return None
        max = 0
        index = 0
        for key in possibleMatrix:
            if dictionary[key] > max:
                max = dictionary[key]
                index = key
        return index
    
    def __find_numbers_boxes(self, boxes, hierarchy, matrix_index):
        numbers_boxes = []
        for i in range(len(hierarchy)):
            if hierarchy[i][3] == matrix_index:
                numbers_boxes.append(cv2.boundingRect(boxes[i]))
        ordered = sorted(numbers_boxes, key=lambda x: x[0] * 10 + x[1] * 100)
        return ordered
    
    def find_numbers(self):
        numbers = []
        if self.__numbers_boxes == None:
            self.__calculate_metadata()
        for box in self.__numbers_boxes:
            x, y, w, h = box
            number = self.__finder.find(TextRectangle(OutputRectangle(x,y,w,h),numeric=True))
            if number == None:
                numbers.append(0)
            else:
                numbers.append(int(number))
        return numbers

    
    def find_numbers_with_cache(self, cache, only_first=True):
        numbers = cache
        for i in range(len(numbers)):
            if numbers[i] == 0:
                x, y, w, h = self.__numbers_boxes[i]
                if np.array_equal(self.__finder.get_image()[y+h//2, x+w//2], self.__blank_box_color):
                    continue
                number = self.__finder.find(TextRectangle(OutputRectangle(x,y,w,h),numeric=True))
                if number != None:
                    numbers[i] = int(number)
                    if only_first:
                        return numbers
        return numbers