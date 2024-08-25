import os
import re
import math

from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from AI.src.constants import DLV_PATH
from AI.src.puzzle_bubble.constants import MAX_BUBBLES_PER_ROW
from AI.src.puzzle_bubble.dlvsolution.constants import ANGLE_APPROX
from AI.src.puzzle_bubble.detect.constants import BUBBLES_COLORS

from languages.predicate import Predicate

from AI.src.puzzle_bubble.detect.new_detect import distance_between_color

##add all classes needed by EMBASP

#probably two other classes will be needed,
# Angle, defined by the python function that calculate where the bubble will hit after the first angle
# Move, to define the move chosen by the agent

EMPTY_SPOT_TYPE = "Empty"
DEFAULT_TYPE = "Standard"
    
class CoordSystem:

    def __init__(self, col=None, row=None):
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
        return f"({self.__col}, {self.__row})\n"

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

    def __init__(self,col = None, row = None, angle = None):
        Predicate.__init__(self,[("col",int), ("row",int), ("angle")])
        CoordSystem.__init__(self,col,row)
        self.__angle = angle

    def get_angle(self):
        return self.__angle

    def set_angle(self, angle):
        self.__angle = angle
    
    def __str__(self):
        return f"path({self.__angle}, {CoordSystem.get_col(self)}, {CoordSystem.get_row(self)})\n"
    

    
class Move(Predicate,CoordSystem):

    predicate_name="Move"

    def __init__(self, index=None, angle = None, col=None, row=None):
        Predicate.__init__(self, [("index", int), ("angle"), ("col",int), ("row",int)])
        CoordSystem.__init__(self,col,row)
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
        return f"({self.__index}, {self.__angle}, {CoordSystem.get_col(self)}, {CoordSystem.get_row(self)})\n"
    
class EmptySpot(Predicate,CoordSystem):

    predicate_name = "Empty"

    def __init__(self, col=None, row=None):
        Predicate.__init__(self, [("col",int), ("row",int)])
        CoordSystem.__init__(self,col,row)

    def __str__(self):
        return f"empty({CoordSystem.get_col(self)}, {CoordSystem.get_row(self)}) \n"

class Bubble(Predicate,Bubble_Type,Bubble_color,CoordSystem):

    predicate_name = "Bubble"

    def __init__(self, col=None, row=None, color = None ,type = None):
        Predicate.__init__(self, [("col", int), ("row", int),("color"),("type")])
        Bubble_Type.__init__(self,type)
        Bubble_color.__init__(self,color)
        CoordSystem.__init__(self,col,row)
    
    def __str__(self):
        return f"bubble({CoordSystem.get_col(self)}, {CoordSystem.get_row(self)}, {Bubble_Type.get_type(self)}, {Bubble_color.get_color(self)}) \n"

class PlayerBubble(Predicate,Bubble_color):
    
    predicate_name = "PlayerBubble"

    def __init__(self,index = None, color = None):
        Predicate.__init__(self, [("index", int),("color")])
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

def get_input_dlv_path(exagonal_grid,player_bubbles):
    bubble_info = player_bubbles[0]
    input = []

    for i in range(len(exagonal_grid)):
        plusFactor = 2

        if(len(exagonal_grid[i]) == MAX_BUBBLES_PER_ROW):
            column = 0
        else :
            column = 1
        
        for j in range(len(exagonal_grid[i])):
            if(get_bubble_spot_type(exagonal_grid[i][j][3]) != EMPTY_SPOT_TYPE): 
                for angle in ANGLE_APPROX:
                    returnedAngle = ExistPath(exagonal_grid,exagonal_grid[i][j],bubble_info,angle)

                    if(returnedAngle is not None):
                        #determines angle
                        if(angle == ANGLE_APPROX[0] or angle == ANGLE_APPROX[1] or angle == ANGLE_APPROX[2]):
                                #when column + 1 above 20 not append
                                input.append(Path(column+1,i+1,returnedAngle))

                        if(angle == ANGLE_APPROX[3] or angle == ANGLE_APPROX[4] or angle == ANGLE_APPROX[5]):
                                input.append(Path(column-1,i+1,returnedAngle))

            column += plusFactor

    return input

def checkCollisions(exagonal_grid,current_bubble,player_bubble,angle,raycast_offset = 22):

    radius_offset = player_bubble[2] + raycast_offset

    X1 = current_bubble[0] + current_bubble[2] * math.cos(math.radians(angle))
    Y1 = current_bubble[1] + current_bubble[2] * math.sin(math.radians(angle))
    m = (Y1 - player_bubble[1]) / (X1 - player_bubble[0])
    q = player_bubble[1] - m * player_bubble[0]

    for row in range(len(exagonal_grid)):
        for bubble in exagonal_grid[row]:
            if(get_bubble_spot_type(bubble[3]) != EMPTY_SPOT_TYPE):
                if(bubble[0] != current_bubble[0] or bubble[1] != current_bubble[1]):
                    if(bubble[1] > current_bubble[1] + current_bubble[2]):
                        Xr = round((bubble[1] - q) / m)
                        if(Xr >= bubble[0] - radius_offset and Xr <= bubble[0] + radius_offset):
                            return True
                            
    return False


def ExistPath(exagonal_grid,current_bubble,player_bubble,angle):

    if(not checkCollisions(exagonal_grid,current_bubble,player_bubble,angle)):

        #calculate coords in respect of a new defined coords system based on the player_bubble

        Y = (current_bubble[0] - player_bubble[0]) * - 1
        X = abs(current_bubble[1] - player_bubble[1])

        X1 = X + current_bubble[2] * math.cos(math.radians(angle+90))
        Y1 = Y + current_bubble[2] * math.sin(math.radians(angle+270))

        m = Y1 / X1

        found_angle = math.atan(m) + math.pi/2

        return found_angle
    
    return None

'''
def conversion_doubleCoords2Pixels(x,y,radius,start_bubble_y):

    if(x % 2 == 0): #MAX_BUBBLES_ROW
        position = x/ 2
        pixel_current_x = radius + ((2*radius) * position)
    else: #MAX_BUBBLES_ROW - 1
        position = int(x/2)
        pixel_current_x = (radius * 2) + ((2*radius) * position)
    
    pixel_current_y = start_bubble_y + ((math.sqrt(3) * radius) * y)

    return (round(pixel_current_x),round(pixel_current_y))
'''


