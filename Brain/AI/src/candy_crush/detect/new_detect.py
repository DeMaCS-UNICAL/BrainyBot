import os
import cv2
import sys 

from matplotlib import pyplot as plt
from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.candy_crush.object_graph.constants import PX, PY, TYPE, ID
from AI.src.abstraction.abstraction import Abstraction
from AI.src.validation.validation import Validation
from AI.src.candy_crush.detect.constants import SPRITES
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.candy_crush.constants import RED, YELLOW, PURPLE, GREEN, BLUE, WHITE, nameColor, ORANGE


def draw(matrixCopy, row,column,offset,delta, color):
    x_start =  offset[0]+column*delta[0]
    y_start = offset[1]+row*delta[1]
    cv2.rectangle(matrixCopy, (x_start,y_start), (x_start+delta[0], y_start+delta[1]), color, 10)
    #cv2.putText(matrixCopy,f"({x_start},{y_start})",(x_start,y_start),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

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
    def __init__(self, screenshot,difference:(), debug=False,validation=None):
        #
        # Use Matrix2.png for testing
        #
        self.screenshot=screenshot
        self.debug=debug
        self.__difference = difference
        self.image = None
        self.__graph=None
        self.__matrix=None
        self.validation=validation

    def vision(self):
        finder = ObjectsFinder(self.screenshot,cv2.COLOR_BGR2RGB, threshold=0.78)
        self.image = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot),color_conversion=cv2.COLOR_BGR2RGB)
        if self.validation==None:
            plt.imshow( self.image)
            plt.title(f"Screenshot")
            plt.show()
            if not self.debug:
                plt.pause(0.1)
        return finder.find_all(SPRITES)
    
    def abstraction(self,vision_output):
        gridifier = Abstraction()
        #self.__graph = gridifier.ToGraph(vision_output,self.__difference)
        matrix,offset,delta=gridifier.ToMatrix(vision_output,self.__difference)
        '''
        for l in matrix:
            for l1 in l:
                print(l1,end=' ')
            print()
        '''
        number_per_type={}
        matrix_copy=self.image.copy()
        print(offset)
        print(delta)
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                #print(matrix[i][j],end=" ")
                if matrix[i][j] != None:
                    color = get_color(matrix[i][j])
                    draw(matrix_copy , i,j,offset,delta, color)
                    if not matrix[i][j] in number_per_type.keys():
                        number_per_type[matrix[i][j]] = 0
                    number_per_type[matrix[i][j]] = number_per_type[matrix[i][j]]+1
            #print()
        for type in number_per_type.keys():
            print(f"{type[0:-4]}:{number_per_type[type]}",file=sys.stderr,end='\t')
        print("",file=sys.stderr)
        if self.validation==None:
            plt.imshow(matrix_copy)
            plt.title(f"Matching")
            plt.show()
            if not self.debug: 
                plt.pause(0.5)
        return matrix
    
    def old_search(self) -> ObjectGraph:
        self.__graph = self.abstraction(self.vision())
        return self.__graph
    
    def search(self)->[]:
        self.__matrix= self.abstraction(self.vision())
        return self.__matrix

    def get_matrix(self):
        return self.image
