import os
import sys
import cv2
import numpy as np
import mahotas
import multiprocessing
from time import time
from matplotlib import pyplot as plt

from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH

class ObjectsFinder:

    def __init__(self, screenshot, color=None, debug=False, threshold=0.8,validation=False ):
        #
        # Use Matrix2.png for testing
        #
        self.validation=validation
        self.__img_matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color) 
        self.__output = self.__img_matrix.copy()  
        self.__blurred = cv2.medianBlur(self.__img_matrix,5)  # Used to find the color of the balls
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=cv2.COLOR_BGR2GRAY)  # Used to find the balls
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
        #objects_found = list(zip(*loc[::-1]))
        #print(f"Found {len(objects_found)} matches")
        # Combine coordinates (x, y) with corresponding res values
        for pt in zip(*loc[::-1]):
            x, y = pt
            confidence = res[y, x]  # Extract the confidence value at the corresponding position
            objects_found.append((x, y, confidence))
        return objects_found

    def get_circle_shape(self):
        center = (300, 300)
        radius = 200
        # Generate points around the circle
        points = []
        for angle in range(0, 360, 1):
            x = int(center[0] + radius * np.cos(np.radians(angle)))
            y = int(center[1] + radius * np.sin(np.radians(angle)))
            points.append((x, y))
        # Convert points to a numpy array
        points = np.array(points)
        # Create a contour from the points
        return points.reshape((-1, 1, 2))

    def find_circles(self, min_radius,canny_threshold):
        circle_shape = self.get_circle_shape()
        gray = self.__gray
        # threshold
        #blurred_img = cv2.blur(gray,ksize=(5,5))
        canny = cv2.Canny(gray, canny_threshold,int(canny_threshold*3.5))
        contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        circles = [cnt for cnt in contours if cv2.matchShapes(cnt,circle_shape,1,0.0)<0.05]
        if not self.validation:
            canny = cv2.cvtColor(canny, cv2.COLOR_GRAY2RGB)
            canny2 = canny.copy()
            canny3 = canny.copy()
            cv2.drawContours(canny, contours, -1, (255, 0, 0), 1)
            plt.imshow(canny)
            plt.show()
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        balls = []
        if circles is not None:
            for circle in circles:
                (center),r = cv2.minEnclosingCircle(circle)
                if r<min_radius:
                    continue
                # get the color of pixel (x, y) form the blurred image
                x=int(center[0])
                y=int(center[1])
                r=int(r)
                color = np.array(self.__blurred[y,x])
                if not self.validation:
                    print(f"Found ball:({x}, {y}): {color}")
                    # draw the circle
                    cv2.circle(self.__img_matrix, (x, y), r, (0, 255, 0), 2)
                    #cv2.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                    #cv2.circle(self.__blurred, (x, y), r, (0, 255, 0), 2)
                    #cv2.circle(self.__blurred, (x, y), 6, (0, 0, 0), 1)
                    cv2.putText(self.__img_matrix, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                balls.append([x, y, r,color.tolist()])
            if not self.validation:
                plt.imshow(cv2.cvtColor(self.__img_matrix,cv2.COLOR_BGR2RGB))
                plt.show()
                cv2.waitKey(0)
        return balls
    
    def find_circles_old(self, balls_min_distance, balls_min_radius, balls_max_radius) -> list:
        gray = self.__gray.copy()  # Used to find the balls
        gray = cv2.medianBlur(gray, 5)
        gray = cv2.Canny(gray,1,150)
        gray = cv2.dilate(gray, None, iterations=1)
        if not self.validation:
            plt.imshow(gray, cmap="gray")
            plt.show()
            cv2.waitKey(0)
        circles = cv2.HoughCircles(gray, self.__hough_circles_method, dp=1, minDist=balls_min_distance,param1= 100, param2=15, minRadius=balls_min_radius,     maxRadius=balls_max_radius)
        balls = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                # get the color of pixel (x, y) form the blurred image
                color = np.array(self.__blurred[y, x])
                if not self.validation:
                    print(f"Found ball:({x}, {y}): {color}")
                    # draw the circle
                    cv2.circle(self.__img_matrix, (x, y), r, (0, 255, 0), 2)
                    #cv2.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                    #cv2.circle(self.__blurred, (x, y), r, (0, 255, 0), 2)
                    #cv2.circle(self.__blurred, (x, y), 6, (0, 0, 0), 1)
                    cv2.putText(self.__img_matrix, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                balls.append([x, y, r,color.tolist()])
            if not self.validation:
                plt.imshow(cv2.cvtColor(self.__img_matrix,cv2.COLOR_BGR2RGB))
                plt.show()
                cv2.waitKey(0)
        return balls

    
    def detect_container(self,template,proportion_tolerance=0,size_tolerance=0,rotate=False):

        # Convert to grayscale and apply edge detection
        tem_gray = template.copy()
        gray = self.__gray.copy()
        #edges = cv2.Canny(gray, 50, 150)
        ret, edges = cv2.threshold(gray, 127, 255, 0)
        #tem_edges = cv2.Canny(tem_gray, 50, 150)
        ret, tem_edges = cv2.threshold(tem_gray, 127, 255, 0)
        # Find contours
        tem_contours, _ = cv2.findContours(tem_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        tem_cnt = tem_contours[0]
        _,tem_axis,tem_a = cv2.fitEllipse(tem_cnt)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        containers = [cnt for cnt in contours if cv2.matchShapes(cnt,tem_cnt,3,0.0)<0.02]
        coordinates = []
        to_return=[]
        for i in range(len(containers)):
            (x,y),axis,cont_a = cv2.fitEllipse(containers[i])
            if not rotate and abs(tem_a+cont_a)%179>5: #the 2 contours are aligned
                    continue
            if proportion_tolerance!=0 and abs(axis[1]/axis[0]-tem_axis[1]/tem_axis[0])>tem_axis[1]/tem_axis[0]*proportion_tolerance:
                continue
            if size_tolerance!=0 and abs(axis[1]-tem_axis[1])>tem_axis[1]*size_tolerance:
                continue
            to_return.append(containers[i])
            coordinates.append((x,y))

        # Show the image
        #plt.figure(dpi=300)
        return to_return,coordinates

