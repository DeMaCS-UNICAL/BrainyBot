from AI.src.vision.objectsFinder import ObjectsFinder
import cv2
from math import sqrt

class Matching2048:
    def __init__(self, screenshot_path, debug = False,validation=None,iteration=0):
        self.__image = cv2.imread(screenshot_path)
        self.__finder = ObjectsFinder(screenshot_path)
        self.__debug = debug
        self.__matrix = None
        self.__numbers_boxes = None
        self.__calculate_metadata()

    def get_image(self):
        return self.__image
    
    def set_image(self, screenshot_path, recalculate_metadata = False):
        self.__image = cv2.imread(screenshot_path)
        self.__finder = ObjectsFinder(screenshot_path)
        if recalculate_metadata:
            self.__calculate_metadata()

    def __calculate_metadata(self):
        boxes, hierarchy = self.__finder.find_boxes_and_hierarchy()
        matrix_index = self.__find_matrix(boxes, hierarchy)
        if matrix_index == None:
            return False
        self.__matrix = cv2.boundingRect(boxes[matrix_index])
        self.__numbers_boxes = self.__find_numbers_boxes(boxes, hierarchy, matrix_index)

    def get_numbers(self):
        for i in range(len(self.__numbers_boxes)):
            x, y, w, h = self.__numbers_boxes[i]
            elem = self.__finder.find_number(x, y, w, h)


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
        if self.__numbers_boxes != None:
            for box in self.__numbers_boxes:
                x, y, w, h = box
                number = self.__finder.find_number(x, y, w, h)
                if number == None:
                    numbers.append(0)
                else:
                    numbers.append(int(number))
        return numbers

    def __cut_image_to_matrix(self):
        x, y, w, h = self.__matrix
        return self.__image[y:y+h, x:x+w].copy()

    def get_output(self, i):
        output = self.__image.copy()
        numbers = []
        
        if self.__matrix != None:
            x, y, w, h = self.__matrix
            cv2.rectangle(output, (x, y), (x + w, y + h), (255, 0, 0), 2)
            if self.__numbers_boxes != None:
                for box in self.__numbers_boxes:
                    x, y, w, h = box
                    number = self.__finder.find_number(x, y, w, h)
                    if number == None:
                        numbers.append(0)
                    else:
                        numbers.append(number)
                    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(output, str(number) if number != None else "0" , (x+10, y+30), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.imwrite(f'output/output{i}.png', output)
        return numbers
    
    def isOver(self) -> bool:
        return False
        
