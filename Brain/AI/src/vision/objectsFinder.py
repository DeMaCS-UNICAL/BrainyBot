import os
import sys
import cv2
import numpy as np
import mahotas
import multiprocessing
from time import time

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


    def worker_process(self,id,dictionary,elements:list,regmax):
        for pair in elements:
            dictionary[pair[0]]=self.find_matches(self.__img_matrix,pair[1],regmax)
        #print(f"I'm done {id}")

        

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

    def find_all(self, elements_to_find:dict, request_regmax=True) -> dict:
        template_num=len(elements_to_find.keys())
        num_processes = min(multiprocessing.cpu_count(),template_num)
        template_per_process = template_num//num_processes
        count=0
        templates_for_process=[]
        for element in elements_to_find.keys():
            if count<template_per_process or len(templates_for_process)==num_processes:
                if count==0:
                    templates_for_process.append([])
                templates_for_process[-1].append((element,elements_to_find[element]))
                count+=1
                if count==template_per_process and len(templates_for_process)<num_processes:
                    count=0
                    
        processes = []
        
        with multiprocessing.Manager() as manager:
        # Create a shared dictionary
            shared_dict = manager.dict()
            for i in range(num_processes):
                #print(f"Starting process number {i}")
                process = multiprocessing.Process(target=self.worker_process, args=(i,shared_dict,templates_for_process[i],request_regmax))
                processes.append(process)
                process.start()

            for process in processes:
                process.join()

            #print("All processes have finished.")
            '''
            objects_found={}
            for element in elements_to_find.keys():
                #print(f"{element} ")
                objects_found[element] = self.find_matches(self.__img_matrix,elements_to_find[element],request_regmax)
            '''
            return dict(shared_dict)

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
