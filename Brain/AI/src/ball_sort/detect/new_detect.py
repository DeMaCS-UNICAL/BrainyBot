import os

import re
import cv2
import numpy as np
from matplotlib import pyplot as plt
import sys 
from AI.src.ball_sort.constants import SPRITE_PATH,SRC_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.stack import Stack
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_sort.dlvsolution.dlvsolution import Ball,Color,Tube,On


class MatchingBalls:  #classe che si occupa di trovare le palle e i container

    BALLS_DISTANCE_RATIO = 30 #distanza minima tra le palle
    TUBES_DISTANCE_RATIO = 8 # distanza minima tra i container
    RADIUS_RATIO = 60 # rapporto tra il raggio della palla e l'altezza dell'immagine

    def __init__(self, screenshot_path, debug = False,validation=None,iteration=0):
        self.screenshot=screenshot_path
        self.debug=debug
        self.image = None
        self.__gray = None
        self.__output = None
        self.__ball_chart=None
        self.validation=validation
        self.__tubeTemplates = {}
        self.__balls=[]
        self.img_width = None
        self.canny_threshold,self.proportion_tolerance,self.size_tolerance = self.retrieve_config()
        self.canny_threshold = self.adjust_threshold(iteration)
        
        for file in os.listdir(SPRITE_PATH):
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                if not validation:
                    print(f"Found Tube sprite {fullname}")
                img = getImg(fullname,gray=True)
                self.__tubeTemplates[fullname]  = img

    def adjust_threshold(self,iteration):
        if iteration==0:
            return self.canny_threshold
        return self.canny_threshold+iteration*10
                
    def retrieve_config(self):
        f = open(os.path.join(SRC_PATH,"config"), "r")
        x=f.read()
        f.close()
        canny_threshold=int(re.search("CANNY_THRESHOLD=([^\n]+)", x,flags=re.M).group(1))
        proportion_tolerance=float(re.search("TUBE_PROPORTION_TOLERANCE=([^\n]+)", x,flags=re.M).group(1))
        size_tolerance=float(re.search("TUBE_SIZE_TOLERANCE=([^\n]+)", x,flags=re.M).group(1))
        return canny_threshold,proportion_tolerance,size_tolerance
        

    def get_balls_chart(self):
        vision_output=self.vision()
        if len(vision_output[1])==0:
            return None
        return self.abstraction(vision_output)

    def vision(self):
        
        self.finder = ObjectsFinder(self.screenshot,debug=self.debug, threshold=0.8,validation=self.validation)
        
        self.__image = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot))

        if self.debug and self.validation==None:
            plt.imshow( cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB))
            plt.title(f"Screenshot")
            plt.show()
            if not self.debug:
                plt.pause(0.1)

        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot),gray=True)
        self.__output = self.__image.copy()  # Used to display the result
        self.__ball_chart = ElementsStacks()
        self.img_width = self.__image.shape[1]
        self.__balls = self.detect_balls()
        template,containers,coordinates = self.detect_empty_tube()
        return template,containers,coordinates
            
    
    def abstraction(self,vision_output)->ElementsStacks:  #serve per associare le palle ai container
        stacker = Abstraction()
        
        empty_stacks,non_empty_stacks = stacker.assign_to_container_as_stack(self.__balls.copy(),vision_output[1],vision_output[2]) 
        matcher_width, matcher_height = vision_output[0].shape[::-1]
        self.__ball_chart.add_stacks(empty_stacks)
        # draw the empty tubes
        self.__ball_chart.add_stacks(non_empty_stacks)
        if self.validation==None:
            balls_count = 0
            for l in non_empty_stacks:
                balls_count+=len(l.get_elements())
            print("Found ",len(empty_stacks)," empty stacks;",len(non_empty_stacks),"non empty stacks;",balls_count,"balls")
            for p in empty_stacks:
                cv2.rectangle(self.__output, (int(p.get_x() - 10), int(p.get_y() - 30)), 
                            (int(p.get_x() + 10), int(p.get_y() + 30)), (0, 0, 255), 3)
            self.__show_result()

        return self.__ball_chart

    def detect_balls(self)->list:
        height = self.__image.shape[0]
        min_dist = int(height / MatchingBalls.BALLS_DISTANCE_RATIO)
        minRadius=int(height / MatchingBalls.RADIUS_RATIO)
        maxRadius=int(height / MatchingBalls.RADIUS_RATIO)
        self.balls = self.finder.find_circles(minRadius,self.canny_threshold)
        return self.balls
        #self.__ball_chart.setup_non_empty_stack(self.balls.copy())

    def detect_empty_tube(self)->(int,list):
        c=0
        for name in self.__tubeTemplates:
            if self.validation==None:
                print(f"Trying to detect empty tube {name}")
            #matches = self.finder.find_matches(cv2.cvtColor(self.__image, cv2.COLOR_RGB2GRAY),self.__tubeTemplates[name],False)
            #print(len(matches))
            #if len(matches) > 0:
            actual_matches,coordinates = self.finder.detect_container(self.__tubeTemplates[name],self.proportion_tolerance,self.size_tolerance)
            if len(actual_matches)>0:
                return self.__tubeTemplates[name],actual_matches,coordinates
        #self.__ball_chart.setup_empty_stack(match)
        return None,[],[]
        
    def Remove_False_Empty_Stack(self,full,empty, width, matcher_width):
        to_remove=[]
        for p in empty:
            for p1 in full:
                print(f"p:({p.get_x()},{p.get_y()}), p1:({p1.get_x()},{p1.get_y()})")
                if abs(p.get_x() - p1.get_x()) < (width/MatchingBalls.TUBES_DISTANCE_RATIO)-matcher_width/2:
                    print(f"{abs(p.get_x() - p1.get_x())}")
                    to_remove.append(p)
                    break
        for p in to_remove:
            empty.remove(p)
    
    def get_image(self):
        return self.__image

    def __show_result(self):
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'output.png'), self.__output)
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'blurred.png'), self.__blurred)
        # print detecting result
        width = int(self.__image.shape[1] * 0.3)
        height = int(self.__image.shape[0] * 0.3)
        dim = (width, height)
        img_copy=self.__output.copy()
        #cv.imwrite(os.path.join(SCREENSHOT_PATH, 'edges.png'), edges)
        for tube in self.__ball_chart.get_stacks():
            for (x, y, r,c) in tube.get_elements():
                    
                    # draw the circle
                    cv2.circle(img_copy, (x, y), r, (c[0],c[1],c[2]), 10)
                    cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
                    cv2.putText(img_copy, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        resized_input = cv2.cvtColor(cv2.resize(self.__image, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        #resized_edges = cv2.cvtColor(cv2.resize(edges, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized_output = cv2.cvtColor(cv2.resize(img_copy, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized_gray = cv2.cvtColor(cv2.resize(self.__gray, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        #resized_blurred = cv2.cvtColor(cv2.resize(self.__blurred, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        result = np.concatenate((resized_input, resized_gray,resized_output), axis=1)
        plt.imshow(result)
        plt.show()
        cv2.waitKey(0)

#### prendo il contorno del template che fa match, faccio i contorni dello screenshot e mi prendo solo i contorni uguali a quelli del template. Trovo le palle: per ogni palla controllo che i punti massimi lungo gli assi siano contenuti nei contorni: ogni contorno sarà un container, la palla verrà associata al container