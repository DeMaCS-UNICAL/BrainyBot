import os
from itertools import count
from math import sqrt
import cv2
import numpy as np


from languages.predicate import Predicate
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from specializations.clingo.desktop.clingo_desktop_service import ClingoDesktopService


from AI.src.constants import DLV_PATH
from AI.src.asp_mapping.color import Color



"""
1: Gialla
2: Blu scuro
3: Rossa
4: Viola scuro
5: Arancione
6: Verde scuro
7: Marrone
"""

class BPoolColor(Color):
    """
    Estensione di Color per il biliardo (8-ball pool).
    Aggiunge il concetto di 'ball_type' (cue, eight, solid, striped)
    e parametri di distanza differenti.
    """
    predicate_name = "color"

    __ids = count(1, 1)
    __colors = []
    __MAX_DISTANCE = 20  # più tollerante rispetto a Color

    def reset():
        BPoolColor.__ids = count(1, 1)

    # Dizionario con colori in formato BGR (usato in OpenCV) ordinati dal più chiaro al più scuro
    POOL_REFERENCE_COLORS_BGR = {
        "white": np.array([255, 255, 255]),   # Bianco: BGR(255, 255, 255) - luminosità: 255
        "yellow": np.array([0, 172, 253]),    # Giallo: BGR(0, 255, 255) - luminosità: 226.7
        "orange": np.array([0, 94, 239]),    # Arancione: BGR(0, 165, 255) - luminosità: 178.5
        "red": np.array([16, 0, 255]),         # Rosso: BGR(0, 0, 255) - luminosità: 76.5
        "blue": np.array([193, 103, 43]),        # Blu: BGR(255, 0, 0) - luminosità: 76.5
        "purple": np.array([143,30,79]),    # Viola: BGR(128, 0, 128) - luminosità: 73.1
        "green": np.array([41, 145, 20]),       # Verde: BGR(0, 128, 0) - luminosità: 75.5
        "maroon": np.array([0, 18, 99]),      # Bordeaux: BGR(0, 0, 128) - luminosità: 38.2
        "black": np.array([0, 0, 0])          # Nero: BGR(0, 0, 0) - luminosità: 0
    }


    def __init__(self, bgr=None, ball_type=None):
        super().__init__(bgr)
        self.set_id(next(BPoolColor.__ids))
        self.__ball_type = ball_type
  

        if isinstance(bgr, np.ndarray):
            if bgr.ndim == 1:
                self.__mean_color = bgr
            else:
                self.__mean_color = np.mean(bgr, axis=(0, 1))
        else:
            self.__mean_color = np.array(bgr, dtype=np.float32)


    def get_white_ratio(self):
        return self.__white_ratio
    
    def set_white_ratio(self, white_ratio: float):
        self.__white_ratio = white_ratio
        print(f"White ratio set: {self.__white_ratio:.4f}")


    def get_ball_type(self):
        return self.__ball_type

    def set_ball_type(self, ball_type):
        self.__ball_type = ball_type

    @staticmethod
    def __euclidean_distance(color1, color2):
        return sqrt(pow(color1[0] - color2[0], 2) + 
                    pow(color1[1] - color2[1], 2) + 
                    pow(color1[2] - color2[2], 2))
    
    def find_closest_color_category(detected_color):
        """
        Dato un colore (BGR) rilevato, restituisce la categoria (stringa)
        del colore più vicino tra quelle di POOL_REFERENCE_COLORS.
        """
        return min(BPoolColor.POOL_REFERENCE_COLORS_BGR.items(),
                key=lambda item: BPoolColor.__euclidean_distance(
                    detected_color, item[1]
                ))[0]

    
    @staticmethod
    def get_color(patch, white_ratio:float = None):
        #print(f"White ratio: {white_ratio:.4f}")

        """
        Estrae (o crea) un BPoolColor dalla patch, assegnando solo il valore BGR.
        La classificazione (ball type) verrà gestita successivamente.
        """
        if isinstance(patch, BPoolColor):
            return patch

        if isinstance(patch, Color):
            patch = patch.get_bgr()

        if not isinstance(patch, np.ndarray):
            patch = np.array(patch, dtype=np.float32)

        if patch.ndim == 1:
            patch = patch.reshape((1, 1, -1))

        # Calcola il colore medio; se la patch è vuota usa [0, 0, 0]
        mean_color = np.mean(patch, axis=(0, 1)) 

        new_color = BPoolColor(mean_color)  
        
        BPoolColor.__colors.append(new_color)
        return new_color


    @classmethod
    def assign_ball_types(cls, balls):
        """
        Raggruppa le palle per categoria di colore e, per ciascuna:
          - "white": viene mantenuta una sola palla (tipo "cue").
          - "black": viene mantenuta una sola palla (tipo "eight").
          - Altri colori: se ci sono due palle, si usa sia la distanza dal colore di riferimento
            che il white_ratio per determinare quale viene etichettata "striped" (maggiore white_ratio)
            e quale "solid"; se c'è solo una palla, viene etichettata "striped" se il white_ratio è alto.
        """
        color_groups = {}
        for ball in balls:
            color = ball.get_color()
            detected_color = np.array(color.get_bgr(), dtype=np.float32)
            category = cls.find_closest_color_category(detected_color)

            ball.category = category  # Salva la categoria nell'oggetto
            ref_color = cls.POOL_REFERENCE_COLORS_BGR[category]
            distance = BPoolColor.__euclidean_distance(detected_color, ref_color)
            white_ratio = ball.get_white_ratio()

            color_groups.setdefault(category, []).append((ball, distance, white_ratio))
           
        final_balls = []
        for category, ball_list in color_groups.items():
            # Ordina in base alla distanza dal colore di riferimento (minore è migliore)
            ball_list_sorted = sorted(ball_list, key=lambda x: x[1])

            if category in ("white", "black"):
                chosen_ball, _, _ = ball_list_sorted[0]
                ball_type = "cue" if category == "white" else "eight"
                chosen_ball.get_color().set_ball_type(ball_type)
                final_balls.append(chosen_ball)

                if len(ball_list_sorted) > 1:
                    print(f"Attenzione: rilevate più palle {category}; ne è stata mantenuta solo una come {ball_type}.")
            else:
                ball_list_sorted = ball_list_sorted[:2]
                #print(f"Rilevate {len(ball_list_sorted)} palle {category}.")
                ball1, d1, wr1 = ball_list_sorted[0]

                if len(ball_list_sorted) == 2:
                    ball2, d2, wr2 = ball_list_sorted[1]
                    #print(f"Rilevate due palle {category}. Distanze: {d1:.2f}, {d2:.2f}; White ratios: {wr1:.4f}, {wr2:.4f}")
                    # Se la differenza nel white_ratio è significativa, assegna "striped" a quella con white_ratio maggiore.

                    if d1 > d2 or wr1 > wr2:
                        ball1.get_color().set_ball_type("striped")
                        ball2.get_color().set_ball_type("solid")
                    else:
                        ball1.get_color().set_ball_type("solid")
                        ball2.get_color().set_ball_type("striped")
                    #print("-" * 30)
                        
                elif len(ball_list_sorted) == 1:
                    #print(f"Rilevata una palla {category} con distanza: {ball_list_sorted[0][1]:.2f} e white ratio: {ball_list_sorted[0][2]:.2f}")
                    ball1.get_color().set_ball_type("striped") if wr1 > 0.9 else ball1.get_color().set_ball_type("solid")
            
                for ball, _, _ in ball_list_sorted:
                    final_balls.append(ball)        # Stampa il tipo di palla e il colore per ogni palla finale

        for ball in final_balls:
            bp_color = ball.get_color() if hasattr(ball, "get_color") else ball.color
            print(f"Ball at ({ball.get_x()}, {ball.get_y()}) is type: {bp_color.get_ball_type().upper()} "
                f"and color: {ball.category.upper()}")

            
        return final_balls


