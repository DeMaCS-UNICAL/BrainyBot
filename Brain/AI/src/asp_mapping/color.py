from math import sqrt,atan2

from itertools import count
from languages.predicate import Predicate
import numpy as np
from scipy.spatial.distance import cdist
import cv2

class Color(Predicate):
    predicate_name = "color"

    __ids = count(1, 1)
    __colors= []
    __MAX_DISTANCE = 20
    __delta_e_distance = 3
    def reset():
        Color.__ids = count(1, 1)
        Color.__colors = []
        Color.__MAX_DISTANCE = 20
        Color.__delta_e_distance = 3
        

    def __init__(self, bgr=None):
        Predicate.__init__(self, [("id", int)])
        #self.__id = next(Color.__ids)
        self.__id = -1
        self.__bgr = bgr

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id
    
    def incr_id(self):
        self.__id+=1

    def decr_id(self):
        self.__id-=1

    def get_bgr(self) -> []:
        return self.__bgr

    def set_bgr(self, bgr: []):
        self.__bgr = bgr

    @staticmethod
    def is_less_than(color1,color2):
        if color1.__bgr[0]<color2.__bgr[0]:
            return True
        if color1.__bgr[0]-color2.__bgr[0]<10:
            if color1.__bgr[1]<color2.__bgr[1]:
                return True
            if color1.__bgr[1]-color2.__bgr[1]<10:
                if color1.__bgr[2]<color2.__bgr[2]:
                    return True
        return False

    @staticmethod
    def __euclidean_distance(color1, color2):
        return sqrt(pow(color1[0] - color2[0], 2) + pow(color1[1] - color2[1], 2) + pow(color1[2] - color2[2], 2))
    
    @staticmethod
    def delta_e_2000(color1, color2):
        # Converti i colori BGR in CIELAB
        color1_bgr = np.array([[color1]], dtype=np.uint8)
        color2_bgr = np.array([[color2]], dtype=np.uint8)
        color1_lab = cv2.cvtColor(color1_bgr, cv2.COLOR_BGR2LAB)[0][0]
        color2_lab = cv2.cvtColor(color2_bgr, cv2.COLOR_BGR2LAB)[0][0]
        
        # Usa cdist con il parametro 'euclidean' per calcolare Delta E 2000
        delta_e = cdist([color1_lab], [color2_lab], metric='euclidean')[0][0]
        return delta_e
    
    def sort_colors_by_lab(colors_bgr):
        def lab_to_angle(lab):
            a, b = lab[1], lab[2]
            return atan2(b, a)  # Calcola l'angolo in radianti

        
        # Ordina gli oggetti in base all'angolo nel piano a-b
        sorted_color_objects = sorted(colors_bgr, key=lambda obj: lab_to_angle(cv2.cvtColor(np.uint8([[obj.__bgr]]), cv2.COLOR_BGR2LAB)[0][0]))

        return sorted_color_objects

    @staticmethod
    def get_color(bgr: []):
        for color in Color.__colors:
            if Color.delta_e_2000(color.__bgr, bgr) < Color.__delta_e_distance:
                return color
        color = Color(bgr)
        Color.__colors.append(color)
        Color.__colors = Color.sort_colors_by_lab(Color.__colors)
        for i in range(len(Color.__colors)):
            Color.__colors[i].set_id(i+1 )
        return color
    
    @staticmethod
    def get_bgr_by_id(id):
        for color in Color.__colors:
            if color.__id==id:
                return color.__bgr

    
    def remove_except(colors_needed:list):
        for i in range(len(Color.__colors)):
            if Color.__colors[i] not in colors_needed:
                Color.__colors[i].set_id(-1)
                for j in range(i+1,len(Color.__colors)):
                    Color.__colors[j].decr_id()
        Color.__colors=[color for color in Color.__colors if (color.get_id()!=-1)]

