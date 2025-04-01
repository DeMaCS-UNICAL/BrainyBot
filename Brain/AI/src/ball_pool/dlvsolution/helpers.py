import os
from itertools import count
from math import sqrt
import cv2
import numpy as np

import math


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

class PoolBallsColor(Color):
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
        PoolBallsColor.__ids = count(1, 1)

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
        self.set_id(next(PoolBallsColor.__ids))
        self.__ball_type = ball_type
  
        if isinstance(bgr, np.ndarray):
            if bgr.ndim == 1:
                self.__mean_color = bgr
            else:
                self.__mean_color = np.mean(bgr, axis=(0, 1))
        else:
            self.__mean_color = np.array(bgr, dtype=np.float32)

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
        return min(PoolBallsColor.POOL_REFERENCE_COLORS_BGR.items(),
                key=lambda item: PoolBallsColor.__euclidean_distance(
                    detected_color, item[1]
                ))[0]

    
    @staticmethod
    def get_color(patch, white_ratio:float = None):
        #print(f"White ratio: {white_ratio:.4f}")

        """
        Estrae (o crea) un PoolBallsColor dalla patch, assegnando solo il valore BGR.
        La classificazione (ball type) verrà gestita successivamente.
        """
        if isinstance(patch, PoolBallsColor):
            return patch

        if isinstance(patch, Color):
            patch = patch.get_bgr()

        if not isinstance(patch, np.ndarray):
            patch = np.array(patch, dtype=np.float32)

        if patch.ndim == 1:
            patch = patch.reshape((1, 1, -1))

        # Calcola il colore medio; se la patch è vuota usa [0, 0, 0]
        mean_color = np.mean(patch, axis=(0, 1)) 

        new_color = PoolBallsColor(mean_color)  
        
        PoolBallsColor.__colors.append(new_color)
        return new_color


    @classmethod
    def group_balls_by_color(cls, balls):
        """
        Raggruppa le palle per categoria di colore.
        Per ogni palla, viene calcolata la distanza dal colore di riferimento e
        il white_ratio. Restituisce un dizionario con chiave la categoria e valore
        una lista di tuple (ball, distanza, white_ratio).
        """
        color_groups = {}
        for ball in balls:
            detected_color = np.array(ball.get_color().get_bgr(), dtype=np.float32)
            category = cls.find_closest_color_category(detected_color)
            ball.category = category  # Salva la categoria nell'oggetto

            ref_color = cls.POOL_REFERENCE_COLORS_BGR[category]
            distance = cls.__euclidean_distance(detected_color, ref_color)
            white_ratio = ball.get_white_ratio()  # Metodo atteso sull'oggetto palla

            color_groups.setdefault(category, []).append((ball, distance, white_ratio))
        return color_groups

    @classmethod
    def assign_types_from_groups(cls, color_groups):
        """
        Assegna il ball type per ogni gruppo di colore.
        - Per "white" e "black", viene mantenuta una sola palla.
        - Per le altre categorie, se sono presenti due palle vengono valutate distanza e white_ratio
          per decidere quale etichettare come "solid" o "striped"; se c'è una sola palla, il tipo
          viene assegnato in base al white_ratio.
        Restituisce la lista delle palle finali con il ball type assegnato.
        """
        final_balls = []
        for category, ball_list in color_groups.items():
            # Ordina per distanza dal colore di riferimento (minore è migliore)
            ball_list_sorted = sorted(ball_list, key=lambda x: x[1])

            if category in ("white", "black"):
                chosen_ball, _, _ = ball_list_sorted[0]
                ball_type = "cue" if category == "white" else "eight"
                chosen_ball.set_type(ball_type)
                final_balls.append(chosen_ball)
                if len(ball_list_sorted) > 1:
                    print(f"Attenzione: rilevate più palle {category}; ne è stata mantenuta solo una come {ball_type}.")
            else:
                # Limita a massimo 2 palle per categoria
                ball_list_sorted = ball_list_sorted[:2]
                if len(ball_list_sorted) == 1:
                    ball_obj, _, wr = ball_list_sorted[0]
                    ball_obj.set_type("striped" if wr > 0.9 else "solid")
                    final_balls.append(ball_obj)
                    
                elif len(ball_list_sorted) == 2:
                    ball1, d1, wr1 = ball_list_sorted[0]
                    ball2, d2, wr2 = ball_list_sorted[1]
                    if d1 > d2 or wr1 > wr2:
                        ball1.set_type("striped")
                        ball2.set_type("solid")
                    else:
                        ball1.set_type("solid")
                        ball2.set_type("striped")
                    final_balls.extend([ball1, ball2])
        return final_balls

    @classmethod
    def assign_ball_types(cls, balls):
        """
        Funzione wrapper che raggruppa le palle per colore e assegna il ball type.
        Restituisce la lista delle palle finali con il ball type assegnato.
        """
        groups = cls.group_balls_by_color(balls)
        return cls.assign_types_from_groups(groups)
    

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

    def reset_balls(self):
        self.__near_balls = []

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
    def __init__(self, player1_pic_pos=None, player2_pic_pos=None):
        self.player1_pic_pos = player1_pic_pos
        self.player2_pic_pos = player2_pic_pos

        self.player_turn = 1
        self.player_white_ratio = [0.0, 0.0]
        self.player1_ball_type = "not assigned"


    def set_player_turn(self, player_turn):
        self.player_turn = player_turn
    

    def set_player_white_ratio(self,player, white_ratio):
        self.player_white_ratio[player-1] = white_ratio
        
    def set_player1_ball_type(self, ball_type):
        self.player1_ball_type = ball_type
    
    def read_player_turn(self, squares):
        squares= sorted(squares, key=lambda item: item[1], reverse=True)
        squares = squares[:2]
        pos_brighter_square = squares[0][0].x
        if len(squares) > 1:
            pos_second_square = squares[1][0].x
            self.player_turn = 1 if pos_brighter_square < pos_second_square else 2
            #print(f"Luminosità: {squares[0][1]} {squares[1][1]}")
            #print(f"Posizione: {squares[0][0].x} {squares[1][0].x}")
        else:
            
            if squares[0][0].x <= self.player2_pic_pos:
                self.player_turn = 1
            else:
                self.player_turn = 2       
                    

    def assign_player1_ball_type(self, players_balls, final_balls  = None):
        players_balls = [players_balls[0], players_balls[len(players_balls) - 1]]

        #print(f"turno giocatore: {self.player_turn}")
        detected_left_wr = players_balls[0].white_ratio
        detected_right_wr = players_balls[1].white_ratio
        if detected_left_wr == 0.0 and detected_right_wr == 0.0:
            return
        
        if self.player_white_ratio[0] != 0 and self.player_turn == 1 and detected_left_wr > 0.0:
            self.player_white_ratio[0] = detected_left_wr
            print(f"Assegnato {detected_left_wr}")

        elif self.player_white_ratio[1] != 0 and  self.player_turn == 2 and detected_right_wr > 0.0:
            self.player_white_ratio[1] = detected_right_wr
            print(f"Assegnato {detected_right_wr}")


        if self.player1_ball_type == "not assigned" and all(ratio > 0.0 for ratio in self.player_white_ratio):
            self.player1_ball_type = "striped" if detected_left_wr > detected_right_wr else "solid"
            print(f"Tipo di palla assegnato: {self.player1_ball_type}")
            return
        
        if self.player1_ball_type != "not assigned":
            at_least_one_ball_left = any(ball.get_type() == self.player1_ball_type for ball in final_balls)
            if not at_least_one_ball_left:
                self.player1_ball_type = "eight"

    

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

