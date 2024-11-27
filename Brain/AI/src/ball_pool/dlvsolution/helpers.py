import os
from itertools import count
from math import sqrt

from languages.predicate import Predicate
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService

from AI.src.constants import DLV_PATH


class Color(Predicate):
    predicate_name = "color"

    __ids = count(1, 1)
    __colors = []
    __MAX_DISTANCE = 40

    def __init__(self, bgr=None, ball_type = None):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Color.__ids)
        self.__bgr = bgr
        self.__ball_type = ball_type #solid o striped

    
    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_bgr(self) -> []:
        return self.__bgr

    def set_bgr(self, bgr: []):
        self.__bgr = bgr

    def get_ball_type(self) -> str:
        return self.__ball_type

    @staticmethod #statico perchè non dipende da nessuna istanza
    def __euclidean_distance(color1, color2): # indica la distanza euclidea tra due colori
        return sqrt(sum(pow(color1[i] - color2[i], 2) for i in range(3)) )

    @staticmethod
    def get_color(bgr: []):
        for color in Color.__colors:
            if Color.__euclidean_distance(color.__bgr, bgr) < Color.__MAX_DISTANCE:
                return color
        ball_type = "solid" if len(Color.__colors) < 8 else "striped"
        color = Color(bgr, ball_type)
        Color.__colors.append(color)
        return color


class Ball(Predicate):
    predicate_name = "ball"

    __ids = count(1, 1) # genera un id univoco per ogni palla, inizia da 1 e incrementa di 1

    def __init__(self, color: Color):
        Predicate.__init__(self, [("id", int), ("color", int)])
        self.__id = next(Ball.__ids)
        self.__color = color
        self.__type = color.get_ball_type()

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_color(self) -> int:
        return self.__color

    def set_color(self, color):
        self.__color = color

    def get_type(self) -> str:
        return self.__type



class Pocket(Predicate):
    predicate_name = "pocket"

    __ids = count(1, 1)

    def __init__(self, x=None, y=None, ):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Pocket.__ids)
        self.__balls = []
        self.__x = x
        self.__y = y

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_x(self) -> int:
        return self.__x

    def set_x(self, x):
        self.__x = int(x)

    def get_y(self) -> int:
        return self.__y

    def set_y(self, y):
        self.__y = int(y)

    def add_ball(self, ball):
        self.__balls.append(ball)
    
    def contains_ball(self, ball):
        return ball in self.__balls

class MoveAndShoot(Predicate): #Da modificare
    predicate_name = "moveandshoot"

    def __init__(self, ball=None, tube=None, step=None):
        Predicate.__init__(self, [("ball", int), ("tube", int), ("step", int)])
        self.__ball = ball
        self.__tube = tube
        self.__step = step

    def get_ball(self) -> int:
        return self.__ball

    def set_ball(self, ball):
        self.__ball = ball

    def get_tube(self) -> int:
        return self.__tube

    def set_tube(self, tube):
        self.__tube = tube

    def get_step(self) -> int:
        return self.__step

    def set_step(self, step):
        self.__step = step

class Game(Predicate):
    def __init__(self):
        self.current_player = 1
        self.player_targets = {1: None, 2: None}
        self.balls = []
        self.pockets = []

    def assign_targets(self,ball : Ball):
        self.player_targets[self.current_player] = ball.get_type()

    def check_target(self, ball: Ball):
        return ball.get_type() == self.player_targets[self.current_player]
    
    def switch_player(self):
        self.current_player = self.current_player % 2 + 1 


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
        for ball in tube.get_balls():
            on.append(On(ball.get_id(), ball_below, tube.get_id(), 1))
            ball_below = ball.get_id()
    return on
