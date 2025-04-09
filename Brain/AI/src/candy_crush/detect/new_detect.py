import os
import cv2
import sys 

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
from AI.src.vision.input_game_object import TemplateMatch, SimplifiedTemplateMatch
from AI.src.vision.output_game_object import OutputTemplateMatch

def draw(matrixCopy, center,id,width,height, color):
    top_left = (center[0] - width // 2, center[1] - height // 2)
    bottom_right = (center[0] + width // 2, center[1] + height // 2)

    cv2.rectangle(matrixCopy, top_left,bottom_right, color, 10)
    cv2.putText(matrixCopy,f"{id}",center,cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def get_color(strg) -> tuple:
    # print(strg)
    name = None
    for color in [RED, BLUE, YELLOW, GREEN, PURPLE, ORANGE]:
        if color in strg:
            name = color

    if "colourB" in strg:
        name = WHITE

    if name in nameColor:
        return nameColor[name]

    return nameColor[RED]

class MatchingCandy:
    def __init__(self, screenshot,difference:tuple, thresholds:dict, debug=False,validation=False, sprites=SPRITES):
        #
        # Use Matrix2.png for testing
        #
        self.screenshot=screenshot
        self.debug=debug
        #self.__difference = difference
        self.__distance = DISTANCE
        self.image = None
        self.__graph=None
        self.__matrix=None
        self.validation=validation
        self.threshold_dictionary=thresholds
        self.object_matrix=None
        self.first=True
        self.sprites=sprites

    def vision(self, grid_changed=True, benchmark=False):
        grid_changed=self.first
        self.first=False
        finder = ObjectsFinder(self.screenshot,color=cv2.COLOR_BGR2RGB, debug=self.debug, threshold=0.78,validation=self.validation)
        self.__matrix = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot),color_conversion=cv2.COLOR_BGR2RGB)
        if not benchmark:
            if  not self.validation:
                plt.imshow( self.__matrix)
                plt.title(f"Screenshot")
                plt.show()
                if not self.debug:
                    plt.pause(0.1)
        if grid_changed:
            to_return = finder.find(TemplateMatch(self.sprites,self.threshold_dictionary))

            return to_return
        else:
            print("Looking for existing matrix") if not benchmark else None
            return finder.find_from_existing_matrix(SimplifiedTemplateMatch(self.sprites,self.__distance),self.object_matrix)
    
    def abstraction(self,vision_output, benchmark=False):
        gridifier = Abstraction()
        #self.__graph = gridifier.ToGraph(vision_output,self.__difference)
        matrix_rep,offset,delta = gridifier.ToMatrix(vision_output,self.__distance)
        objectMatrix = ObjectMatrix(matrix_rep,offset,delta)

        number_per_type={}
        matrix_copy=self.__matrix.copy()
        width,heigth = objectMatrix.delta[0], objectMatrix.delta[1]
        for row in objectMatrix.get_cells():
            for cell in row:
                value=cell.get_value()
                if value != None:
                    color = get_color(value)
                    draw(matrix_copy , (cell.x,cell.y),cell.get_id(),width,heigth, color)
        if not benchmark:
            if not self.validation:
                plt.imshow(matrix_copy)
                plt.title(f"ABSTRACTION")
                plt.show()
                if not self.debug: 
                    plt.pause(0.5)
        #return self.__graph
        self.object_matrix=objectMatrix
        self.__distance=objectMatrix.delta
        return objectMatrix,matrix_copy
    
    def search(self, benchmark=False) -> tuple[list,ObjectMatrix]:
        #self.__graph = self.abstraction(self.vision())
        #return self.__graph
        template_matches_list = self.vision(False, benchmark)
        matrix,to_plot = self.abstraction(template_matches_list.copy(), benchmark)
        return template_matches_list,matrix,to_plot

    def get_matrix(self):
        return self.__matrix

