import os

import re
import cv2
import numpy as np
from matplotlib import pyplot as plt
import sys 
from AI.src.ball_pool.constants import SPRITE_PATH,SRC_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.stack import Stack
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.dlvsolution.helpers import  Color, Ball, Pocket, MoveAndShoot, GameOver


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

    BALLS_DISTANCE_RATIO = 1  # rapporto usato per filtrare le palline
    BALL_RADIUS_RATIO = 20

    #Valori range campo
    X_MIN = 535
    Y_MIN = 266
    X_MAX = 1440
    Y_MAX = 712

    MIN_DIST = 1         # distanza minima tra i cerchi
    MIN_RADIUS = 14       # raggio minimo in pixel
    MAX_RADIUS = 25       # raggio massimo in pixel
    PARAM1 = 70          # soglia per Canny
    PARAM2 = 20           # soglia per HoughCircles



    def __init__(self, screenshot_path, debug=True, validation=None, iteration=0, table_area=None):
        self.screenshot = screenshot_path
        self.debug = debug
        self.validation = validation
        self.iteration = iteration
        self.image = None
        self.__gray = None
        self.__output = None
        self.detection_result = None
        self.__pocketTemplates = {}
        self.__balls = []
        self.__pockets = []
        self.img_width = None
        # Questi valori ora non vengono più letti da config per le palline,
        # ma potresti comunque usarli per le pocket se necessario.
        self.canny_threshold = self.PARAM1  # In questo caso, usiamo PARAM1 come soglia per Canny
        # Imposta la ROI se fornita. Altrimenti, table_area rimane None.
        self.table_area = MatchingBallPool.X_MIN, MatchingBallPool.Y_MIN, MatchingBallPool.X_MAX, MatchingBallPool.Y_MAX if table_area is not None else None
        

        
        """for file in os.listdir(SPRITE_PATH): # indica la cartella in cui cercare i file
            if file.endswith('.png') or file.endswith('.jpg'):
                fullname = os.path.join(SPRITE_PATH,file)
                if not validation: # se non è in modalità di validazione
                    print(f"Found field sprite {fullname} (testingg)") # stampa il nome del file
                img = getImg(fullname,gray=True)
                self.__pocketTemplates[fullname]  = img # crea un dizionario con il nome del file e l'immagine in scala di grigi"""
        
    
    def adjust_threshold(self,iteration):
        if iteration == 0:
            return self.canny_threshold
        return self.canny_threshold + iteration*10
    
    def retrieve_config(self):
        with open(os.path.join(SRC_PATH, "config"), "r") as f:
            x = f.read()
        canny_threshold = int(re.search("CANNY_THRESHOLD=([^\n]+)", x, flags=re.M).group(1))
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
        # Per pool, restituisce un dizionario con le liste di palline e pocket
        vision_output = self.vision()
        if len(vision_output["balls"]) == 0:
            return None
        return self.abstraction(vision_output)
    
    
    def vision(self):
        # Inizializza la visione: carica l'immagine e crea la versione in scala di grigi
        self.finder = ObjectsFinder(self.screenshot, debug=self.debug, threshold=0.8, validation=self.validation)
        # Carica l'immagine completa e salvala
        self.image = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot))
        if self.image is None:
            raise ValueError("Immagine non trovata: " + self.screenshot)
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
            detection_gray = self.__gray[y:y+h, x:x+w]
            detection_image = self.image[y:y+h, x:x+w]
        else:
            detection_gray = self.__gray
            detection_image = self.image
        
        # Salviamo self.__output come immagine completa per la visualizzazione finale
        self.__output = self.image.copy()
        self.img_width = self.image.shape[1]
        
        # Usa la sub-immagine per il rilevamento delle palline
        self.__balls = self.detect_balls(detection_gray, detection_image)
        self.__pockets = self.detect_pockets()  # Se implementato, qui puoi decidere se applicare la ROI anche per le pocket
        return {"balls": self.__balls, "pockets": self.__pockets}

    def detect_balls(self, detection_gray, detection_image) -> list:
        # Pre-elaborazione: applica blur e chiusura morfologica sul detection_gray
        blurred = cv2.GaussianBlur(detection_gray, (5, 5), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

        circles = cv2.HoughCircles(closed,
                                cv2.HOUGH_GRADIENT,
                                dp=1,
                                minDist=self.MIN_DIST,
                                param1=self.PARAM1,
                                param2=self.PARAM2,
                                minRadius=self.MIN_RADIUS,
                                maxRadius=self.MAX_RADIUS)
        raw_balls = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                x, y, r = int(i[0]), int(i[1]), int(i[2])
                if r < self.MIN_RADIUS or r > self.MAX_RADIUS:
                    continue
                # Estrai il campione colore dalla detection_image (coordinate relative alla ROI)
                color_sample = detection_image[y, x].tolist()  # formato BGR
                raw_balls.append([x, y, r, color_sample])
        
        # Applica la Non-Maximum Suppression (NMS) e filtra i duplicati
        nms_balls = self.non_max_suppression(raw_balls, overlapThresh=0.5)
        filtered_balls = self.filter_duplicate_balls(nms_balls, min_distance=2)
        # Se è definita una ROI, le coordinate rimangono relative al crop; 
        # questo verrà gestito in __show_result aggiungendo l'offset.
        print(f"Detected {len(filtered_balls)} balls")
        for ball in filtered_balls:
            x, y, r, _ = ball
            print(f"x: {x}, y: {y}, r: {r}")
        return filtered_balls


    
    def filter_duplicate_balls(self, balls, min_distance=4):
        filtered = []
        for ball in balls:
            x, y, r, c = ball
            duplicate = False
            for fb in filtered:
                fx, fy, fr, fc = fb
                if np.sqrt((x - fx)**2 + (y - fy)**2) < min_distance:
                    duplicate = True
                    break
            if not duplicate:
                filtered.append(ball)
        return filtered




    def non_max_suppression(self, circles, overlapThresh=0.5):
        if len(circles) == 0:
            return []
        rects = []
        for (x, y, r, _) in circles:
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
        filtered = [circles[i] for i in pick]
        return filtered

    
    def apply_roi(self, balls):
        if self.table_area is None:
            return balls
        x_roi, y_roi, w_roi, h_roi = self.table_area
        filtered = []
        for ball in balls:
            x, y, r, c = ball
            if x >= x_roi and x <= x_roi + w_roi and y >= y_roi and y <= y_roi + h_roi:
                filtered.append(ball)
        return filtered


    def detect_pockets(self) -> list:
        detected_pockets = []
        # Utilizza il template matching per rilevare le pocket
        for name, template in self.__pocketTemplates.items():
            if self.validation is None:
                print(f"Trying to detect pocket using template {name}")
            actual_matches, coordinates = self.finder.detect_container(template, self.proportion_tolerance, self.size_tolerance)
            print(f"Detected {len(actual_matches)} pockets using template {name}")
            if len(actual_matches) > 0:
                for (x, y) in coordinates:
                    pocket = Pocket(x, y)
                    detected_pockets.append(pocket)
        return detected_pockets

    def abstraction(self, vision_output) -> dict:
        result = {"balls": [], "pockets": []}
        for ball in vision_output["balls"]:
            if len(ball) < 4:
                continue
            x, y, r, bgr = ball[0], ball[1], ball[2], ball[3]
            ball_obj = Ball(Color.get_color(bgr))
            ball_obj.set_x(x)
            ball_obj.set_y(y)
            ball_obj.set_r(r)
            #print(f"x: {ball_obj.get_x()}, y: {ball_obj.get_y()}, r: {ball_obj.get_r()}")
            result["balls"].append(ball_obj)

        for pocket in vision_output["pockets"]:
            result["pockets"].append(pocket)
        if self.validation is None and self.debug:
            print(f"Found {len(result['balls'])} balls and {len(result['pockets'])} pockets")
            balls_count = len(result["balls"])
            pockets_count = len(result["pockets"])
            print(f"Found {balls_count} balls and {pockets_count} pockets")
            for pocket in result["pockets"]:
                cv2.rectangle(self.__output, (pocket.get_x() - 10, pocket.get_y() - 10),
                              (pocket.get_x() + 10, pocket.get_y() + 10), (0, 255, 0), 3)
            self.__show_result()
        return result

    def get_image(self):
        return self.image

    def __show_result(self):
        # Se è definita la ROI, usiamo l'immagine completa e aggiungiamo l'offset
        if self.table_area is not None:
            offset_x, offset_y, _, _ = self.table_area
            display_img = self.full_image.copy()
            for ball in self.__balls:
                x, y, r, _ = ball
                # Convertiamo le coordinate rilevate (relativamente al crop) in coordinate globali
                x_full = x + offset_x
                y_full = y + offset_y
                cv2.circle(display_img, (x_full, y_full), r, (0, 255, 0), 2)
                cv2.circle(display_img, (x_full, y_full), 2, (0, 0, 255), 3)
                cv2.putText(display_img, f"({x_full}, {y_full})", (x_full + 10, y_full),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            for pocket in self.__pockets:
                x_p = pocket.get_x() + offset_x
                y_p = pocket.get_y() + offset_y
                cv2.rectangle(display_img, (x_p - 10, y_p - 10),
                            (x_p + 10, y_p + 10), (255, 0, 0), 2)
            # Evidenzia la ROI sull'immagine completa
            x_roi, y_roi, w_roi, h_roi = self.table_area
            cv2.rectangle(display_img, (x_roi, y_roi), (x_roi + w_roi, y_roi + h_roi), (0, 0, 255), 3)
        else:
            display_img = self.__output.copy()
            for ball in self.__balls:
                x, y, r, _ = ball
                cv2.circle(display_img, (x, y), r, (0, 255, 0), 2)
                cv2.circle(display_img, (x, y), 2, (0, 0, 255), 3)
                cv2.putText(display_img, f"({x}, {y})", (x + 10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            for pocket in self.__pockets:
                cv2.rectangle(display_img, (pocket.get_x()-10, pocket.get_y()-10),
                            (pocket.get_x()+10, pocket.get_y()+10), (255, 0, 0), 2)
        
        # Aggiungi callback del mouse per visualizzare le coordinate in tempo reale
        cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Result", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        mouse_data = {"pos": None}
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_MOUSEMOVE:
                param["pos"] = (x, y)
        cv2.setMouseCallback("Result", mouse_callback, mouse_data)
        
        while True:
            disp = display_img.copy()
            if mouse_data["pos"] is not None:
                mx, my = mouse_data["pos"]
                cv2.circle(disp, (mx, my), 5, (0, 255, 255), -1)
                cv2.putText(disp, f"X: {mx}, Y: {my}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow("Result", disp)
            key = cv2.waitKey(20) & 0xFF
            if key == 27:
                break
        cv2.destroyAllWindows()



