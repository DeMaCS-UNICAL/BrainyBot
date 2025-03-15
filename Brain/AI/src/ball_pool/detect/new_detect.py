import os

import re
import cv2
import numpy as np
import math
from matplotlib import pyplot as plt
import sys 
from AI.src.ball_pool.constants import SPRITE_PATH,SRC_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.input_game_object import Circle, Container, Rectangle
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.stack import Stack
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.dlvsolution.helpers import BPoolColor, Color, Ball, Pocket, MoveAndShoot, GameOver


class MatchingBallPool:

    # Parametri relativi al campo (se necessari per ulteriori controlli)
    X_MIN = 446
    Y_MIN = 169
    X_MAX = 2067
    Y_MAX = 1073

    # Parametri per la rilevazione delle palline
    BALLS_MIN_DIST = 1
    BALLS_MIN_RADIUS = 20
    BALLS_MAX_RADIUS = 25
    PARAM1 = 17   # Soglia per Canny (palline)
    PARAM2 = 23   # Soglia per HoughCircles (palline)

    # Parametri per la rilevazione dei pocket (buche) tramite rilevamento dei cerchi
    POCKETS_MIN_DIST = 400        # Distanza minima tra le buche
    POCKETS_MIN_RADIUS = 33       # Raggio minimo in pixel per i pocket
    POCKETS_MAX_RADIUS = 50
    POCKET_PARAM1 = 50            # Soglia per Canny (pocket)
    POCKET_PARAM2 = 90            # Soglia per HoughCircles (pocket)

    STICK_COORDS = 221, 348, 221, 887
    #dimensioni del mio schermo 2400x1077
    #Calibrerò meglio le costanti 

    def __init__(self, screenshot_path, debug=False, validation=False, iteration=0):
        self.screenshot = screenshot_path
        self.debug = debug
        self.validation = validation
        self.iteration = iteration
        self.image = None
        self.__gray = None
        self.__output = None
        self.__ball_chart = None
        self.detection_result = None
        self.__balls: list = []
        self.__pockets: list = []  # Ora i pocket verranno rilevati via circle detection
        self.img_width = None

        self.table_area = MatchingBallPool.X_MIN, MatchingBallPool.Y_MIN, MatchingBallPool.X_MAX, MatchingBallPool.Y_MAX 

        # Recupera la configurazione dal file config
        self.canny_threshold, self.proportion_tolerance, self.size_tolerance = self.retrieve_config()
        
        self.canny_threshold = self.adjust_threshold(iteration)
        

    def adjust_threshold(self, iteration):
        if iteration == 0:
            return self.canny_threshold
        return self.canny_threshold + iteration * 10

    def retrieve_config(self):
        with open(os.path.join(SRC_PATH, "config"), "r") as f:
            x = f.read()
        canny_threshold = int(re.search("CANNY_THRESHOLD=([^\n]+)", x, flags=re.M).group(1))
        # Anche se non usiamo template per i pocket, manteniamo la configurazione per eventuali usi futuri
        proportion_tolerance = (
            float(re.search("POCKET_PROPORTION_TOLERANCE=([^\n]+)", x, flags=re.M).group(1))
            if re.search("POCKET_PROPORTION_TOLERANCE=([^\n]+)", x, flags=re.M)
            else 0.1
        )
        size_tolerance = (
            float(re.search("POCKET_SIZE_TOLERANCE=([^\n]+)", x, flags=re.M).group(1))
            if re.search("POCKET_SIZE_TOLERANCE=([^\n]+)", x, flags=re.M)
            else 0.1
        )
        return canny_threshold, proportion_tolerance, size_tolerance


    def get_balls_chart(self):
        vision_output = self.vision()
        # In questo caso vision_output è una tupla: (lista di palline, lista di pocket)
        if len(vision_output["balls"]) == 0:
            return None
        return self.abstraction(vision_output)

    def vision(self):
        #dichiarato ma mai usato 
        self.finder = ObjectsFinder(self.screenshot, debug=self.debug, threshold=0.8, validation=self.validation)

        self.image = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot))
        self.full_image = self.image.copy()  # conserva l'immagine completa per la visualizzazione
        
        if self.debug and self.validation is None:
            plt.imshow(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
            plt.title("Screenshot")
            plt.show()
        
        # Carica la versione in scala di grigi e applica pre-elaborazione
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot), gray=True)
        self.__gray = cv2.GaussianBlur(self.__gray, (5, 5), 0)
        self.__gray = cv2.equalizeHist(self.__gray)
        
        # Se è definita una ROI (table_area), creiamo delle versioni per il rilevamento,
        # ma non modifichiamo self.image (che rimane la full image)
        if self.table_area is not None:
            x, y, w, h = self.table_area
    
        # Salviamo self.__output come immagine completa per la visualizzazione finale
        self.__output = self.image.copy()
        self.img_width = self.image.shape[1]


        player_squares = self.find_squares(area=(x,y,w,h))

        target_ball = self.finder.detect_target_ball(
            Circle(17, 100, 23,
                   (x,y,w,h)
                   )
        )
        
        aim_line = None
        self.tx, self.ty, self.tr = None, None,None
        if target_ball != None:
            self.tx, self.ty, self.tr = target_ball #target_ball_center=(tx, ty, tr)

        #pocket_circles = self.find_pocket_pool_houghCircles(area=(x,y,w,h))
        pocket_circles = self.finder._find_pockets_pool_contour(
            Circle(self.POCKETS_MIN_RADIUS, 40, self.POCKETS_MAX_RADIUS+2,
                   (x,y,w,h),
                   )
        )

        ball_circles = self.finder._find_balls_pool_contour(
            Circle(self.BALLS_MIN_RADIUS-1, 100, self.BALLS_MAX_RADIUS+2,
                   (x,y,w,h),
                   (self.tx, self.ty, self.tr) if target_ball != None else None,
                   )
        )

        # Assegniamo per riferimento interno
        self.__balls = ball_circles
        self.__pockets = pocket_circles
        self.__target_balls = target_ball
        self.__player_squares = player_squares
        
        """if self.__player1_turn:
            print("Player 1 turn")
        else:
            print("Player 2 turn")"""

        print(f"{len(pocket_circles)} Pockets")
        print(f"{target_ball} Target balls")
        print(f"{len(ball_circles)} Balls")
        #print(f"{len(aim_line) if aim_line != None else None} Aim line")


        return {"balls": ball_circles, "pockets": pocket_circles}
    
   
    def find_squares(self, area=None):
        squares = self.finder.detect_square_boxes()
        if area is not None:
            x_min, y_min, x_max, y_max = area 
            squares = [sq for sq in squares if x_min <= sq[0].x <= x_max and sq[0].y <= y_min]
            
        if squares is not None and len(squares) >= 2:
            print(f"len find squares {len(squares)}")
            # Ordina la lista in base al clear_count (indice 1 della tupla), decrescente
            squares= sorted(squares, key=lambda item: item[1], reverse=True)
            brighter_square_x = squares[0][0].x
            second_square_x = squares[1][0].x

            self.__player1_turn = brighter_square_x < second_square_x
        
        for sq in squares:
            print(f"Square {sq[0].x} {sq[0].y} {sq[1]}")

        return squares
    
    def extract_ball_roi(self, ball_obj, scale=1.4):
        """
        Data una palla (ball_obj) con centro (x, y) e raggio r,
        estrae il ROI dalla self.image. 'scale' serve ad aumentare il raggio per includere un margine.
        Restituisce il ROI come numpy array oppure None se le coordinate non sono valide.
        """
        cx, cy, r = ball_obj.get_x(), ball_obj.get_y(), ball_obj.get_r()
        margin = int(r * scale)
        x1 = max(0, cx - margin)
        y1 = max(0, cy - margin)
        x2 = min(self.image.shape[1], cx + margin)
        y2 = min(self.image.shape[0], cy + margin)
        # Se il ROI è vuoto, restituisci None
        #print(f"ROI: ({x1}, {y1}) - ({x2}, {y2})")
        if x2 <= x1 or y2 <= y1:
            #print("Empty ROI")
            return None
        #print(f"Self.image : {self.image}")
        return x1, y1, x2, y2

    
    def detect_direction_line(self, roi_coords, r, ball_x, ball_y):
        """
        Cerca di rilevare una linea interna (ad es. la linea di direzione) all'interno dell'ROI,
        che sia formata da pixel bianchi.
        La funzione:
        - Converte l'ROI in scala di grigi se necessario
        - Crea una maschera per i pixel bianchi (valori > 200)
        - Applica Canny per il rilevamento dei bordi
        - Utilizza HoughLinesP per individuare segmenti lineari
        - Per ogni linea candidata, verifica se lungo la linea prevalgono pixel bianchi
        - Se viene trovata una linea con lunghezza >= 0.8 * r, la restituisce come tuple (x1, y1, x2, y2)
        Restituisce None se non viene trovata una linea adeguata.
        """
        x1, y1, x2, y2 = roi_coords
        roi = self.image

        # Converte in scala di grigi se necessario
        if len(roi.shape) == 3:
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray_roi = roi.copy()
        
        # Crea una maschera dei pixel "bianchi" (valori > 200)
        _, white_mask = cv2.threshold(gray_roi, 200, 255, cv2.THRESH_BINARY)

        # Applica Canny per rilevare i bordi sull'immagine in scala di grigi
        edges = cv2.Canny(gray_roi, 50, 150, apertureSize=3)

        # Individua segmenti lineari con HoughLinesP
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, 
                                minLineLength=int(1), maxLineGap=5)
        
        if lines is not None:
            best_line = None
            best_length = 0
            for line in lines:
                x_start, y_start, x_end, y_end = line[0]
                line_length = np.sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2)
                
                # Crea una maschera per la linea per verificare l'intensità dei pixel
                mask_line = np.zeros_like(gray_roi, dtype=np.uint8)
                cv2.line(mask_line, (x_start, y_start), (x_end, y_end), 255, thickness=3)
                mean_white = cv2.mean(white_mask, mask=mask_line)[0]
                
                # Se la linea è formata prevalentemente da pixel bianchi (media >= 200)
                # o ha lunghezza maggiore del candidato precedente, allora la selezioniamo
                if not (x1 <= x_start <= x2 and
                        y1 <= y_start <= y2):
                    continue

                """print(f"x1: {x1} y1: {y1}-")
                print(f"x:  {x}   y: {y} -- ")"""
                if mean_white >= 200 or line_length > best_length:
                    
                    best_length = line_length
                    best_line = (x_start, y_start, x_end, y_end)
                    
            
            # Restituisce la linea se la lunghezza è adeguata
            if best_line is not None:
                return best_line

        return None

    def find_perpendicular_lines(self, raw_aim_lines, angle_tolerance=10):
        """
        Data una lista di raw_aim_lines (ogni elemento è una tupla:
        (ball_center_x, ball_center_y, direction_line, len_line)),
        trova due linee che siano perpendicolari (angolo ~90° ± angle_tolerance).
        Restituisce una tupla contenente le due raw_aim_lines se trovate, altrimenti None.
        """
        import math
        n = len(raw_aim_lines)
        if n < 2:
            return None
        aim_lines = []

        for i in range(n):
            for j in range(i+1, n):
                _, _, line1, _ = raw_aim_lines[i]
                _, _, line2, _ = raw_aim_lines[j]
                x1, y1, x2, y2 = line1
                x3, y3, x4, y4 = line2

                # Calcola i vettori direzionali
                v1 = (x2 - x1, y2 - y1)
                v2 = (x4 - x3, y4 - y3)
                norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
                norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
                if norm1 == 0 or norm2 == 0:
                    continue

                # Calcola l'angolo in gradi tra i due vettori
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                cos_angle = dot / (norm1 * norm2)
                # Per evitare errori numerici
                cos_angle = max(-1.0, min(1.0, cos_angle))
                angle = math.degrees(math.acos(cos_angle))
                if abs(angle - 90) <= angle_tolerance:
                    aim_lines.append(raw_aim_lines[i])
                    aim_lines.append(raw_aim_lines[j])
        return aim_lines


    
    def abstract_balls(self, circles):
        if circles is None:
            return []
        raw_balls = []
        # Per ogni cerchio rilevato, crea una Ball assegnandole il BPoolColor
        for c in circles:
            x = c.x
            y = c.y
            r = c.radius
            dominant_col = c.color  # patch dell'immagine della pallina
            white_ratio : float= c.white_ratio 
            

            #print(f"x: {x} y: {y} r: {r} color: {patch}")
            bpColor = BPoolColor.get_color(dominant_col, white_ratio)

            ball_obj = Ball(bpColor)
            ball_obj.set_x(x)
            ball_obj.set_y(y)
            ball_obj.set_r(r)
            raw_balls.append(ball_obj)
        
        # Raggruppa le palle per categoria di colore e assegna il tipo ("piena" o "mezza")
        final_balls = BPoolColor.assign_ball_types(raw_balls)
        return final_balls

    def abstract_pockets(self, circles):
        """
        Converte i cerchi (x, y, r) in oggetti Pocket.
        Esegue eventuale NMS e filtraggio dei duplicati.
        """
        if circles is None:
            return []
        #circles = np.uint16(np.around(circles))
        raw_pockets = []
        for c in circles:
            # Se vuoi, controlla range di r
            # if r < self.POCKETS_MIN_RADIUS or r > self.POCKETS_MAX_RADIUS:
            #     continue

            p = Pocket(c.x, c.y)
            p.set_r(c.radius)
            raw_pockets.append(p)

        return raw_pockets
    

    def abstraction(self, vision_output, reset=True) -> ElementsStacks:
        """if reset:
            Ball.reset()
            Pocket.reset()
            Color.reset()
            """
        result = {"balls": [], "aim_lines": [] , "pockets": []}

        # 1) Creazione e filtraggio palline
        ball_circles = vision_output["balls"]
        final_balls = self.abstract_balls(ball_circles)
        result["balls"] = final_balls

        aim_line = self.finder.compute_target_direction(all_balls=ball_circles,
                                                        target_ball=(self.tx, self.ty, self.tr), 
                                                        area=(self.X_MIN, self.Y_MIN, self.X_MAX, self.Y_MAX),
                                                        )
        
        result["aim_line"] = aim_line

        #result["aim_lines"] = self.__aim_lines

        # 2) Creazione e filtraggio buche
        pocket_circles = vision_output["pockets"]
        final_pockets = self.abstract_pockets(pocket_circles)
        result["pockets"] = final_pockets

        # Salviamo il risultato in un attributo interno
        self.__result = result

        self.__balls = result["balls"]
        self.__pockets = result["pockets"]
        self.__aim_line = result["aim_line"]

        if self.validation is None and self.debug:
            print(f"Found {len(result['balls'])} balls and {len(result['pockets'])} pockets")
            self.__show_result()  # Nessun parametro

        return result

    

    def __show_result(self):
        scale_factor = 1.0
        width = int(self.image.shape[1] * scale_factor)
        height = int(self.image.shape[0] * scale_factor)
        dim = (width, height)

        img_copy = self.__output.copy()
        

        # Disegna il rettangolo dell'area (in rosso)
        cv2.rectangle(img_copy, (self.X_MIN, self.Y_MIN), (self.X_MAX, self.Y_MAX), (255, 0, 0), 5)

        # Disegna le palline (in verde)
        for ball in self.__balls:
            x, y, r = ball.get_x(), ball.get_y(), ball.get_r()
            cv2.circle(img_copy, (x, y), r, (0, 255, 0), 3)
            cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
            # Testo con bordo nero e testo verde
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Disegna i pocket (in giallo)
        for pocket in self.__pockets:
            x, y, r = pocket.get_x(), pocket.get_y(), pocket.get_r()
            cv2.circle(img_copy, (x, y), r, (0, 255, 255), 3)
            cv2.circle(img_copy, (x, y), 4, (0, 0, 0), 1)
            cv2.putText(img_copy, f"P({x}, {y}) {r}", (x + r, y + r),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(img_copy, f"P({x}, {y}) {r}", (x + r, y + r),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
        """if len(self.__stick) != 0:
            for rect in self.__stick:
                x = rect.x
                y = rect.y
                width = rect.width
                heigth = rect.heigth

                cv2.rectangle(img_copy, (x, y), (x+width, y+heigth), (255, 255, 255), 5)
        """

        # Supponiamo che self.__aim_line sia una lista di tuple, in cui ogni tupla è:
        # (ball_center_x, ball_center_y, direction_vector, len_line)
        # dove direction_vector è una tupla (dx, dy) già normalizzata.

        if self.__aim_line is not None:
            print(f"Aim lines show {len(self.__aim_line)}")
            if isinstance(self.__aim_line, tuple):
                aim_lines = [self.__aim_line]
            else:
                aim_lines = self.__aim_line

            print(f"Aim lines show {len(aim_lines)}")
            print(f"Aim lines details: {aim_lines}")

            # Iteriamo su ogni linea e disegniamola
            for line in aim_lines:
                # Ci aspettiamo che ogni linea sia una tupla (x1, y1, x2, y2)
                if len(line) == 4:
                    x1, y1, x2, y2 = line
                    # Disegna la linea in viola (BGR: (255, 0, 255))
                    cv2.line(img_copy, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 255), 3)
                else:
                    print("Formato non riconosciuto per la linea:", line)


        x, y, r = self.__target_balls

        cv2.circle(img_copy, (x, y), r, (60,20,220), 4)
        cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
        # Testo con bordo nero e testo verde
        cv2.putText(img_copy, f"({x}, {y}) {r}", (x - 200, y -50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
        cv2.putText(img_copy, f"({x}, {y}) {r}", (x - 200, y - 50 ),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (60,20,220), 2)
        
        #purple bgr 
        x_above, y_above, x_below, y_below = self.STICK_COORDS

        cv2.line(img_copy, (x_above, y_above), (x_below, y_below), (255, 0, 255), 3)
        cv2.putText(img_copy, f"Stick", (x_above, y_above),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        #purple rgb  (255,0,255)
        #red rgb (0,0,255)
        print(f"{len(self.__player_squares)} Player square")

        if self.__player_squares is not None and len(self.__player_squares) != 0:
            player_cont = 0
            for rect, clear_count in self.__player_squares:
                x = rect.x
                y = rect.y
                width = rect.width
                heigth = rect.heigth
                if player_cont == 0:
                    cv2.rectangle(img_copy, (x, y), (x+width, y+heigth), (0, 0, 255), 5)
                else:
                    cv2.rectangle(img_copy, (x, y), (x+width, y+heigth), (255,0,255), 5)
                player_cont+=1
            player_cont = 0

        # Ridimensionamento per la visualizzazione
        resized_input = cv2.cvtColor(cv2.resize(self.image, dim, interpolation=cv2.INTER_LINEAR), cv2.COLOR_BGR2RGB)
        resized_gray = cv2.cvtColor(cv2.resize(self.__gray, dim, interpolation=cv2.INTER_LINEAR), cv2.COLOR_GRAY2RGB)
        resized_output = cv2.cvtColor(cv2.resize(img_copy, dim, interpolation=cv2.INTER_LINEAR), cv2.COLOR_BGR2RGB)

        # Mostra i risultati
        fig, axes = plt.subplots(3, 1, figsize=(8, 18))

        axes[0].imshow(resized_input)
        axes[0].set_title("Input Image")
        axes[0].axis("off")

        axes[1].imshow(resized_gray)
        axes[1].set_title("Gray Image")
        axes[1].axis("off")

        axes[2].imshow(resized_output)
        axes[2].set_title("Detection Output")
        axes[2].axis("off")

        plt.tight_layout()
        plt.show()
