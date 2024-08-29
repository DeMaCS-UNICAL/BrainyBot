import os
import cv2
import math
from matplotlib import pyplot as plt

from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.helpers import getImg
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.constants import SCREENSHOT_PATH
from AI.src.puzzle_bubble.constants import GRID_START_APPROXIMATION,GRID_END_APPROXIMATION,PLAYER_BUBBLE_END_APPROXIMATION,MAX_BUBBLES_PER_ROW
from AI.src.puzzle_bubble.detect.constants import BACKGROUND_COLOR

def distance_between_color(color1,color2, max_distance = 45):

    delta_r = color1[0] - color2[0]
    delta_g = color1[1] - color2[1]
    delta_b = color1[2] - color2[2]

    # Calculate euclidean distance between the two given colors
    return math.sqrt(pow(delta_r, 2) + pow(delta_g, 2) + pow(delta_b, 2)) > max_distance

class MatchingBubblePuzzle:

    def __init__(self,screenshot_path,debug = False):
        self.debug=debug
        self.screenshot=screenshot_path
        self.__exagonal_matrix = None
        self.__player_bubbles = None
        self.__radius = None
        self.__bubble_offset = None

    def convert_BGR2RGB(self,x,y):
        (blue, green, red) = self.__image[int(y),int(x)]
        rgb = [red,green,blue]

        return rgb
    
    def vision(self):
        finder = ObjectsFinder(self.screenshot,debug=self.debug)
        self.__image=getImg(os.path.join(SCREENSHOT_PATH,self.screenshot))

        if self.debug:
            plt.imshow( cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB))
            plt.title(f"Screenshot")
            plt.show()
        
        self.__radius= round((self.__image.shape[1] / MAX_BUBBLES_PER_ROW) / 2,2)
        self.__bubble_offset = round(self.__radius / 8)

        min_radius= (self.__radius) - self.__bubble_offset

        return finder.find_circles_blurred(min_radius,canny_threshold=10)

    def abstraction(self,vision_output):
        data_structures = Abstraction()

        #approximation of where the grid should be
        start_approximation = self.__image.shape[0] * GRID_START_APPROXIMATION
        end_approximation = self.__image.shape[0] * GRID_END_APPROXIMATION

        player_bubbles_end_approximation = self.__image.shape[0] * PLAYER_BUBBLE_END_APPROXIMATION

        #defining the distance between two rows on a flat-top exagonal grid implementation, source:
        # https://www.redblobgames.com/grids/hexagons/
        # in our example the exagonal grid we show as feature from both the flat-top and the point-top implementation
        
        distance_next_row = math.sqrt(3) * self.__radius
        
        approximations = (start_approximation,end_approximation,player_bubbles_end_approximation)
        grid_data = (self.__bubble_offset,MAX_BUBBLES_PER_ROW,distance_next_row)

        bubbles, player = data_structures.removing_false_matches(vision_output,self.__radius,approximations,grid_data)
        bubbles, player = self.convert_color_data_structure(bubbles,player)
        
        exagonal_matrix = data_structures.exagonal_grid_to_matrix(bubbles,self.__radius,grid_data)

        if(len(exagonal_matrix[0]) > 0):
            last_row_Y = exagonal_matrix[-1][0][1]
            extra_rows = int((end_approximation - last_row_Y) / distance_next_row) - 1

            #adds extra rows to avoid not getting rows only composed of special bubbles not detected by vision
            exagonal_matrix = data_structures.add_empty_rows_to_exagonal_grid(exagonal_matrix,extra_rows,self.__radius,grid_data)

        return exagonal_matrix,player

    def convert_color_data_structure(self,matrix,player):
        for bubble in matrix:
            bubble[3] = [bubble[3][2],bubble[3][1],bubble[3][0]]
        
        for bubble in player:
            bubble[3] = [bubble[3][2],bubble[3][1],bubble[3][0]]
        
        return matrix,player

    def find_special_bubbles_via_color(self,matrix):
        for row in range (len(matrix)):
            for bubble in matrix[row]:
                rgb = self.convert_BGR2RGB(bubble[0],bubble[1] + self.__radius/4)

                if(bubble[3] == [0,0,0] and distance_between_color(rgb,BACKGROUND_COLOR)):
                    bubble[3] = rgb
                    bubble[2] = self.__radius
    
    def remove_extra_empty_rows(self,matrix):
        for row in range(len(matrix)-1,0,-1):
            counter_empty = 0
            for bubble in matrix[row]:
                if(bubble[3] == [0,0,0]):
                    counter_empty +=1
            
            if(counter_empty == len(matrix[row])):
                pop = True
                if(row > 0):
                    for bubble in matrix[row-1]:
                        if(bubble[3] != [0,0,0]):
                            pop = False
                    
                    if pop:
                        matrix.pop()

    def SearchGrid(self):

        self.__exagonal_matrix, self.__player_bubbles = self.abstraction(self.vision())
        self.find_special_bubbles_via_color(self.__exagonal_matrix)
        self.remove_extra_empty_rows(self.__exagonal_matrix)

        #Debug purpose
        if self.debug:
            for i  in range(len(self.__exagonal_matrix)):
                plusFactor = 2

                if(len(self.__exagonal_matrix[i]) == MAX_BUBBLES_PER_ROW):
                    column = 0
                else :
                    column = 1

                for j in range(len(self.__exagonal_matrix[i])):
                    x=int(self.__exagonal_matrix[i][j][0])
                    y=int(self.__exagonal_matrix[i][j][1])
                    r=int(self.__exagonal_matrix[i][j][2])
                    c=self.__exagonal_matrix[i][j][3]
                    if(c != [0,0,0]) :
                        print(f"FOUND BUBBLE: {x} {y} {r} {c}")
                        cv2.circle(self.__image, (x, y), r, (0, 255, 0), 2)
                    else :
                        print(f"EMPTY BUBBLE SPOT : {x} {y}")
                        cv2.circle(self.__image, (x, y), int(r/2), (0, 255, 0), 2)
                    # draw the circle
                    cv2.putText(self.__image, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    #cv2.putText(self.__image, f"({column}, {i})", (x - 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                    column+=plusFactor
                
            for bubble in (self.__player_bubbles):
                x=int(bubble[0])
                y=int(bubble[1])
                r=int(bubble[2])
                c= bubble[3]
                print(f"FOUND PLAYER BUBBLE: {x} {y} {r} {c}")
                # draw the circle
                cv2.circle(self.__image, (x, y), r, (0, 0, 255), 2)
                cv2.putText(self.__image, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        

            plt.imshow(cv2.cvtColor(self.__image,cv2.COLOR_BGR2RGB))
            plt.show()
            cv2.waitKey(0)


        ##################

        return self.__exagonal_matrix,self.__player_bubbles
    
    def get_image_width(self):
        return self.__image.shape[1]

    def get_image_height(self):
        return self.__image.shape[0]
    
