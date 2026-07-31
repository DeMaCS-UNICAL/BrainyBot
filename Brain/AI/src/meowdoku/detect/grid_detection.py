import os
import cv2
import sys 

import numpy as np

from matplotlib import pyplot as plt
from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.candy_crush.object_graph.constants import PX, PY, TYPE, ID
from AI.src.abstraction.abstraction import Abstraction
from AI.src.validation.validation import Validation
from AI.src.abstraction.objectsMatrix import ObjectMatrix
from AI.src.candy_crush.detect.constants import SPRITES,DISTANCE
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.candy_crush.constants import RED, YELLOW, PURPLE, GREEN, BLUE, WHITE, nameColor, ORANGE
from AI.src.vision.input_game_object import Rectangle, TemplateMatch, SimplifiedTemplateMatch
from AI.src.vision.output_game_object import OutputTemplateMatch

class MatchingMeowdoku: 
    def __init__(self, screenshot_path, debug = False, vision_validation=None, abstraction_validation=None, iteration=0, benchmark=False):
        self.__finder = ObjectsFinder(screenshot_path)
        self.__finder.saturate_img() # forzo la detection sull'immagine saturata
        self.screenshot = screenshot_path

        self.debug = debug,
        self.vision_validation=vision_validation,
        self.abstraction_validation=abstraction_validation,
        self.iteration=iteration,
        self.benchmark=benchmark,

        self.boxes, self.hierarchy, self.grid, self.cells = None, None, None, None

        self._vision()


    def _vision(self):
        self.__image = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot))
        self.boxes,self.hierarchy = self._detect_squares()
        self.grid = self.detect_grid()
        self.cells = self.read_cells()
        # self._print_boxes()

    # da risolvere questo ... 
    #def detect_grid(self):
    #    max_idx = 0
    #    max_area = 0
    #    for idx, contour in enumerate(self.boxes):
    #        area = cv2.contourArea(contour)
    #        if area > max_area:
    #            max_area = area
    #            max_idx = idx
    #    
    #
    #    return [idx for idx, box in enumerate(self.hierarchy) if box[3] == self.hierarchy[max_idx][2]]

    # rifatta dal sig. gemini spero sia buona ...
    def detect_grid(self):
        if not self.boxes or self.hierarchy is None:
            return []

        # Gestisce sia hierarchy 2D (N, 4) che 3D (1, N, 4) restituito da cv2.findContours
        hierarchy = self.hierarchy[0] if len(self.hierarchy.shape) == 3 else self.hierarchy

        # 1. Trova l'indice del contorno con area massima
        max_idx = 0
        max_area = 0
        for idx, contour in enumerate(self.boxes):
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                max_idx = idx

        # Funzione helper per recuperare tutti i figli diretti di un nodo
        def get_children(node_idx):
            children = []
            child_idx = hierarchy[node_idx][2]  # Index 2: First_Child
            while child_idx != -1:
                children.append(child_idx)
                child_idx = hierarchy[child_idx][0]  # Index 0: Next sibling
            return children

        # 2. Scendi nella gerarchia finché c'è solo un figlio (es. cornici esterne doppie)
        current_idx = max_idx
        while True:
            children = get_children(current_idx)

            # Se c'è esattamente un solo figlio, scendiamo al livello successivo
            if len(children) == 1:
                current_idx = children[0]
            else:
                # Appena ne troviamo più di uno (es. le celle della griglia) o zero, ci fermiamo
                break

        # 3. Restituisci la lista dei box trovati a quel livello
        return children if children else [current_idx]


    def read_cells(self):
        # mapping {id [unsinged] : color [tuple], cat [bool], sample_point [tuple], side_size [int]}
        mapping = {}
        for box_id in self.grid:
            color, sample_point, side_size = self.detect_color(box_id)
            cat = self._detect_cat(color, sample_point, side_size)
            mapping[box_id] = (color,cat, sample_point, side_size)
        

        return mapping

    def detect_color(self, box_id):
        # prendo un box ...
        clean_box = [self.boxes[box_id][idx][0] for idx in range(len(self.boxes[box_id]))]

        left_side = sorted(clean_box, key=lambda x : x[0])[:2]

        sample_point = (left_side[0][0] + 3, int((left_side[0][1] + left_side[1][1]) / 2))
        side_size = abs(left_side[0][1] - left_side[1][1])

        color = self.__image[sample_point[1],[sample_point[0]]][0][::-1] # BGR to RGB
        color = tuple(int(c) for c in color)
        return color, sample_point, side_size

    # deprecato     
    #def _count_child_boxes(self, box_id):
    #    # true if count of boxes that have this as a parent > 1
    #
    #    # devo esplorare in modo ricorsivo la gerarchia dei box per contare quanti box hanno come parent il box_id dato
    #    child = [box for box in range(len(self.hierarchy)) if self.hierarchy[box][3] == box_id]
    #    if not child:
    #        return 0
    #
    #    return len(child) + sum(self._count_child_boxes(c) for c in child)

    def _detect_cat(self, color, sample_point, side_size):
        for x_ofs in range(sample_point[0], int(sample_point[0] + side_size / 2)):
            if tuple(self.__image[sample_point[1],x_ofs]) != color[::-1]:
                return True
        return False

    def _detect_squares(self)->list:
        boxes, hierarchy = self.__finder.find(Rectangle(True))
        return boxes, hierarchy

    def _print_all(self):
        plt.title(f"meow")
        img = cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        #plt.ylim(h * 0.75, h * 0.3)
        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # _, img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        cv2.drawContours(img,self.boxes, -1, (255,0,0), 1)
    
        plt.imshow(img, cmap='gray')
        plt.draw()
        plt.waitforbuttonpress(0)


    def _print_boxes(self): 
        plt.title(f"meow")
        img = cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        #plt.ylim(h * 0.75, h * 0.3)

        for box_id in self.cells.keys():
            color, cat, source_point, _ = self.cells[box_id]

            cv2.drawContours(img,[self.boxes[box_id]], -1, (255,0,0) if cat else (0,0,0), 3)
            cv2.drawContours(img,[self.boxes[box_id]], -1, color, 1)
            cv2.putText(img, f"{box_id}", self.boxes[box_id][0][0] + [40,40], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(img, f"{source_point}", self.boxes[box_id][0][0] + [70,70], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)

        plt.imshow(img)
        plt.draw()
        plt.waitforbuttonpress(0)

    def get_box_source_point(self,id):
        return self.cells[id][2]

    def get_box_touch_point(self,id):
        source_point = self.cells[id][2]
        side_size = self.cells[id][3]
        return (source_point[0] + side_size // 2 + 20, source_point[1])