import os
import sys
import cv2
import numpy as np
import mahotas
import pytesseract as ts

from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
class ObjectsFinder:

    def __init__(self, screenshot, color=None, debug=False, threshold=0.8 ):
        #
        # Use Matrix2.png for testing
        #
        self.__img_matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=color) 
        self.__output = self.__img_matrix.copy()  
        self.__blurred = cv2.GaussianBlur(self.__img_matrix, (65, 65), 0)  # Used to find the color of the balls
        self.__gray = cv2.cvtColor(self.__img_matrix, cv2.COLOR_BGR2GRAY)  # Used to find the balls
        self.__generic_object_methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__generic_object_method = eval(self.__generic_object_methodName)
        self.__threshold=threshold
        #self.__graph = CandyGraph(difference)
        
        self.__hough_circles_method_name = 'cv2.HOUGH_GRADIENT'
        self.__hough_circles_method = eval(self.__hough_circles_method_name)

    def find_one_among(self,  elements_to_find:{}, request_regmax=True) -> list:
        objects_found=[]
        for element in elements_to_find.keys():
            objects_found = self.find_matches(self.__img_matrix,elements_to_find[element],request_regmax)
            if len(objects_found)>0:
                break
        return objects_found

    def find_one_among_gray_scale(self, elements_to_find:{}, request_regmax:True)->list:
        image_gray = cv2.cvtColor(self.__img_matrix, cv2.COLOR_BGR2GRAY)
        objects_found = self.find_one_among(image_gray,elements_to_find,request_regmax)
        return objects_found

    def find_all(self, elements_to_find:{}, request_regmax=True) -> dict:
        objects_found={}
        for element in elements_to_find.keys():
            #print(f"{element} ")
            objects_found[element] = self.find_matches(self.__img_matrix,elements_to_find[element],request_regmax)
        return objects_found

    def find_all_gray_scale(self, elements_to_find:{}, request_regmax:True)->dict:
        image_gray = cv2.cvtColor(self.__img_matrix, cv2.COLOR_BGR2GRAY)
        objects_found = self.find_all(image_gray,elements_to_find,request_regmax)
        return objects_found

    def find_matches(self, image, element_to_find, request_regmax=True) -> list:
        
        objects_found=[]
        # execute template match
        res = cv2.matchTemplate(image, element_to_find, self.__generic_object_method)
        # find regional maxElem
        if request_regmax:
            regMax = mahotas.regmax(res)
            res = res * regMax
        # modify this to change the algorithm precision
        loc = np.where(res >= self.__threshold)
        objects_found = list(zip(*loc[::-1]))
        #print(f"Found {len(objects_found)} matches")
        return objects_found

    def find_circles(self, balls_min_distance, balls_min_radius, balls_max_radius) -> list:  
        gray = cv2.cvtColor(self.__img_matrix, cv2.COLOR_BGR2GRAY)  # Used to find the balls
        circles = cv2.HoughCircles(gray, self.__hough_circles_method, dp=1, minDist=balls_min_distance,
                                  param1= 100, param2=15, minRadius=balls_min_radius,
                                  maxRadius=balls_max_radius)
        balls = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                # get the color of pixel (x, y) form the blurred image
                color = np.array(self.__blurred[y, x])
                print(f"Found ball:({x}, {y}): {color}")
                '''
                # draw the circle
                cv2.circle(self.__output, (x, y), r, (0, 255, 0), 2)
                cv2.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                cv2.circle(self.__blurred, (x, y), r, (0, 255, 0), 2)
                cv2.circle(self.__blurred, (x, y), 6, (0, 0, 0), 1)
                cv2.putText(self.__output, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                '''
                balls.append([x, y, r,color.tolist()])
        return balls
            
    def find_boxes(self) -> list:
        contour = cv2.Canny(self.__img_matrix, 25, 80)
        contour = cv2.dilate(contour, None, iterations=1)
        contours, _ = cv2.findContours(contour, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        boxes = []
        for i in range(len(contours)):
            per = cv2.arcLength(contours[i], True)
            epsilon = 0.05 * per
            approx = cv2.approxPolyDP(contours[i], epsilon, True)
            
            # if the contour is not a rettangle or if it is too small, ignore it
            if len(approx) != 4 or cv2.isContourConvex(approx) == False or cv2.contourArea(approx) < 3000:
                continue
            x, y, w, h = cv2.boundingRect(approx)
            boxes.append((x, y, w, h))
        return boxes
    
    def find_boxes_and_hierarchy(self):
        mat_contour = np.zeros((self.__img_matrix.shape[0], self.__img_matrix.shape[1]), dtype=np.uint8)
        boxes = self.find_boxes()
        for box in boxes:
            x, y, w, h = box
            cv2.rectangle(mat_contour, (x, y), (x + w, y + h), 255, thickness=1, lineType=cv2.LINE_AA)
        boxes, hierarchy = cv2.findContours(mat_contour, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return boxes, hierarchy[0]

    def find_text(self, x, y, w, h) -> str:
        img = self.__img_matrix[y:y+h, x:x+w].copy()
        elem = ts.image_to_string(img, config='--psm 8 --oem 3') 
        return elem if elem != '' else None

    def find_number(self, x, y, w, h) -> int:
        img = self.__img_matrix[y:y+h, x:x+w].copy()
        # Upscale the image to improve the OCR if the image is too small
        if img.shape[0] < 150 or img.shape[1] < 150:
            img = cv2.resize(img, (round(img.shape[1]*1.5), round(img.shape[0]*1.5)))
        elem = ts.image_to_string(img, config='--psm 6 --oem 1 -c tessedit_char_whitelist=0123456789')
        if elem == '':
            elem = ts.image_to_string(img, config='--psm 7 --oem 1 -c tessedit_char_whitelist=0123456789')
        try:
            return int(elem)
        except:
            return None
    
    def find_text_from_dictionary(self, x, y, w, h, dictionary_path) -> str:
        img = self.__img_matrix[y:y+h, x:x+w].copy()
        elem = ts.image_to_string(img, config='--psm 8 --oem 3 --user-words {}'.format(dictionary_path))
        return elem if elem != '' else None

    def find_text_from_regex(self, x, y, w, h, regex) -> str:
        img = self.__img_matrix[y:y+h, x:x+w].copy()
        elem = ts.image_to_string(img, config='--psm 8 --oem 3')
        if regex.match(elem):
            return elem
        else:
            return None        