def calculate_shot_angle(cue_ball, target, pocket):
    """
    Calcola l'angolo (in gradi) tra il vettore cue_ball->target e target->pocket.
    """
    t_c_vec = (target.get_x() - cue_ball.get_x(), target.get_y() - cue_ball.get_y())
    p_t_vec = (pocket.get_x() - target.get_x(), pocket.get_y() - target.get_y())
    
    # Prodotto scalare e magnitudini
    dot = t_c_vec[0] * p_t_vec[0] + t_c_vec[1] * p_t_vec[1]
    mag1 = math.sqrt(t_c_vec[0]**2 + t_c_vec[1]**2)
    mag2 = math.sqrt(p_t_vec[0]**2 + p_t_vec[1]**2)
    
    if mag1 * mag2 == 0:
        return 0
    
    # Calcola e converte l'angolo in gradi
    angle_rad = math.acos(dot / (mag1 * mag2))
    return math.degrees(angle_rad)

def is_in_between(cue_ball, target, other):
    """
    Verifica se la pallina 'other' si trova sul segmento tra la pallina bianca 'cue_ball'
    e la pallina target, considerando la soglia BALL_RADIUS.
    """
    # Vettore dal punto di partenza (cue_ball) al target
    dx = target.get_x() - cue_ball.get_x()
    dy = target.get_y() - cue_ball.get_y()
    segment_length = sqrt(dx**2 + dy**2)
    if segment_length == 0:
        return False

    # Calcola la proiezione del vettore (other - cue_ball) su (target - cue_ball)
    t = ((other.get_x() - cue_ball.get_x()) * dx + (other.get_y() - cue_ball.get_y()) * dy) / (segment_length**2)
    
    # Se la proiezione non cade sul segmento, non è in mezzo
    if not (0 <= t <= 1):
        return False

    # Punto di proiezione sul segmento
    proj_x = cue_ball.get_x() + t * dx
    proj_y = cue_ball.get_y() + t * dy

    # Distanza tra il punto proiettato e il centro della pallina 'other'
    dist = math.sqrt((other.get_x() - proj_x)**2 + (other.get_y() - proj_y)**2)
    
    return dist < max(other.get_r(), target.get_r())  # Considera il raggio della pallina


def is_path_clear(cue_ball, target, balls):
    """
    Verifica che non esista nessuna pallina diversa da quella bianca e dalla pallina target
    che si trovi tra la palla bianca e la pallina target.
    """

    for other in balls:
        if other == target:
            continue
        if cue_ball != None:
            if other == cue_ball:
                continue
            if is_in_between(cue_ball, target, other):
                return False
    return True

