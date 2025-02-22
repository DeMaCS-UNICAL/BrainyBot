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


    @staticmethod
    def __euclidean_distance(color1, color2):
        return sqrt(pow(color1[0] - color2[0], 2) +
                    pow(color1[1] - color2[1], 2) +
                    pow(color1[2] - color2[2], 2))

    @staticmethod
    def get_color(bgr: list):
        # Verifica se esiste già un oggetto Color simile
        for color in Color.__colors:
            if Color.__euclidean_distance(color.__bgr, bgr) < Color.__MAX_DISTANCE:
                return color
        # Se non esiste, determina il tipo di palla in base al colore
        avg = sum(bgr) / 3.0
        # Heuristica per riconoscere bianca e nera
        if avg > 240:
            ball_type = "bianca"   # Cue ball
        elif avg < 30:
            ball_type = "nera"     # 8-ball
        else:
            # Per le altre palline, alterna fra "piena" e "mezza"
            non_special = [c for c in Color.__colors if c.get_ball_type() not in ("bianca", "nera")]
            if len(non_special) < 7:
                ball_type = "piena"
            else:
                ball_type = "mezza"
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
        self.__x = None
        self.__y = None

    def get_id(self) -> int:
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_color(self) -> int:
        return self.__color

    def set_color(self, color):
        self.__color = color
    
    def get_x(self) -> int:
        return self.__x

    def set_x(self, x):
        self.__x = int(x)
    
    def get_y(self) -> int:
        return self.__y
    
    def set_y(self, y):
        self.__y = int(y)
        
    def get_r(self) -> int:
        return self.__r
    
    def set_r(self, r):
        self.__r = int(r)

    def get_type(self) -> str:
        return self.__color.get_ball_type()
        
        



class Pocket(Predicate):
    predicate_name = "pocket"

    __ids = count(1, 1)

    def __init__(self, x=None, y=None, ):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Pocket.__ids)
        self.__balls = []   # Palline imbucate
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

    def __init__(self, ball=None, pocket=None, step=None):
        Predicate.__init__(self, [("ball", int), ("pocket", int), ("step", int)])
        self.__ball = ball
        self.__pocket = pocket
        self.__step = step

    def get_ball(self) -> int:
        return self.__ball

    def set_ball(self, ball):
        self.__ball = ball

    def get_pocket(self):
        return self.__pocket

    def set_pocket(self, pocket):
        self.__pocket = pocket

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
        # Al primo tiro, il giocatore sceglie il target in base al tipo (solid o striped)
        self.player_targets[self.current_player] = ball.get_type()

    def check_target(self, ball: Ball):
        # Controlla se la pallina colpita corrisponde al target del giocatore corrente
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


def get_colors(detections: list):
    """
    L'input è una lista di rilevamenti [x, y, r, bgr].
    Restituisce la lista dei colori distinti (con il relativo ball_type).
    """
    colors = set()
    #print("Detections:", detections.__str__())
    for detection in detections:
        # detection[3] contiene il BGR
        colors.add(Color.get_color(detection.get_color().get_bgr()))
    return list(colors)


def get_balls_and_pockets(detections: list):
    """
    Converte i rilevamenti in oggetti Ball e inizializza le Pocket.
    - detections: lista di [x, y, r, bgr]
    - Restituisce una tupla (lista_pockets, lista_balls).
    Le Pocket vengono inizializzate con coordinate fisse (da adattare al tavolo reale).
    """
    ball_list = []
    for ball in detections:
        color_obj = Color.get_color(ball.get_color().get_bgr())

        b = Ball(color_obj)
        ball_list.append(b)
    # Definizione delle Pocket (coordinate da adattare)
    pockets = []
    
    pockets.append(Pocket(x=100, y=50))   # Pocket p1
    pockets.append(Pocket(x=500, y=50))   # Pocket p2
    pockets.append(Pocket(x=900, y=50))   # Pocket p3
    pockets.append(Pocket(x=100, y=400))  # Pocket p4
    pockets.append(Pocket(x=500, y=400))  # Pocket p5
    pockets.append(Pocket(x=900, y=400))  # Pocket p6

    return pockets, ball_list

