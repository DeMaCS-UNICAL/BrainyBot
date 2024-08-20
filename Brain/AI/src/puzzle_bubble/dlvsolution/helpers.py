import os
import re
import math

from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from AI.src.constants import DLV_PATH
from AI.src.puzzle_bubble.constants import MAX_BUBBLES_PER_ROW,GRID_START_APPROXIMATION
from AI.src.puzzle_bubble.detect.constants import BUBBLES_COLORS

from languages.predicate import Predicate

from AI.src.puzzle_bubble.detect.new_detect import distance_between_color

##add all classes needed by EMBASP

#probably two other classes will be needed,
# Angle, defined by the python function that calculate where the bubble will hit after the first angle
# Move, to define the move chosen by the agent

EMPTY_SPOT_TYPE = "Empty"
DEFAULT_TYPE = "Standard"

'''
class BUBBLE_INFO:

    def __init__(self, exagonal_grid = None, matcher = None, player_bubble = None):
        self.start_bubble_y = exagonal_grid[0][0][1]
        self.bubble_radius = exagonal_grid[0][0][2]
        self.image_width = matcher.get_image_width()
        self.image_height = matcher.get_image_height()
        self.player_bubble_x = player_bubble[0][0]
        self.player_bubble_y = player_bubble[0][1]
        self.exagonal_grid = exagonal_grid
    
    def conversion_doubleCoords2Pixels(self,x,y):

        if(x % 2 == 0): #MAX_BUBBLES_ROW
            position = x/ 2
            pixel_current_x = self.bubble_radius + ((2*self.bubble_radius) * position)
        else: #MAX_BUBBLES_ROW - 1
            position = int(x/2)
            pixel_current_x = (self.bubble_radius * 2) + ((2*self.bubble_radius) * position)
        
        pixel_current_y = self.start_bubble_y + ((math.sqrt(3) * self.bubble_radius) * y)

        return (round(pixel_current_x),round(pixel_current_y))

    def path_to_position(self,x,y):

        currentPosY = self.player_bubble_y + 3 * self.bubble_radius

        for angle in range(20,160):
            currentPosX = (self.player_bubble_x + ((self.player_bubble_y - currentPosY) / math.tan(math.radians(angle))))
            stop = False
            while(not stop):
                #esce dal while non appena trova qualcosa per cui si bloccata, di solito se va a contatto con una bolla della griglia
                for row in range(len(self.exagonal_grid)):
                    for bubble in self.exagonal_grid[row]:
                        if( currentPosX >= bubble[0] - self.bubble_radius and  currentPosX <= bubble[0] + self.bubble_radius):
                            if( currentPosY >= bubble[1] - self.bubble_radius and currentPosY <= bubble[1] + self.bubble_radius):
                                stop = True
                                #decides which neighbour it will occupy


                #checks whether it has to change direction due to a rebound

                if(currentPosX <= 0):
                    #reflection

                elif(currentPosX >= self.image_width):
                    #reflection
                
                elif(currentPosY <= self.image_height * GRID_START_APPROXIMATION):
                    #reflection

                currentPosX += 1
                currentPosY += 1
            
            if(currentPosX <= x - self.bubble_radius and currentPosX >= x + self.bubble_radius):
                if(currentPosY <= y - self.bubble_radius and currentPosY >= y + self.bubble_radius):
                    return angle
        
        return 0
'''
    
class CoordSystem:

    def __init__(self, row=None,col=None):
        self.__row = row
        self.__col = col

    def get_row(self):
        return self.__row
    def get_col(self):
        return self.__col
    
    def set_row(self,row):
        self.__row = row
    def set_col(self,col):
        self.__col = col
    
    def __str__(self) -> str:
        return f"({self.__row}, {self.__col})\n"

class Bubble_Type:

    def __init__(self, type = None):
        self.__type = type
    
    def get_type(self):
        return self.__type
    
    def set_type(self,type):
        self.__type = type
    
    def __str__(self):
        return f"({self.__type})\n"
    
class Bubble_color:

    def __init__(self,color = None):
        self.__color = color
    
    def get_color(self):
        return self.__color

    def set_color(self,color):
        self.__color = color
    
    def __str__(self):
        return f"({self.__color})\n"
    