def calculate_shot_score(cue_ball, target, pocket, balls):
    """
    Calcola un punteggio per il tiro basato sui seguenti criteri:
      - Percorso bianca->target: bonus se libero, penalità altrimenti.
      - Percorso target->pocket: bonus se libero, penalità altrimenti.
      - Distanza target->pocket: bonus maggiore per distanze minori.
      - Angolo del tiro: bonus per angoli piccoli, penalità per angoli elevati.
    """
    score = 0
    
    # Verifica il percorso dalla bianca al target
    if is_path_clear(cue_ball, target, balls):
        score += 50
    
    # Verifica il percorso dal target alla pocket
    if is_path_clear(target, pocket, balls):
        score += 50

    pocket_distance = math.sqrt((target.get_x() - pocket.get_x())**2 + (target.get_y() - pocket.get_y())**2)
    if cue_ball is not None:
        cue_ball_b_distance = math.sqrt((cue_ball.get_x() - target.get_x())**2 + (cue_ball.get_y() - target.get_y())**2)
        score += max(0, 70 - int(cue_ball_b_distance/ 16))  # ad es., se la distanza è 60, aggiungiamo 40

    score += max(0, 100 - int(pocket_distance/ 16))  # ad es., se la distanza è 60, aggiungiamo 40

    # Bonus/penalità basati sull'angolo del tiro
    if cue_ball is not None:
        angle = calculate_shot_angle(cue_ball, target, pocket)
        if angle < 30:
            score += (30 - angle) * 2  # bonus proporzionale per angoli piccoli

    return score


def get_best_shot(cue_ball, balls, pockets, player_type="solid"):
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
            shot_score = calculate_shot_score(cue_ball, target, pocket, balls)
            # Debug: print(f"Tiro bianca->{target.get_id()}->pocket({pocket.get_x()}, {pocket.get_y()}): {shot_score:.2f}")
            if shot_score > best_score:
                best_score, best_target, best_pocket = shot_score, target, pocket


    return best_target, best_pocket, best_score


def get_target_aim(ball, pocket, cue_ball, balls):
    move_aim = None
    if ball and pocket:
        dx, dy = pocket.get_x() - ball.get_x(), pocket.get_y() - ball.get_y()
        distance = np.sqrt(dx**2 + dy**2)
        if distance != 0:
            # Vettore unitario dalla target ball alla pocket
            ux = dx / distance
            uy = dy / distance
            # La ghost ball si posiziona "dietro" la target ball, nella direzione opposta alla pocket,
            # a una distanza pari al diametro della pallina.
            ghost_x = ball.get_x() - int(ux * ball.get_r())
            ghost_y = ball.get_y() - int(uy * ball.get_r())
            move_aim = (ghost_x, ghost_y)
            
            # (Opzionale) Verifica che il percorso dalla cue ball alla ghost ball sia libero:
            ghost_dummy = Ball()
            ghost_dummy.set_x(ghost_x)
            ghost_dummy.set_y(ghost_y)
            ghost_dummy.set_r(ball.get_r())

            if not is_path_clear(cue_ball, ghost_dummy, balls):
                print("Percorso bianca -> ghost non libero!")
    
    return move_aim


def get_best_pair_to_shoot(balls: list, pockets: list, player_type="solid", current_ghost_ball= None):
    """
    Valuta per ogni pallina target (del tipo indicato) il tiro verso ciascuna pocket.
    Restituisce:
      - best_ball: la pallina target migliore;
      - best_pocket: la pocket verso cui indirizzare il tiro;
      - ghost_position: le coordinate (x, y) della ghost ball, ovvero
          il punto in cui la bianca deve impattare la target ball affinché,
          dopo il contatto, la target ball segua la direzione verso la pocket.
          
    La ghost ball viene calcolata come:
       ghost_position = target_center - unit_vector(target -> pocket) * BALL_DIAMETER
    Inoltre, potresti (opzionalmente) verificare che il percorso bianca -> ghost_position sia libero.
    """
    cue_ball = next((b for b in balls if b.get_type() == "cue"), None)
    
    if cue_ball is None:
        print("Attenzione: palla bianca non trovata!")
    
    best_ball, best_pocket, max_score = None, None, -float('inf')

    print(f"Player type: {player_type}")

    for ball in balls:
        b_type = ball.get_type()
        if b_type == "cue":
            continue
        
        # Considera solo le palline del tipo specificato
        if player_type != "not assigned" and b_type != player_type:
            continue
        if player_type == "not assigned" and b_type == "eight":
            continue
        
        best_curr_pocket, curr_score = None, -float('inf')
        
        for pkt in pockets:
            shot_score = calculate_shot_score(cue_ball, ball, pkt, balls)
            if shot_score > curr_score:
                curr_score, best_curr_pocket = shot_score, pkt
        
                
        if best_curr_pocket and curr_score > max_score:
            best_ball, best_pocket, max_score = ball, best_curr_pocket, curr_score
    
    
    move_aim = get_target_aim(best_ball, best_pocket, cue_ball, balls)
    
    return best_ball, best_pocket, move_aim