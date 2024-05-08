import os
import cv2
import sys 

from matplotlib import pyplot as plt
from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.candy_crush.object_graph.constants import PX, PY, TYPE, ID
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.objectsMatrix import ObjectMatrix
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.candy_crush.constants import RED, YELLOW, PURPLE, GREEN, BLUE, WHITE, nameColor, ORANGE


def draw(matrixCopy, nodes, color):
    width, height = 110, 110
    cv2.rectangle(matrixCopy, (nodes[PX], nodes[PY]), (nodes[PX] + width, nodes[PY] + height), color, 10)
    cv2.putText(matrixCopy,f"{nodes[ID]}",(nodes[PX],nodes[PY]),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def get_color(strg) -> ():
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
    def __init__(self, screenshot,difference:(), debug=False):
        #
        # Use Matrix2.png for testing
        #
        self.screenshot=screenshot
        self.debug=debug
        self.__difference = difference
        self.__matrix = None
        self.__graph=None

    def vision(self):
        finder = ObjectsFinder(self.screenshot,cv2.COLOR_BGR2RGB, self.debug, threshold=0.78)
        self.__matrix = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot),color_conversion=cv2.COLOR_BGR2RGB)
        plt.imshow( self.__matrix)
        plt.title(f"Screenshot")
        plt.show()
        if not self.debug:
            plt.pause(0.1)
        return finder.find_all(SPRITES)
    
    def abstraction(self,vision_output):
        gridifier = Abstraction()
        #self.__graph = gridifier.ToGraph(vision_output,self.__difference)
        matrix_rep,offset,delta = gridifier.ToMatrix(vision_output,self.__difference)
        objectMatrix = ObjectMatrix(matrix_rep,offset,delta)

        number_per_type={}
        matrix_copy=self.__matrix.copy()
        '''
        for node in self.__graph.get_nodes():
            color = get_color(node[TYPE])
            draw(matrix_copy , node, color)
            if not node[TYPE] in number_per_type.keys():
                number_per_type[node[TYPE]] = 0
            number_per_type[node[TYPE]] = number_per_type[node[TYPE]]+1
        '''
        for row in objectMatrix.get_cells():
            for cell in row:
                value=cell.get_value()
                if value != None:
                    color = get_color(value)
                    draw(matrix_copy , (cell.x,cell.y,value,cell.get_id()), color)
                #if not value in number_per_type.keys():
                #    number_per_type[value] = 0
                #number_per_type[value] = number_per_type[value]+1
        #for type in number_per_type.keys():
         #   print(f"{type[0:-4]}:{number_per_type[type]}",file=sys.stderr,end='\t')
        #print("",file=sys.stderr)
        plt.imshow(matrix_copy)
        plt.title(f"Matching")
        plt.show()
        if not self.debug: 
            plt.pause(0.5)
        #return self.__graph
        return objectMatrix
    
    def search(self) -> ObjectMatrix:
        #self.__graph = self.abstraction(self.vision())
        #return self.__graph
        return self.abstraction(self.vision())

    def get_matrix(self):
        return self.__matrix
