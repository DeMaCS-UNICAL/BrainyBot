import os
from itertools import count
from math import sqrt
import cv2
import numpy as np


from languages.predicate import Predicate
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService

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

        # Dizionario con colori in formato RGB
    POOL_REFERENCE_COLORS_RGB = {
        "yellow": np.array([255, 204, 0], dtype=np.float32),   # Giallo
        "blue": np.array([0, 0, 255], dtype=np.float32),       # Blu
        "red": np.array([255, 0, 0], dtype=np.float32),        # Rosso
        "purple": np.array([128, 0, 128], dtype=np.float32),   # Viola
        "orange": np.array([255, 102, 0], dtype=np.float32),   # Arancione
        "green": np.array([0, 153, 0], dtype=np.float32),      # Verde
        "maroon": np.array([139, 69, 19], dtype=np.float32),   # Marrone
        "black": np.array([0, 0, 0], dtype=np.float32)   ,      # Nero (8-ball)
        "white": np.array([255, 255, 255], dtype=np.float32)   # Bianco (cue)
    }

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
        # Calcolo del colore medio e della white ratio
        if isinstance(bgr, np.ndarray):
            if bgr.ndim == 1:
                self.__mean_color = bgr
            else:
                self.__mean_color = np.mean(bgr, axis=(0, 1))
        else:
            self.__mean_color = np.array(bgr, dtype=np.float32)
        self.__white_ratio = self.compute_white_ratio(bgr)

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
        best_category = None
        best_distance = float('inf')
        for category, ref_color in BPoolColor.POOL_REFERENCE_COLORS_BGR.items():
            distance = np.linalg.norm(detected_color - ref_color)
            if distance < best_distance:
                best_distance = distance
                best_category = category
        print(f"Detected color: {detected_color},Ref color {BPoolColor.POOL_REFERENCE_COLORS_BGR[best_category]} Best category: {best_category}")
        return best_category
    
    @staticmethod
    def get_color(patch):
        """
        Estrae (o crea) un BPoolColor dalla patch.
        Se la luminosità media è molto alta o bassa, classifica la pallina come 'cue' (bianca)
        o 'eight' (nera). Altrimenti, calcola il colore medio e usa il riferimento per
        assegnare la categoria più vicina.
        """
         
        
        if isinstance(patch, BPoolColor):
            return patch

        if isinstance(patch, Color):
            patch = patch.get_bgr()

        if not isinstance(patch, np.ndarray):
            patch = np.array(patch, dtype=np.float32)

        if patch.ndim == 1:
            patch = patch.reshape((1, 1, -1))

        if patch.size == 0:
            mean_color = np.array([0, 0, 0], dtype=np.float32)
        else:
            mean_color = np.mean(patch, axis=(0, 1))

        avg = np.mean(mean_color)
        ball_type = BPoolColor.find_closest_color_category(detected_color=mean_color)
        print("------------------")

        # Verifica se esiste già un BPoolColor simile
        for c in BPoolColor.__colors:
            dist = BPoolColor.__euclidean_distance(c.get_bgr(), mean_color)
            if dist < BPoolColor.__MAX_DISTANCE:
                return c

        new_color = BPoolColor(mean_color, ball_type)
        BPoolColor.__colors.append(new_color)
        return new_color
    

    @classmethod
    def assign_ball_types(cls, balls):
        """
        Raggruppa le palle per categoria di colore e, per ciascun colore, assegna:
        - Se il colore è "white": viene impostata come "cue" (si tiene al massimo 1 palla)
        - Se il colore è "black": viene impostata come "eight" (si tiene al massimo 1 palla)
        - Altrimenti: se ci sono due palle per la categoria, quella con la distanza maggiore
            dal colore di riferimento viene etichettata come "striped" e l'altra come "solid";
            se c'è solo una palla, viene impostata come "solid".
        """
        color_groups = {}
        for ball in balls:
            # Assumiamo che ball.get_color().get_bgr() restituisca il colore in formato BGR
            detected_color = np.array(ball.get_color().get_bgr(), dtype=np.float32)
            category = cls.find_closest_color_category(detected_color)
            ball.category = category  # Salva la categoria nell'oggetto
            ref_color = cls.POOL_REFERENCE_COLORS_BGR[category]
            distance = np.linalg.norm(detected_color - ref_color)
            if category not in color_groups:
                color_groups[category] = []
            color_groups[category].append((ball, distance))
        
        final_balls = []
        for category, ball_list in color_groups.items():
            # Gestione speciale per la palla bianca (cue) e quella nera (eight)
            if category == "white":
                # Si mantiene al massimo 1 palla per il bianco (cue)
                ball_list_sorted = sorted(ball_list, key=lambda x: x[1])
                ball_list_sorted[0][0].get_color().set_ball_type("cue")
                final_balls.append(ball_list_sorted[0][0])
                if len(ball_list_sorted) > 1:
                    print("Attenzione: rilevate più palle bianche; ne è stata mantenuta solo una come cue.")
            elif category == "black":
                # Si mantiene al massimo 1 palla per il nero (eight)
                ball_list_sorted = sorted(ball_list, key=lambda x: x[1])
                ball_list_sorted[0][0].get_color().set_ball_type("eight")
                final_balls.append(ball_list_sorted[0][0])
                if len(ball_list_sorted) > 1:
                    print("Attenzione: rilevate più palle nere; ne è stata mantenuta solo una come eight.")
            else:
                # Per gli altri colori: se ci sono più di 2, ne si considerano solo 2
                ball_list_sorted = sorted(ball_list, key=lambda x: x[1])
                if len(ball_list_sorted) > 2:
                    ball_list_sorted = ball_list_sorted[:2]
                
                if len(ball_list_sorted) == 2:
                    # Assegna "striped" alla palla con distanza maggiore dal colore di riferimento
                    if ball_list_sorted[0][1] > ball_list_sorted[1][1]:
                        ball_list_sorted[0][0].get_color().set_ball_type("striped")
                        ball_list_sorted[1][0].get_color().set_ball_type("solid")
                    else:
                        ball_list_sorted[0][0].get_color().set_ball_type("solid")
                        ball_list_sorted[1][0].get_color().set_ball_type("striped")
                elif len(ball_list_sorted) == 1:
                    ball_list_sorted[0][0].get_color().set_ball_type("solid")
                
                for ball, _ in ball_list_sorted:
                    final_balls.append(ball)
        
        # Stampa il ball type e il nome del colore per ogni palla
        for ball in final_balls:
            bp_color = ball.get_color() if hasattr(ball, "get_color") else ball.color
            print(f"Ball at ({ball.get_x()}, {ball.get_y()}) with radius {ball.get_r()} is type: {bp_color.get_ball_type()} and color: {ball.category}")
        
        return final_balls



    
    def get_white_ratio(self):
        return self.__white_ratio

    def compute_white_ratio(self, patch):
        """
        Calcola la percentuale di pixel "bianchi" nella patch.
        Se la patch è un singolo pixel, restituisce 1.0 se il valore medio è elevato.
        """
        if not isinstance(patch, np.ndarray):
            patch = np.array(patch, dtype=np.float32)
        if patch.ndim == 1:
            avg = np.mean(patch)
            return 1.0 if avg > 240 else 0.0
        patch_uint8 = np.uint8(patch)
        gray = cv2.cvtColor(patch_uint8, cv2.COLOR_BGR2GRAY)
        white_pixels = np.sum(gray > 240)
        total_pixels = gray.size
        return white_pixels / total_pixels
    
    def get_color_key(self):
        """
        Genera una chiave per il raggruppamento basata sul colore medio arrotondato.
        Qui arrotondiamo al multiplo di 20 per ridurre la sensibilità a piccole variazioni.
        """
        quantization_factor = 60  # Aumenta il fattore rispetto a 10 per ottenere gruppi più ampi
        rounded = tuple(int(round(c / quantization_factor) * quantization_factor) for c in self.__mean_color)
        return rounded


class Ball(Predicate):
    predicate_name = "ball"

    __ids = count(1, 1) # genera un id univoco per ogni palla, inizia da 1 e incrementa di 1

    def __init__(self, color: BPoolColor):
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

    def get_r(self) -> int:
        return self.__r
    
    def set_r(self, r):
        self.__r = int(r)

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
        print(f"Ball: {b.get_type()}")
    # Definizione delle Pocket (coordinate da adattare)
    pockets = []

    return pockets, ball_list

