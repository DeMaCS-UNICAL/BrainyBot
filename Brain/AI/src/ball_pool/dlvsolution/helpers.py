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
                chosen_ball.set_type(ball_type)
                final_balls.append(chosen_ball)

                if len(ball_list_sorted) > 1:
                    print(f"Attenzione: rilevate più palle {category}; ne è stata mantenuta solo una come {ball_type}.")
            else:
                # Limita la lista a massimo 3 elementi, se ce ne sono di più.
                ball_list_sorted = ball_list_sorted[:2]
                
                if len(ball_list_sorted) == 1:
                    ball1, d1, wr1 = ball_list_sorted[0]
                    ball1.set_type("striped") if wr1 > 0.9 else ball1.set_type("solid")
                
                elif len(ball_list_sorted) == 2:
                    ball1, d1, wr1 = ball_list_sorted[0]
                    ball2, d2, wr2 = ball_list_sorted[1]
                    if d1 > d2 or wr1 > wr2:
                        ball1.set_type("striped")
                        ball2.set_type("solid")
                    else:
                        ball1.set_type("solid")
                        ball2.set_type("striped")

            
                for ball, _, _ in ball_list_sorted:
                    final_balls.append(ball)        # Stampa il tipo di palla e il colore per ogni palla finale

        for ball in final_balls:
            bp_color = ball.get_color() if hasattr(ball, "get_color") else ball.color
            #print(f"Ball at ({ball.get_x()}, {ball.get_y()}) is type: {bp_color.get_ball_type().upper()} and color: {ball.category.upper()}")

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
    
    def set_shot_score(self, score):
        self.__shot_score = score
    
    def get_shot_score(self):
        return self.__shot_score
    
    def get_x(self):
        return self.__x

    def set_x(self, x):
        self.__x = x
    
    def get_y(self):
        return self.__y
    
    def set_y(self, y):
        self.__y = y
        
    def get_r(self):
        return self.__r
    
    def set_r(self, r):
        self.__r = r
    
    def get_coordinates(self):
        return self.__x, self.__y
    
    def get_type(self) -> str:
        return self.__type
    
    def set_type(self, ball_type):
        self.__type = ball_type

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
        self.__near_balls = []   
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

    def get_all_balls(self):
        return self.__near_balls
    
    def get_ball(self, index):
        return self.__near_balls[index]
    
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

import math

def calculate_shot_angle(white, target, pocket):
    """
    Calcola l'angolo (in gradi) tra il vettore white->target e target->pocket.
    """
    # Vettori
    v1 = (target.get_x() - white.get_x(), target.get_y() - white.get_y())
    v2 = (pocket.get_x() - target.get_x(), pocket.get_y() - target.get_y())
    
    # Prodotto scalare e magnitudini
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    if mag1 * mag2 == 0:
        return 0
    
    # Calcola e converte l'angolo in gradi
    angle_rad = math.acos(dot / (mag1 * mag2))
    return math.degrees(angle_rad)

def calculate_shot_score(white, target, pocket, balls):
    """
    Calcola un punteggio per il tiro basato sui seguenti criteri:
      - Percorso bianca->target: bonus se libero, penalità altrimenti.
      - Percorso target->pocket: bonus se libero, penalità altrimenti.
      - Distanza target->pocket: bonus maggiore per distanze minori.
      - Angolo del tiro: bonus per angoli piccoli, penalità per angoli elevati.
    """
    score = 0
    
    # Verifica il percorso dalla bianca al target
    if is_path_clear(white, target, balls):
        score += 50
    
    # Verifica il percorso dal target alla pocket
    if is_path_clear(target, pocket, balls):
        score += 50

    # Bonus in base alla distanza target->pocket (maggiore bonus per distanze inferiori)
    distance = math.sqrt((target.get_x() - pocket.get_x())**2 + (target.get_y() - pocket.get_y())**2)
    score += max(0, 100 - distance)  # ad es., se la distanza è 60, aggiungiamo 40

    # Bonus/penalità basati sull'angolo del tiro
    angle = calculate_shot_angle(white, target, pocket)
    if angle < 30:
        score += (30 - angle) * 2  # bonus proporzionale per angoli piccoli

    return score


def get_best_shot(white, balls, pockets, ball_type="solid"):
    """
    Per ogni pallina (del tipo indicato) che non sia la bianca,
    e per ogni pocket, calcola il punteggio del tiro.
    Restituisce la combinazione (target, pocket) con il punteggio più alto.
    """
    best_score = -float('inf')
    best_target = None
    best_pocket = None

    for target in balls:
        if target.get_type() == "cue":
            continue  # escludi la bianca
        
        for pocket in pockets:
            # Calcola il punteggio per la combinazione target-pocket
            shot_score = calculate_shot_score(white, target, pocket, balls)
            # Debug: print(f"Tiro bianca->{target.get_id()}->pocket({pocket.get_x()}, {pocket.get_y()}): {shot_score:.2f}")
            if shot_score > best_score:
                best_score = shot_score
                best_target = target
                best_pocket = pocket

    return best_target, best_pocket, best_score