class Path(Predicate,CoordSystem):

    predicate_name="Path"

    def __init__(self,angle = None,row = None, col = None):
        Predicate.__init__(self,[("angle",int), ("row",int), ("col",int)])
        CoordSystem.__init__(self,row,col)
        self.__angle = angle

    def get_angle(self):
        return self.__angle

    def set_angle(self, angle):
        self.__angle = angle
    
    def __str__(self):
        return f"({self.__angle}, {CoordSystem.get_row(self)}, {CoordSystem.get_row(self)})\n"
    

    
class Move(Predicate,CoordSystem):

    predicate_name="Move"

    def __init__(self, index=None, angle = None, row=None, col=None):
        Predicate.__init__(self, [("index", int), ("angle", int), ("row",int), ("col",int)])
        CoordSystem.__init__(self,row,col)
        self.__index = index
        self.__angle = angle

    def get_index(self):
        return self.__index

    def set_index(self,index):
        self.__index = index
    
    def get_angle(self):
        return self.__angle

    def set_angle(self, angle):
        self.__angle = angle
    
    def __str__(self):
        return f"({self.__index}, {self.__angle}, {CoordSystem.get_row(self)}, {CoordSystem.get_col(self)})\n"
    
class EmptySpot(Predicate,CoordSystem):

    predicate_name = "Empty"

    def __init__(self, row=None,col=None):
        Predicate.__init__(self, [("row",int), ("col",int)])
        CoordSystem.__init__(self,row,col)

    def __str__(self):
        return f"empty({CoordSystem.get_row(self)}, {CoordSystem.get_col(self)}) \n"

class Bubble(Predicate,Bubble_Type,Bubble_color,CoordSystem):

    predicate_name = "Bubble"

    def __init__(self, row=None, col=None, color = None ,type = None):
        Predicate.__init__(self, [("row", int), ("col", int),("color",str),("type",str)])
        Bubble_Type.__init__(self,type)
        Bubble_color.__init__(self,color)
        CoordSystem.__init__(self,row,col)
    
    def __str__(self):
        return f"bubble({CoordSystem.get_row(self)}, {CoordSystem.get_col(self)}, {Bubble_Type.get_type(self)}, {Bubble_color.get_color(self)}) \n"

class PlayerBubble(Predicate,Bubble_color):
    
    predicate_name = "PlayerBubble"

    def __init__(self,index = None, color = None):
        Predicate.__init__(self, [("index", int),("color",str)])
        Bubble_color.__init__(self,color)
        self.__index = index

    def get_index(self):
        return self.__index

    def set_index(self,index):
        self.__index = index
    
    def __str__(self):
        return f"playerbubble({self.__index}, {Bubble_color.get_color(self)}) \n"

def chooseDLVSystem() -> DesktopHandler:
    try:
        if os.name == 'nt':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
        elif os.uname().sysname == 'Darwin':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
        else:
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux")))
    except Exception as e:
        print(e)

def get_input_dlv_grid(exagonal_grid):
    input_grid = []

    for i in range(len(exagonal_grid)):
        plusFactor = 2

        if(len(exagonal_grid[i]) == MAX_BUBBLES_PER_ROW):
            column = 0
        else :
            column = 1
            
        for j in range(len(exagonal_grid[i])):
            bubble_info = get_bubble_spot_type(exagonal_grid[i][j][3])
            pattern = r"^([^_]+)_([^_]+)$"
            search_match = re.match(pattern,bubble_info.lower())

            bubble_type = DEFAULT_TYPE
            bubble_color = bubble_info

            if(search_match):
                bubble_type = search_match.group(1)
                bubble_color = search_match.group(2)

            if(bubble_color == EMPTY_SPOT_TYPE):
                input_grid.append(EmptySpot(column,i))
            else:
                input_grid.append(Bubble(column,i,bubble_color.lower(),bubble_type.lower()))
            
            column+=plusFactor

    return input_grid

def get_input_dlv_player(player_bubbles):
    input_player = []
    for i in range(len(player_bubbles)):
        bubble_type = get_bubble_spot_type(player_bubbles[i][3])
        input_player.append(PlayerBubble(i,bubble_type.lower()))
    
    return input_player


def get_bubble_spot_type(bubble_color):
    for key in BUBBLES_COLORS.keys():
        if(not distance_between_color(bubble_color,BUBBLES_COLORS[key])):
            return key
    
    return EMPTY_SPOT_TYPE

#TODO: define functions for getting the angle of the path to reach the x,y value