class Ball(Predicate):
    predicate_name = "ball"

    __ids = count(1, 1) # genera un id univoco per ogni palla, inizia da 1 e incrementa di 1

    def reset():
        Ball.__ids = count(1, 1)

    def __init__(self):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Ball.__ids)
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

    def get_white_ratio(self):
        return self.__white_ratio

    def set_white_ratio(self, white_ratio: float):
        self.__white_ratio = white_ratio
    
    
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

    def set_aimed(self, aimed):
        self.__aimed = aimed
    
    def is_aimed(self):
        return self.__aimed
        

class Pocket(Predicate):
    predicate_name = "pocket"

    __ids = count(1, 1)

    def reset():
        Pocket.__ids = count(1, 1)

    def __init__(self, x=None, y=None):
        Predicate.__init__(self, [("id", int)])
        self.__id = next(Pocket.__ids)
        self.__near_balls = []   # Palline imbucate
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

    def get_r(self) -> int:
        return self.__r
    
    def set_r(self, r):
        self.__r = int(r)

    def add_ball(self, ball):
        self.__near_balls.append(ball)
    
    def contains_ball(self, ball):
        return ball in self.__near_balls


class AimLine(Predicate):

    predicate_name = "aimline"

    __ids = count(1, 1)

    def reset():
        AimLine.__ids = count(1, 1)

    def __init__(self, x1=None, y1=None, x2=None, y2=None):
        Predicate.__init__(self, [("x1", int), ("y1", int), ("x2", int), ("y2", int)])
        self.__id = next(AimLine.__ids)
        self.__x1 = int(x1)
        self.__y1 = int(y1)
        self.__x2 = int(x2)
        self.__y2 = int(y2)

    def get_id(self) -> int:
        return self.__id
    
    def get_x1(self) -> int:
        return self.__x1
    
    def set_x1(self, x1):
        self.__x1 = x1
    
    def get_y1(self) -> int:
        return self.__y1
    
    def set_y1(self, y1):
        self.__y1 = y1

    def get_x2(self) -> int:    
        return self.__x2
    
    def set_x2(self, x2):
        self.__x2 = x2

    def get_y2(self) -> int:
        return self.__y2

    def set_y2(self, y2):
        self.__y2 = y2
    
    def get_coordinates(self):
        return self.__x1, self.__y1, self.__x2, self.__y2

    
