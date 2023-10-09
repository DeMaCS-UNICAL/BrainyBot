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

    def __init__(self, bgr=None):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Color.__ids)
        self.__bgr = bgr

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_bgr(self) -> []:
        return self.__bgr

    def set_bgr(self, bgr: []):
        self.__bgr = bgr

    @staticmethod
    def __euclidean_distance(color1, color2):
        return sqrt(pow(color1[0] - color2[0], 2) + pow(color1[1] - color2[1], 2) + pow(color1[2] - color2[2], 2))

    @staticmethod
    def get_color(bgr: []):
        for color in Color.__colors:
            if Color.__euclidean_distance(color.__bgr, bgr) < Color.__MAX_DISTANCE:
                return color
        color = Color(bgr)
        Color.__colors.append(color)
        return color


class Ball(Predicate):
    predicate_name = "ball"

    __ids = count(1, 1)

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
        self.__x = x

    def get_y(self) -> int:
        return self.__y

    def set_y(self, y):
        self.__y = y


class On(Predicate):
    predicate_name = "on"

    def __init__(self, ball_above=None, ball_below=None, tube=None, step=None):
        Predicate.__init__(self, [("ball_above", int), ("ball_below", int), ("tube", int), ("step", int)])
        self.__ball_above = ball_above
        self.__ball_below = ball_below
        self.__tube = tube
        self.__step = step

    def get_ball_above(self) -> int:
        return self.__ball_above

    def set_ball_above(self, ball_above):
        self.__ball_above = ball_above

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
    return colors


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