def is_in_between(white, target, other):
    """
    Verifica se la pallina 'other' si trova sul segmento tra la pallina bianca 'white'
    e la pallina target, considerando la soglia BALL_RADIUS.
    """
    # Vettore dal punto di partenza (white) al target
    dx = target.get_x() - white.get_x()
    dy = target.get_y() - white.get_y()
    segment_length = sqrt(dx**2 + dy**2)
    if segment_length == 0:
        return False

    # Calcola la proiezione del vettore (other - white) su (target - white)
    t = ((other.get_x() - white.get_x()) * dx + (other.get_y() - white.get_y()) * dy) / (segment_length**2)
    
    # Se la proiezione non cade sul segmento, non è in mezzo
    if t < 0 or t > 1:
        return False

    # Punto di proiezione sul segmento
    proj_x = white.get_x() + t * dx
    proj_y = white.get_y() + t * dy

    # Distanza tra il punto proiettato e il centro della pallina 'other'
    dist = sqrt((other.get_x() - proj_x)**2 + (other.get_y() - proj_y)**2)
    
    return dist < 25

def is_path_clear(white, target, balls):
    """
    Verifica che non esista nessuna pallina diversa da quella bianca e dalla pallina target
    che si trovi tra la palla bianca e la pallina target.
    """
    for other in balls:
        if other == white or other == target:
            continue
        if is_in_between(white, target, other):
            return False
    return True

def get_best_pair_to_shoot(balls: list, pockets: list, ball_type="solid"):
    """
    Per ogni pallina del tipo indicato (esclusa la bianca), valuta il tiro verso ciascuna pocket
    calcolando un punteggio basato su:
      - Percorso libero: dalla bianca al target e dal target alla pocket.
      - Distanza: bonus per distanze target->pocket minori.
      - Angolo del tiro: bonus per traiettorie più lineari.
    
    La pallina viene associata alla pocket per cui il tiro ha il punteggio più alto.
    
    Restituisce la lista delle pocket ordinate in base al numero di palline associate.
    """
    # Individua la palla bianca
    white_ball = next((b for b in balls if b.get_type() == "cue"), None)
    
    # Se non esiste la pallina bianca, procediamo senza il controllo di percorso bianca->target
    if white_ball is None:
        print("Attenzione: palla bianca non trovata!")
    
    best_score = -float('inf')
    best_pocket = None
    # Per ogni pallina target, valuta il tiro verso ogni pocket
    for ball in balls:
        if ball.get_type() == "cue":
            continue  # salta la palla bianca
        
        # Se è specificato un ball_type, consideriamo solo quelle palline
        if ball_type is not None and ball.get_type() != ball_type:
            continue
        
        # Se esiste la palla bianca, controlla che non ci siano palline in mezzo (per il percorso bianca->target)
        if white_ball and not is_path_clear(white_ball, ball, balls):
            continue  # esclude la pallina se il percorso non è libero
        
        best_curr_score = -float('inf')
        best_curr_pocket = None
        
        # Per ogni pocket, calcola il punteggio del tiro (bianca -> target -> pocket)
        for pkt in pockets:
            # Calcola il punteggio: si parte dal presupposto che se la palla bianca non esiste, il punteggio sarà solo parziale
            shot_score = calculate_shot_score(white_ball, ball, pkt, balls)
            # Debug: print(f"Palla {ball.get_id()} -> Pocket ({pkt.get_x()},{pkt.get_y()}): score = {shot_score:.2f}")
            if shot_score > best_score:
                best_curr_score = shot_score
                best_curr_pocket = pkt
        
        # Se è stata trovata una pocket migliore, associa la pallina ad essa
        if best_curr_pocket is not None:
            if best_curr_score > best_score:
                ball.set_shot_score(best_curr_score)
                best_score = best_curr_score
                best_curr_pocket.add_ball(ball)
                best_pocket = best_curr_pocket
                
    print(f"Best pocket: {best_pocket.get_id()}")
    for ball in best_pocket.get_all_balls():
        print(f"Ball {ball.get_id()} associated with pocket {best_pocket.get_id()}")
    print(f"Best score: {best_score}")
    return best_pocket



def get_aimed_ball_and_aim_line(ghost_ball : Ball, stick: AimLine, aimed_ball : Ball, aim_line: AimLine):

    if aimed_ball == None:
        aimed_ball_to_debug = 0
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