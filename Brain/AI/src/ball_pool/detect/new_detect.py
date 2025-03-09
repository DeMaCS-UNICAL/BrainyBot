import os

import re
import cv2
import numpy as np
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



"""I parametri param1 e param2 nella funzione cv2.HoughCircles() controllano specifici aspetti del rilevamento dei cerchi:

param1: Corrisponde alla soglia superiore per il rilevatore di bordi di Canny interno all'algoritmo. 
In pratica, determina la sensibilità nel riconoscere i bordi nell'immagine. Valori più alti richiedono bordi più definiti.
param2: È la soglia per il rilevamento del centro dei cerchi. Un valore più basso rileverà più cerchi (inclusi quelli falsi),
mentre un valore più alto sarà più selettivo e rileverà solo cerchi con evidenza più forte. Questo è uno dei parametri più influenti.

Ecco come funzionano nel contesto dell'algoritmo Hough Circles:

param1 influenza quanto l'algoritmo è sensibile ai bordi dell'immagine
param2 determina quanti "voti" deve ricevere un cerchio candidato per essere considerato valido

Regolando questi valori, puoi:

Aumentare param1 se l'immagine ha contrasto basso
Diminuire param2 se non vengono rilevati abbastanza cerchi
Aumentare param2 se vengono rilevati troppi falsi cerchi
"""
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
        # Non carichiamo più template per i pocket, poiché li rileviamo via cerchi

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



        
        # 4) Rilevamento cerchi delle palline
        #ball_circles = self.detect_balls_circles((x,y,w,h))
        ball_circles = self.finder._find_balls_pool_contour(
            Circle(self.BALLS_MIN_RADIUS-1, 100, self.BALLS_MAX_RADIUS+2,
                   (x,y,w,h))
        )
        
        #pocket_circles = self.find_pocket_pool_houghCircles(area=(x,y,w,h))
        pocket_circles = self.finder._find_pockets_pool_contour(
            Circle(self.POCKETS_MIN_RADIUS, 40, self.POCKETS_MAX_RADIUS+2,
                   (x,y,w,h)
                   )
        )
        target_ball = self.finder.detect_target_ball(
            Circle(17, 100, 23,
                   (x,y,w,h))
        )

        self.__aim_lines = []
        #self.__stick = stick

        # Assegniamo per riferimento interno
        self.__balls = ball_circles
        self.__pockets = pocket_circles
        self.__target_balls = target_ball

        print(f"{len(pocket_circles)} pockets")
        print(f"{len(target_ball)} target balls")
        print(f"{len(ball_circles)} balls")


        return {"balls": ball_circles, "pockets": pocket_circles}
    
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


    def check_white_circle_with_black_border(self, roi_coords, r):
        """
        Verifica se l'ROI (definito dalle coordinate roi_coords) presenta un interno bianco e un bordo nero.
        'r' è il raggio stimato della palla (usato per definire la maschera).
        Restituisce True se la condizione è verificata, False altrimenti.
        """
        x1, y1, x2, y2 = roi_coords
        roi = self.__gray
        
        h, w = roi.shape
        
        # Assumiamo che la palla sia centrata nel ROI
        center_x, center_y = w // 2, h // 2

        # Crea la maschera per il cerchio completo
        mask = np.zeros(roi.shape, dtype=np.uint8)
        cv2.circle(mask, (center_x, center_y), r, 255, -1)
        
        # Maschera interna, riducendo il raggio per escludere il bordo
        inner_mask = np.zeros(roi.shape, dtype=np.uint8)
        cv2.circle(inner_mask, (center_x, center_y), max(r - 5, 0), 255, -1)
        
        # La maschera del bordo
        border_mask = cv2.subtract(mask, inner_mask)
        
        mean_inside = cv2.mean(roi, mask=mask)[0]
        mean_border = cv2.mean(roi, mask=border_mask)[0]
        
        # Regola le soglie in base all'immagine e all'illuminazione
        if mean_inside <= 200 and mean_border >= 50:
            #print(f"White circle with black border: {mean_inside} - {mean_border}")
            return True
        return False
    
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



    def find_ball_pool_houghCircles(self, area):
        """
        Esegue HoughCircles per rilevare i cerchi (palline).
        Ritorna una struttura circles (x, y, r).
        """
        x,y,w,h = area if area != None else 0
        
        blurred = cv2.GaussianBlur(self.__gray, (5, 5), 0)  
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

        circles = cv2.HoughCircles(
            closed,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=self.BALLS_MIN_DIST,
            param1=self.PARAM1,
            param2=self.PARAM2,
            minRadius=self.BALLS_MIN_RADIUS,
            maxRadius=self.BALLS_MAX_RADIUS
        )
        filtered_circ = []
        for c in circles:
            i = c.get_x()
            j = c.get_y()
            r = c.get_r()
            if (x<= i <= w and
                    y <= j <= h):
                continue
            else:
                filtered_circ.append()

        return circles

    
    def abstract_balls(self, circles):
        if circles is None:
            return []
        #circles = np.uint16(np.around(circles))
        raw_balls = []
        raw_aim_lines = []

        for c in circles:
            x = c.x
            y = c.y
            r = c.radius
            color = c.color
            bpColor = BPoolColor(color)
            ball_obj = Ball(bpColor)
            # Converti in coordinate globali
            ball_obj.set_x(x)
            ball_obj.set_y(y)
            ball_obj.set_r(r)

            """# Estrai il ROI completo della palla (con margine)
            roi_coords = self.extract_ball_roi(ball_obj)
            if roi_coords is not None:
                # Controlla che il ROI mostri un interno bianco e bordi neri
                if self.check_white_circle_with_black_border(roi_coords, r):
                    # Rileva la linea interna (direction_line) in coordinate globali
                    direction_line = self.detect_direction_line(roi_coords, r, x, y)
                    if direction_line is not None:
                        ball_obj.get_color().set_ball_type("cue aim")
                        line_x1, line_y1, line_x2, line_y2 = direction_line
                        len_line = np.sqrt((line_x2 - line_x1) ** 2 + (line_y2 - line_y1) ** 2)
                        raw_aim_lines.append((x, y, direction_line, len_line))
                        print(f"Found line at ({x}, {y}) {direction_line} len {len_line}")
            else:
                print(f"ROI vuoto per la palla in ({x}, {y}) con raggio {r}")
            """
            raw_balls.append(ball_obj)

        # Applica NMS e filtra duplicati
        #nms_balls = self.non_max_suppression(raw_balls, overlapThresh=0.5)
        #filtered_balls = self.filter_duplicate_circles(nms_balls, CIRCLE_MIN_DISTANCE=self.BALLS_MIN_DIST)

        """# Chiama la funzione per trovare due linee perpendicolari tra loro (già definita altrove)
        perp_lines = self.find_perpendicular_lines(raw_aim_lines)
        if perp_lines is not None:
            print("Found perpendicular lines:",)
            reset = 0
            for x,y, dir_line, len_line in perp_lines:
                print(f"Found PERP line at ({x}, {y}) {direction_line} len {len_line}")
                reset += 1
                if reset == 2:
                    print("\r")
                    reset = 0
        else:
            print("No perpendicular lines found.")"""

        return raw_balls

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
        result["aim_lines"] = self.__aim_lines

        # 2) Creazione e filtraggio buche
        pocket_circles = vision_output["pockets"]
        final_pockets = self.abstract_pockets(pocket_circles)
        result["pockets"] = final_pockets

        # Salviamo il risultato in un attributo interno
        self.__result = result

        self.__balls = result["balls"]
        self.__pockets = result["pockets"]
        self.__aim_lines = result["aim_lines"]

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

        

        # Disegna le aim_lines (in viola)
        """if self.__aim_lines != None:
            print(f"Aim lines show {len(self.__aim_lines)}")
            for x1, y1, x2, y2 in self.__aim_lines:
                # Ogni aim_line è definita come (ball_center_x, ball_center_y, direction_line, len_line)
                
                cv2.line(img_copy, (x1, y1), (x2, y2), (255, 0, 255), 3)"""

        # Disegna le linee perpendicolari (se presenti) in rosso
        if hasattr(self, '__perp_lines') and self.__perp_lines is not None:
            for aim_line in self.__perp_lines:
                _, _, direction_line, _ = aim_line
                x1_line, y1_line, x2_line, y2_line = direction_line
                cv2.line(img_copy, (x1_line, y1_line), (x2_line, y2_line), (0, 0, 255), 3)

        for target in self.__target_balls:
            x, y, r = target

            cv2.circle(img_copy, (x, y), r, (60,20,220), 4)
            cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
            # Testo con bordo nero e testo verde
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (60,20,220), 2)
            

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
