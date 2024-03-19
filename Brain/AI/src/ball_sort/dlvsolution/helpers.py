import os
from itertools import count
from math import sqrt

from languages.predicate import Predicate
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from specializations.clingo.desktop.clingo_desktop_service import ClingoDesktopService

from AI.src.constants import DLV_PATH


class Color(Predicate):
    predicate_name = "color"

    __ids = count(1, 1)
    __colors = []
    __MAX_DISTANCE = 40

    def reset():
        Color.__ids = count(1, 1)
        Color.__colors = []
        Color.__MAX_DISTANCE = 40

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
    def get_color(bgr: []):
        for color in Color.__colors:
            if Color.__euclidean_distance(color.__bgr, bgr) < Color.__MAX_DISTANCE:
                return color
        color = Color(bgr)
        pos=0
        for i in range(len(Color.__colors)):
            if Color.is_less_than(color,Color.__colors[i]):
                for j in range(i,len(Color.__colors)):
                    Color.__colors[j].incr_id()
                break
            pos+=1
        Color.__colors.insert(pos,color)
        color.set_id(pos+1 )
        return color
    
    @staticmethod
    def get_bgr_by_id(id):
        for color in Color.__colors:
            if color.__id==id:
                return color.__bgr


class Ball(Predicate):
    predicate_name = "ball"

    __ids = count(1, 1)

    def reset():
        Ball.__ids = count(1, 1)

    def __init__(self, color=None):
        Predicate.__init__(self, [("id", int), ("color", int)])
        self.__id = next(Ball.__ids)
        self.__color = color

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_color(self) -> int:
        return self.__color

    def set_color(self, color):
        self.__color = color



class Tube(Predicate):
    predicate_name = "tube"

    __ids = count(1, 1)

    def reset():
        Tube.__ids = count(1, 1)

    def __init__(self, x=None, y=None, ):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Tube.__ids)
        self.__balls = []
        self.__x = x
        self.__y = y

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_balls(self) -> []:
        return self.__balls

    def set_balls(self, balls:[]):
        self.__balls = balls

    def add_ball(self, ball):
        self.__balls.append(ball)

    def get_x(self) -> int:
        return self.__x

    def set_x(self, x):
        self.__x = int(x)

    def get_y(self) -> int:
        return self.__y

    def set_y(self, y):
        self.__y = int(y)

    def custom_str(self):
        to_return = "T\n"
        for i in range(len(self.__balls),0,-1):
            to_return+=str(self.__balls[i-1])+"\n"
        return to_return


class On(Predicate):
    predicate_name = "on"
    def __init__(self, ball_above=None, ball_below=None, tube=None,position=None, step=None):
        Predicate.__init__(self, [("ball_above", int), ("tube", int),("position",int), ("step", int)])
        self.__ball_above = ball_above
        self.__ball_below = ball_below
        self.__position=position
        self.__tube = tube
        self.__step = step

    def get_ball_above(self) -> int:
        return self.__ball_above

    def set_ball_above(self, ball_above):
        self.__ball_above = ball_above

    def get_position(self) -> int:
        return self.__position

    def set_position(self, position):
        self.__position = position

    def get_ball_below(self) -> int:
        return self.__ball_below

    def set_ball_below(self, ball_below):
        self.__ball_below = ball_below

    def get_tube(self) -> int:
        return self.__tube

    def set_tube(self, tube):
        self.__tube = tube

    def get_step(self) -> int:
        return self.__step

    def set_step(self, step):
        self.__step = step
    


class Move(Predicate):
    predicate_name = "move"

    def __init__(self, tube1=None, tube2=None, step=None):
        Predicate.__init__(self, [("tube1", int), ("tube2", int)])
        self.__tube1 = tube1
        self.__tube2 = tube2
        self.__step = step

    def get_tube1(self) -> int:
        return self.__tube1

    def set_tube1(self, tube1):
        self.__tube1 = tube1

    def get_tube2(self) -> int:
        return self.__tube2

    def set_tube2(self, tube2):
        self.__tube2 = tube2

    def get_step(self) -> int:
        return self.__step

    def set_step(self, step):
        self.__step = step


class GameOver(Predicate):
    predicate_name = "gameOver"

    def __init__(self, step=None):
        Predicate.__init__(self, [("step", int)])
        self.__step = step

    def get_step(self):
        return self.__step

    def set_step(self, step):
        self.__step = step


def choose_dlv_system() -> DesktopHandler:
    try:
        if os.name == 'nt':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.exe")))
        elif os.uname().sysname == 'Darwin':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
        else:
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux")))
        
    except Exception as e:
        print(e)

def choose_clingo_system()->DesktopHandler:
    try:
        return DesktopHandler(ClingoDesktopService("/usr/bin/clingo"))
    except Exception as e:
        print(e)

def get_colors(tubes: []):
    colors = set()
    for tube in tubes:
        for ball in tube.get_elements():
            colors.add(Color.get_color(ball[3]))
    return list(colors)


def get_balls_and_tubes(tubes: []):
    tube_list = []
    balls = []
    for t in tubes:
        tube = Tube()
        tube.set_x(t.get_x())
        tube.set_y(t.get_y())
        for ball in t.get_elements():
            b = Ball(Color.get_color(ball[3]).get_id())
            balls.append(b)
            tube.add_ball(b)
        tube_list.append(tube)
    return tube_list, balls


def get_balls_position(tubes: [Tube]):
    on = []
    for tube in tubes:
        ball_below = 0
        balls = tube.get_balls()
        for i in range(len(balls)-1,-1,-1):
            on.append(On(balls[i].get_color(), None, tube.get_id(),i+1, 1))
    return on
