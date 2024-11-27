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


class MatchingBalls:

    RAIUS_RATIO = 50
    BALLS_DISTANCE_RATIO = 15


    def __init__(self , screenshot_path, debug = False,validationField=None,iteration=0):
        self.screenshot = screenshot_path
        self.debug = debug
        self.image = None
        self.__gray = None
        self.__output = None
        self.validationField = validationField
        self.__myTurn = None
        self.__balls = []
        self.__balls_pocketed = []
        self.img_width = None
        self.canny_threshold,self.proportion_tolerance,self.size_tolerance = self.retrieve_config()
        self.canny_threshold = self.adjust_threshold(iteration)
        
        '''
        for file in os.listdir(SPRITE_PATH): # indica la cartella in cui cercare i file
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                if not validationField: # se non è in modalità di validazione
                    print(f"Found field sprite {fullname} (testingg)") # stampa il nome del file
                img = getImg(fullname,gray=True)
        '''
    def retrieve_config(self): #legge il file di configurazione dal file config
        f = open(os.path.join(SRC_PATH,"config"), "r")
        x = f.read()
        f.close()
        canny_threshold = int(re.search("CANNY_THRESHOLD=([^\n]+)", x,flags=re.M).group(1)) #canny è un algoritmo di edge detection
        return canny_threshold, None, None
    
    def adjust_threshold(self,iteration):
        if iteration==0:
            return self.canny_threshold
        return self.canny_threshold+iteration*10

    def detect_balls(self) -> list: #chiamato da vision per identificare le palle nell'immagine usando rilevamento di cerchi
        height = self.image.shape[0] 
        min_dist = int(height / self.BALLS_DISTANCE_RATIO) # distanza minima tra le palle basato sull'altezza dell'immagine
        min_radius = int(height / self.RAIUS_RATIO) # raggio minimo delle palle
        max_radius = int(height / self.RAIUS_RATIO)
        self.balls = self.finder.find_circles(min_radius, self.canny_threshold)
        return self.balls
    

    def vision(self): #elabora l'immagine e restituisce le palle 
        self.finder = ObjectsFinder(self.screenshot, debug=self.debug, threshold=0.8, validation=self.validationField)
        self.__image= getImg(os.path.join(SCREENSHOT_PATH,self.screenshot))
        if self.debug:
            plt.imshow(cv2.cvtColor(self.__image, cv2.COLOR_BGR2RGB))
            plt.title(f"Screenshot")
            plt.show()

        self.__gray = getImg(os.path.join(SCREENSHOT_PATH,self.screenshot),gray=True)
        self.__output = self.__image.copy()
        #self.img_width = self.__image.shape[1]
        self.__balls = self.detect_balls()

        return self.__balls


    def abstraction(self, vision_output):#converte l'output della visione in un formato strutturato
        ball_chart = []
        for ball in self.__balls:
            ball_chart.append({"x": ball[0], "y": ball[1], "r": ball[2]})
        return ball_chart

    def __show_result(self):
        width = int(self.__image.shape[1] * 0.3)
        height = int(self.__image.shape[0] * 0.3)
        dim = (width, height)
        img_copy = self.__output.copy()
        for(x,y,r) in self.__balls:
            cv2.circle(img_copy, (x,y), r, (255,0,0), 3)
            cv2.circle(img_copy, (x,y), 6, (0,0,0), -1)
            cv2.putText(img_copy, f"({x},{y})", (x+10,y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), -1)
        
        resized_output = cv2.resize(img_copy, dim, interpolation = cv2.INTER_AREA)
        plt.imshow(cv2.cvtColor(resized_output, cv2.COLOR_BGR2RGB))
        plt.show()


    def detect_myPocketedBalls(self):
        height = self.image.shape[0] # altezza dell'immagine
        min_radius = int((height / self.RAIUS_RATIO) * 1.3) # raggio minimo delle palle
        self.balls_pocketed = self.finder.find_circles(min_radius, self.canny_threshold)
        return self.__balls_pocketed

    def detect_table_and_pockets(self):
        ...


    def get_balls_chart(self):
        vision_output = self.vision()
        if len(vision_output[1]) == 0:
            return None
        return self.abstraction(vision_output)
    

#### prendo il contorno del template che fa match, faccio i contorni dello screenshot e mi prendo solo i contorni uguali a quelli del template. Trovo le palle: per ogni palla controllo che i punti massimi lungo gli assi siano contenuti nei contorni: ogni contorno sarà un container, la palla verrà associata al container