import os

import re
import cv2
import numpy as np
from matplotlib import pyplot as plt
import sys 
from AI.src.ball_pool.constants import SPRITE_PATH,SRC_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.input_game_object import Circle, Container
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
    X_MIN = 320
    Y_MIN = 179
    X_MAX = 1953
    Y_MAX = 1069

    # Parametri per la rilevazione delle palline
    BALLS_MIN_DIST = 1
    BALLS_MIN_RADIUS = 20
    BALLS_MAX_RADIUS = 25
    PARAM1 = 17   # Soglia per Canny (palline)
    PARAM2 = 23   # Soglia per HoughCircles (palline)

    # Parametri per la rilevazione dei pocket (buche) tramite rilevamento dei cerchi
    POCKETS_MIN_DIST = 400        # Distanza minima tra le buche
    POCKETS_MIN_RADIUS = 34       # Raggio minimo in pixel per i pocket
    POCKETS_MAX_RADIUS = 50       # Raggio massimo in pixel per i pocket
    POCKET_PARAM1 = 28            # Soglia per Canny (pocket)
    POCKET_PARAM2 = 26            # Soglia per HoughCircles (pocket)

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
        print(f"Adjust thres {self.canny_threshold}")
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
            detection_gray = self.__gray[y:h, x:w]
            detection_image = self.image[y:h, x:x]
        else:
            detection_gray = self.__gray
            detection_image = self.image
        
        # Salviamo self.__output come immagine completa per la visualizzazione finale
        self.__output = self.image.copy()
        self.img_width = self.image.shape[1]
        
        # 4) Rilevamento cerchi delle palline
        ball_circles = self.detect_balls_circles(detection_gray)

        # 5) Rilevamento cerchi delle buche (puoi scegliere se usare detection_gray/detection_image o l'immagine intera)
        pocket_circles = self.detect_pockets_circles(detection_gray)

        # Assegniamo per riferimento interno
        self.__balls = ball_circles
        self.__pockets = pocket_circles

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
        roi = self.__gray[y1:y2, x1:x2]
        
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
    
    def detect_direction_line(self, roi_coords, r):
        """
        Cerca di rilevare una linea interna (ad es. la linea di direzione) all'interno dell'ROI.
        La funzione:
        - Converte l'ROI in scala di grigi (se necessario)
        - Applica il rilevamento dei bordi con Canny
        - Utilizza HoughLinesP per individuare segmenti lineari
        - Se trova una linea con lunghezza >= 0.8 * r, la restituisce come tuple (x1, y1, x2, y2)
        Restituisce None se non viene trovata una linea adeguata.
        """
        x1, y1, x2, y2 = roi_coords
        roi = self.image[y1:y2, x1:x2]
        
        # Crea una maschera dei pixel "bianchi" (valori > 200)
        _, white_mask = cv2.threshold(roi, 200, 255, cv2.THRESH_BINARY)

        # Applica Canny per rilevare i bordi
        edges = cv2.Canny(roi, 50, 150, apertureSize=3)
        
        # Utilizza HoughLinesP per individuare segmenti di linea
        # minLineLength è impostato in modo che la linea debba essere lunga almeno l'80% del raggio della palla
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=int(r * 0.9), maxLineGap=5)
        
        if lines is not None:
            best_line = None
            best_length = 0
            for line in lines:
                x_start, y_start, x_end, y_end = line[0]
                line_length = np.sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2)
                # Se troviamo una linea più lunga, la consideriamo come candidata
                if line_length > best_length:
                    best_length = line_length
                    best_line = (x_start, y_start, x_end, y_end)
            
            # Se la linea trovata ha una lunghezza adeguata, restituiscila
            if best_line is not None and best_length >= r :
                return best_line

        return None



    def detect_balls_circles(self, detection_gray):
        """
        Esegue HoughCircles per rilevare i cerchi (palline).
        Ritorna una struttura circles (x, y, r).
        """
        # Pre-elaborazione specifica (se necessaria)
        blurred = cv2.GaussianBlur(detection_gray, (5, 5), 0)
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

        return circles

    def detect_pockets_circles(self, detection_gray):
        """
        Esegue HoughCircles per rilevare i cerchi (buche).
        Ritorna una struttura circles (x, y, r).
        """
        blurred = cv2.GaussianBlur(detection_gray, (5, 5), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

        circles = cv2.HoughCircles(
            closed,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=self.POCKETS_MIN_DIST,
            param1=self.POCKET_PARAM1,
            param2=self.POCKET_PARAM2,
            minRadius=self.POCKETS_MIN_RADIUS,
            maxRadius=self.POCKETS_MAX_RADIUS
        )
        h, w = detection_gray.shape[:2]
        valid_circles = []
        for (cx, cy, r) in circles[0]:
            if 0 <= cx <= w+70 and 0 <= cy <= h+70:
                valid_circles.append((cx, cy, r))

        circles = np.array([valid_circles], dtype=np.uint16)
        return circles

    def filter_duplicate_circles(self, circles, CIRCLE_MIN_DISTANCE=4):
        """
        Se due cerchi sono troppo vicini, elimina i duplicati.
        """
        filtered = []
        for obj in circles:
            x, y, r = obj.get_x(), obj.get_y(), obj.get_r()
        
            duplicate = False
            for f_obj in filtered:
                fx, fy, fr = f_obj.get_x(), f_obj.get_y(), f_obj.get_r()
                dist = np.sqrt((float(x) - float(fx)) ** 2 + (float(y) - float(fy)) ** 2)

                if dist < CIRCLE_MIN_DISTANCE:
                    duplicate = True
                    break
            if not duplicate:
                filtered.append(obj)
        return filtered

    def non_max_suppression(self, circles, overlapThresh=0.5):
        """
        Esegue la NMS (Non-Maxima Suppression) su una lista di cerchi convertiti in bounding box.
        """
        if len(circles) == 0:
            return []
        # Creiamo le bounding box (x1, y1, x2, y2)
        rects = []
       
        for obj in circles:
            (x, y, r) = (obj.get_x(), obj.get_y(), obj.get_r())
            rects.append([x - r, y - r, x + r, y + r])

        rects = np.array(rects)
        pick = []
        x1 = rects[:, 0]
        y1 = rects[:, 1]
        x2 = rects[:, 2]
        y2 = rects[:, 3]
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)

        while len(idxs) > 0:
            last = idxs[-1]
            pick.append(last)
            suppress = [len(idxs) - 1]
            for pos in range(0, len(idxs) - 1):
                i = idxs[pos]
                xx1 = max(x1[last], x1[i])
                yy1 = max(y1[last], y1[i])
                xx2 = min(x2[last], x2[i])
                yy2 = min(y2[last], y2[i])
                w = max(0, xx2 - xx1 + 1)
                h = max(0, yy2 - yy1 + 1)
                overlap = float(w * h) / area[i]
                if overlap > overlapThresh:
                    suppress.append(pos)
            idxs = np.delete(idxs, suppress)

        # Ritorna gli oggetti filtrati
        filtered = [circles[i] for i in pick]
        return filtered
    
    """def detect_balls(self) -> list:
        height = self.image.shape[0]
        minRadius = int(self.BALLS_MIN_RADIUS)
        maxRadius = int(self.BALLS_MAX_RADIUS)
        minDist = int(self.BALLS_MIN_DIST)
        # Utilizza il finder per individuare le palline tramite il rilevamento dei cerchi
        print(f"Balls canny {self.canny_threshold}")
        self.__balls = self.finder.find(
            Circle(
            min_radius=minRadius, 
            max_radius=maxRadius,
            canny_threshold=1
            ),
            area= (self.X_MIN, self.Y_MIN, self.X_MAX, self.Y_MAX)
            )
        
        # Filtra le palline per mantenere solo quelle sufficientemente distanti
        #self.__balls = self.filter_by_distance(self.__balls, self.BALLS_MIN_DIST)
        
        return self.__balls

    def detect_pockets(self) -> list:
        # Rileva i pocket in maniera simile alle palline, utilizzando i parametri specifici per i pocket
        height = self.image.shape[0]
        minRadius = int(self.POCKETS_MIN_RADIUS)
        maxRadius = int(self.POCKETS_MAX_RADIUS)
        minDist = int(self.POCKETS_MIN_DIST)

        self.__pockets = self.finder.find(
            Circle(
                min_radius=minRadius,
                max_radius=maxRadius,
                canny_threshold=3,
            ),
                area= (self.X_MIN, self.Y_MIN, self.X_MAX, self.Y_MAX)

        )
        return self.__pockets"""
    
    def abstract_balls(self, circles):
        if circles is None:
            return []
        circles = np.uint16(np.around(circles))
        raw_balls = []
        patch_size = 5
        half_patch = patch_size // 2

        for (x, y, r) in circles[0]:
            if not (self.BALLS_MIN_RADIUS <= r <= self.BALLS_MAX_RADIUS):
                continue

            # Estrai un patch piccolo per il colore (già in uso)
            x1 = max(0, x - half_patch)
            y1 = max(0, y - half_patch)
            x2 = x + half_patch + 1
            y2 = y + half_patch + 1

            patch = self.image[y1:y2, x1:x2]
            color_obj = BPoolColor.get_color(patch)
            ball_obj = Ball(color_obj)
            x += self.X_MIN
            y += self.Y_MIN
            ball_obj.set_x(x)
            ball_obj.set_y(y)
            ball_obj.set_r(r)

            # Estrai il ROI completo della palla (con margine)
            roi_coords = self.extract_ball_roi(ball_obj)
            if roi_coords is not None:
                # Step 1: Controlla che il ROI mostri un interno bianco e bordi neri
                if self.check_white_circle_with_black_border(roi_coords, r):
                    # Step 2: Rileva la linea interna
                    direction_line = self.detect_direction_line(roi_coords, r)
                    if direction_line is not None:
                        ball_obj.get_color().set_ball_type("cue aim")
                        line_x1, line_y1, line_x2, line_y2 = direction_line
                        #ball_obj.direction_line = direction_line  # memorizza la linea
                        len_line = np.sqrt((line_x2 - line_x1) ** 2 + (line_y2 - line_y1) ** 2)

                        print(f"Found cue aim ball at ({x}, {y}) with line {direction_line} len {len_line}")
            else:
                print(f"ROI vuoto per la palla in ({x}, {y}) con raggio {r}")

            raw_balls.append(ball_obj)

        # Applica NMS e filtra duplicati
        nms_balls = self.non_max_suppression(raw_balls, overlapThresh=0.5)
        filtered_balls = self.filter_duplicate_circles(nms_balls, CIRCLE_MIN_DISTANCE=self.BALLS_MIN_DIST)
        print(f"Rilevate {len(filtered_balls)} palle (dopo NMS e filtraggio)")
        return filtered_balls

    def abstract_pockets(self, circles):
        """
        Converte i cerchi (x, y, r) in oggetti Pocket.
        Esegue eventuale NMS e filtraggio dei duplicati.
        """
        if circles is None:
            return []
        circles = np.uint16(np.around(circles))
        raw_pockets = []
        for (x, y, r) in circles[0]:
            # Se vuoi, controlla range di r
            # if r < self.POCKETS_MIN_RADIUS or r > self.POCKETS_MAX_RADIUS:
            #     continue
            p = Pocket(x + self.X_MIN, y + self.Y_MIN)
            p.set_r(r)
            raw_pockets.append(p)

        nms_pockets = self.non_max_suppression(raw_pockets, overlapThresh=0.5)
        filtered_pockets = self.filter_duplicate_circles(
            nms_pockets, CIRCLE_MIN_DISTANCE=self.POCKETS_MIN_DIST
        )
        print(f"Detected {len(filtered_pockets)} pockets (after NMS & filtering)")
        return filtered_pockets
    

    def abstraction(self, vision_output, reset=True) -> ElementsStacks:
        """if reset:
            Ball.reset()
            Pocket.reset()
            Color.reset()
            """
        result = {"balls": [], "pockets": []}

        # 1) Creazione e filtraggio palline
        ball_circles = vision_output["balls"]
        final_balls = self.abstract_balls(ball_circles)
        result["balls"] = final_balls

        # 2) Creazione e filtraggio buche
        pocket_circles = vision_output["pockets"]
        final_pockets = self.abstract_pockets(pocket_circles)
        result["pockets"] = final_pockets

        # Salviamo il risultato in un attributo interno
        self.__result = result

        self.__balls = result["balls"]
        self.__pockets = result["pockets"]

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

        print(f"Balls show {len(self.__balls)}")
        print(f"Pockets show {len(self.__pockets)}")

        # Disegna il rettangolo dell'area
        cv2.rectangle(img_copy, (self.X_MIN, self.Y_MIN), (self.X_MAX, self.Y_MAX), (255, 0, 0), 5)  # Rosso

        # Disegna le palline (verdi)
        for ball in self.__balls:
            x, y, r = ball.get_x(), ball.get_y(), ball.get_r()
            cv2.circle(img_copy, (x, y), r, (0, 255, 0), 3)
            cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
            # Testo con bordo nero
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)  # Bordo nero
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  # Testo verde

        # Disegna i pocket (gialli)
        for pocket in self.__pockets:
            x, y, r = pocket.get_x(), pocket.get_y(), pocket.get_r()
            cv2.circle(img_copy, (x, y), r, (0, 255, 255), 3)
            cv2.circle(img_copy, (x, y), 4, (0, 0, 0), 1)
            # Testo con bordo nero
            cv2.putText(img_copy, f"P({x}, {y}) {r}", (x + r, y+r), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)  # Bordo nero
            cv2.putText(img_copy, f"P({x}, {y}) {r}", (x + r, y+r), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  # Testo giallo

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