class MoveAndShoot(Predicate): #Da modificare
    predicate_name = "moveandshoot"

    def __init__(self,  pocket=None, stick=None, ghost_ball= None, aimedball=None, aim_line=None, step=None):
        Predicate.__init__(self, [("pocket", int), ("stick", int), ("ghost_ball", int), 
                                  ("aimed_ball", int), ("aim_line", int), ("step", int)])
        self.__pocket = pocket
        self.__stick = stick
        self.__ghost_ball = ghost_ball
        self.__aimed_ball = aimedball
        self.__aim_line = aim_line
        self.__step = step

    def get_pocket(self):
        return self.__pocket

    def set_pocket(self, pocket):
        self.__pocket = pocket

    def get_ghost_ball(self):
        return self.__ghost_ball
    
    def set_ghost_ball(self, ghost_ball):
        self.__ghost_ball = ghost_ball
    
    def get_aimed_ball(self):
        return self.__aimed_ball
    
    def set_aimed_ball(self, aimed_ball):
        self.__aimed_ball = aimed_ball

    def get_aim_line(self):
        return self.__aim_line

    def set_aim_line(self, aim_line):
        self.__aim_line = aim_line

    def get_step(self) -> int:
        return self.__step

    def set_step(self, step):
        self.__step = step

    def get_stick(self):
        return self.__stick
    
    def set_stick(self, stick):
        self.__stick = stick


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

def choose_clingo_system() -> DesktopHandler:
    return DesktopHandler(ClingoDesktopService("/usr/bin/clingo"))

def get_balls_and_near_pockets(balls: list,pockets : list, ball_type = "solid"):
    
    """
    Per ogni pallina del tipo indicato rileva la buca più vicina 
    e aggiunge una tupla (buca, pallina, distanza) alla lista.
    La lista viene poi ordinata dalla distanza minima alla massima.
    """
    pockets_ordered = []
    for ball in balls:
        if ball.get_type() != ball_type:
            continue
        dist_min = float('inf')  # usa float('inf') per rappresentare l'infinito
        nearest_pkt = None

        for pkt in pockets:
            distance = sqrt((pkt.get_x() - ball.get_x())**2 + (pkt.get_y() - ball.get_y())**2)
            if distance < dist_min:
                dist_min = distance
                nearest_pkt = pkt

        pockets_ordered.append((nearest_pkt, ball, dist_min))
    
    # Ordina la lista in base alla distanza (terzo elemento della tupla)
    pockets_ordered.sort(key=lambda tup: tup[2])
    pockets_ordered = [tup[0].add_ball(tup[1]) for tup in pockets_ordered]  

    return pockets_ordered, balls


def get_aimed_ball_and_aim_line(ghost_ball : Ball, stick: AimLine, aimed_ball : Ball, aim_line: AimLine):

    if aimed_ball == None:
        aimed_ball_to_debug = 22
        print("Aimed ball is None")
    else:
        print("Aimed ball is not None")
        aimed_ball_to_debug = aimed_ball.get_id()

    if aim_line == None:
        aim_line_id_to_debug = 33
        print("Aim line is None")
    else:
        print("Aim line is not None")
        aim_line_id_to_debug = aim_line.get_id()

    situation = [MoveAndShoot(ghost_ball.get_id(), stick.get_id(),ghost_ball.get_id(),
                        aimed_ball_to_debug , aim_line_id_to_debug, step=1)]
    return situation