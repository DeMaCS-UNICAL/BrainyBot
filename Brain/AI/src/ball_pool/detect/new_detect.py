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

    RAIUS_RATIO = 45
    BALLS_DISTANCE_RATIO = 10


    def __init__(self , screenshot_path, debug = False,validationField=None,iteration=0):
        self.screenshot=screenshot_path
        self.debug=debug
        self.image = None
        self.__gray = None
        self.__output = None
        self.__ball_chart=None
        self.validationField=validationField
        self.__myTurn = None
        self.__balls = []
        self.__balls_pocketed = []
        self.img_width = None
        self.canny_threshold,self.proportion_tolerance,self.size_tolerance = self.retrieve_config()
        self.canny_threshold = self.adjust_threshold(iteration)
        
        for file in os.listdir(SPRITE_PATH): # indica la cartella in cui cercare i file
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                if not validationField: # se non è in modalità di validazione
                    print(f"Found field sprite {fullname} (testingg)") # stampa il nome del file
                img = getImg(fullname,gray=True)
            

    def vision(self):

        self.finder = ObjectsFinder(self.screenshot, debug=self.debug, threshold=0.8, validation=self.validationField)

        self.__image= getImg(os.path.join(SCREENSHOT_PATH,self.screenshot))

        if self.debug and self.validationField == None:
            plt.imshow(cv2.cvtColor(self.__image, cv2.COLOR_BGR2RGB)) #converte l'immagine in RGB
            plt.title(f"Screenshot")
            plt.show()
            if not self.debug:
                plt.pause(0.1)
    
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH,self.screenshot),gray=True)
        self.output = self.__gray.copy()
        self.ball_chart = ElementsStacks()
        self.image_width = self.__gray.shape[1]
        self.__balls = self.detect_balls()
        #templates, containers, cordinates = self.detect
        pass

    def detect_myPocketedBalls(self):
        height = self.image.shape[0] # altezza dell'immagine
        min_radius = int((height / self.RAIUS_RATIO) * 1.3) # raggio minimo delle palle
        self.__balls_pocketed = self.finder.find_circles(min_radius, self.canny_threshold)
        return self.__balls_pocketed



    def get_balls_chart(self):
        pass

    def detect_balls(self):
        height = self.image.shape[0] # altezza dell'immagine
        min_dist = int(height / self.BALLS_DISTANCE_RATIO) # distanza minima tra le palle basato sull'altezza dell'immagine
        min_radius = int(height / self.RAIUS_RATIO) # raggio minimo delle palle
        max_radius = int(height / self.RAIUS_RATIO)
        self.balls = self.finder.find_circles(min_radius, self.canny_threshold)
        return self.balls

            

    

#### prendo il contorno del template che fa match, faccio i contorni dello screenshot e mi prendo solo i contorni uguali a quelli del template. Trovo le palle: per ogni palla controllo che i punti massimi lungo gli assi siano contenuti nei contorni: ogni contorno sarà un container, la palla verrà associata al container