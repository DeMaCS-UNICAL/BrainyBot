import os
import cv2
from matplotlib import pyplot as plt
from math import ceil

from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.helpers import getImg
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.constants import SCREENSHOT_PATH
from AI.src.puzzle_bubble.constants import GRID_START_APPROXIMATION,GRID_END_APPROXIMATION,MAX_BUBBLES_PER_ROW,MAX_RADIUS_OFFSET


class MatchingBubblePuzzle:

    def __init__(self,screenshot_path,debug,validation):
        self.validation= validation
        self.debug=debug
        self.screenshot=screenshot_path
        self.__finder = ObjectsFinder(screenshot_path,debug=True)
        self.__matrix = None
    
    def vision(self):

        self.__image=getImg(os.path.join(SCREENSHOT_PATH,self.screenshot))

        if self.debug and self.validation==None:
            plt.imshow( cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB))
            plt.title(f"Screenshot")
            plt.show()

        min_radius= ((self.__image.shape[1] / MAX_BUBBLES_PER_ROW) // 2) - MAX_RADIUS_OFFSET

        return self.__finder.find_circles(min_radius,canny_threshold=20)
        
        #valori canny da rivedere

    def abstraction(self,vision_output):
        ExagonalMatrix = Abstraction()

        start_approximation = self.__image.shape[0] * GRID_START_APPROXIMATION
        end_approximation = self.__image.shape[0] * GRID_END_APPROXIMATION

        radius= round((self.__image.shape[1] / MAX_BUBBLES_PER_ROW) / 2,2)
        
        return ExagonalMatrix.ExagonalGridToMatrix(vision_output,(start_approximation,end_approximation),radius,(MAX_RADIUS_OFFSET,MAX_BUBBLES_PER_ROW))
        #Vedere qui invece come fare per passare ToExagonalMatrix

    def SearchGrid(self):

        self.__matrix = self.abstraction(self.vision())
        #return self.__matrix
        
        for i  in range(len(self.__matrix)):
            for j in range(len(self.__matrix[i])):
                if self.debug and not self.validation:
                    x=int(self.__matrix[i][j][0])
                    y=int(self.__matrix[i][j][1])
                    r=int(self.__matrix[i][j][2])
                    print(f"FOUND BUBBLE: {x} {y} {r}")
                    # draw the circle
                    cv2.circle(self.__image, (x, y), r, (0, 255, 0), 2)
                    cv2.putText(self.__image, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if self.debug and not self.validation:
            plt.imshow(cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB))
            plt.show()
            cv2.waitKey(0)

        #Da rimuovere

        ##################