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
    X_MIN = 419
    Y_MIN = 263
    X_MAX = 1864
    Y_MAX = 985

    BALLS_MIN_DIST = 1         # distanza minima tra i cerchi
    BALLS_MIN_RADIUS = 13      # raggio minimo in pixel
    BALLS_MAX_RADIUS = 25       # raggio massimo in pixel
    PARAM1 = 70          # soglia per Canny
    PARAM2 = 20           # soglia per HoughCircles

    POCKETS_MIN_DIST = 300        # distanza minima tra buche
    POCKETS_MIN_RADIUS = 37      # raggio minimo in pixel
    POCKETS_MAX_RADIUS = 45       # raggio massimo in pixel

    POCKET_PARAM1 = 28
    POCKET_PARAM2 = 26

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
        pocket_circles = self.detect_pockets_circles(self.__gray)

        # Assegniamo per riferimento interno
        self.__balls = ball_circles
        self.__pockets = pocket_circles

        return {"balls": ball_circles, "pockets": pocket_circles}
    
    def detect_balls_circles(self, detection_gray):
        """
        Rileva i cerchi (palline) sfruttando il metodo find() dell'ObjectsFinder.
        Per fare ciò, creiamo un oggetto Circle con i parametri necessari e lo passiamo a finder.find().
        """
        # In questo esempio usiamo self.canny_threshold e BALLS_MIN_RADIUS definiti in MatchingBallPool
        # per configurare il rilevamento. Se necessario, puoi adattare o calcolare altri parametri,
        # ad esempio in base alle dimensioni dell'immagine.
        circle_search_info = Circle(canny_threshold=self.canny_threshold, min_radius=self.BALLS_MIN_RADIUS)
        
        # Chiamando finder.find() con l'oggetto Circle verrà invocato il metodo _find_circles all'interno di ObjectsFinder
        balls = self.finder.find(circle_search_info)
        
        return balls


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

    
    def filter_duplicate_circles(self, circles, CIRCLE_MIN_DISTANCE=4, type="ball"):
        """
        Se due cerchi sono troppo vicini, elimina i duplicati.
        """
        filtered = []
        for obj in circles:
            if type == "ball":
                x, y, r = obj.get_x(), obj.get_y(), obj.get_r()
            else:  # pocket
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




    def non_max_suppression(self, circles, overlapThresh=0.5, type="ball"):
        """
        Esegue la NMS (Non-Maxima Suppression) su una lista di cerchi convertiti in bounding box.
        """
        if len(circles) == 0:
            return []
        # Creiamo le bounding box (x1, y1, x2, y2)
        rects = []
        if type == "ball":
            for obj in circles:
                (x, y, r) = (obj.get_x(), obj.get_y(), obj.get_r())
                rects.append([x - r, y - r, x + r, y + r])
        elif type == "pocket":
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


    def abstraction(self, vision_output) -> dict:
        """
        Converte i cerchi rilevati (vision_output) in oggetti Ball/Pocket.
        Applica anche eventuale NMS, filtraggio, ecc.
        """
        result = {"balls": [], "pockets": []}

        # 1) Creazione e filtraggio palline
        ball_circles = vision_output["balls"]
        final_balls = self.clean_balls(ball_circles)
        result["balls"] = final_balls

        # 2) Creazione e filtraggio buche
        pocket_circles = vision_output["pockets"]
        final_pockets = self.clean_pockets(pocket_circles)
        result["pockets"] = final_pockets

        # Salviamo il risultato in un attributo interno
        self.__result = result

        if self.validation is None and self.debug:
            print(f"Found {len(result['balls'])} balls and {len(result['pockets'])} pockets")
            self.__show_result()  # Nessun parametro

        return result

    
    def clean_balls(self, circles):
        """
        Converte i cerchi (x, y, r) in oggetti Ball, estraendo il colore da un piccolo patch.
        Esegue anche NMS e filtraggio dei duplicati.
        """
        if circles is None:
            return []
        circles = np.uint16(np.around(circles))
        raw_balls = []
        patch_size = 5
        half_patch = patch_size // 2

        # Creiamo le Ball
        for (x, y, r) in circles[0]:
            # Evita raggi fuori range, se vuoi
            if r < self.BALLS_MIN_RADIUS or r > self.BALLS_MAX_RADIUS:
                continue

            # Prendiamo un patch attorno al centro per determinare il colore
            x1 = max(0, x - half_patch)
            y1 = max(0, y - half_patch)
            x2 = x + half_patch + 1
            y2 = y + half_patch + 1
            patch = self.image[y1:y2, x1:x2]

            color_obj = Color.get_color(patch)
            ball_obj = Ball(color_obj)
            ball_obj.set_x(x)
            ball_obj.set_y(y)
            ball_obj.set_r(r)
            raw_balls.append(ball_obj)

        # Applica NMS e filtra duplicati
        nms_balls = self.non_max_suppression(raw_balls, overlapThresh=0.5, type="ball")
        filtered_balls = self.filter_duplicate_circles(nms_balls, CIRCLE_MIN_DISTANCE=30, type="ball")

        print(f"Detected {len(filtered_balls)} balls (after NMS & filtering)")
        return filtered_balls

    def clean_pockets(self, circles):
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
            p = Pocket(x, y)
            p.set_r(r)
            raw_pockets.append(p)

        nms_pockets = self.non_max_suppression(raw_pockets, overlapThresh=0.5, type="pocket")
        filtered_pockets = self.filter_duplicate_circles(
            nms_pockets, CIRCLE_MIN_DISTANCE=self.POCKETS_MIN_DIST, type="pocket"
        )
        print(f"Detected {len(filtered_pockets)} pockets (after NMS & filtering)")
        return filtered_pockets



    def get_image(self):
        return self.image

    def __show_result(self):
        # Recupera i risultati salvati
        balls = self.__result["balls"]
        pockets = self.__result["pockets"]

        # Se la ROI è definita, usiamo l'immagine completa e aggiungiamo l'offset
        if self.table_area is not None:
            x_roi, y_roi, x_max, y_max = self.table_area
            display_img = self.full_image.copy()

            # Disegna le palline, compensando le coordinate della ROI
            for ball in balls:
                bx = ball.get_x() + x_roi
                by = ball.get_y() + y_roi
                r = ball.get_r()
                cv2.circle(display_img, (bx, by), r, (0, 255, 0), 2)
                cv2.circle(display_img, (bx, by), 2, (0, 0, 255), 3)
                cv2.putText(display_img, f"({bx}, {by})", (bx + 10, by),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Disegna il rettangolo della ROI
            cv2.rectangle(display_img, (x_roi, y_roi), (x_max, y_max), (50,205,50), 3)
        else:
            # Se non è definita una ROI, usa l'immagine pre-elaborata
            display_img = self.__output.copy()
            for ball in balls:
                x = ball.get_x()
                y = ball.get_y()
                r = ball.get_r()
                cv2.circle(display_img, (x, y), r, (0, 255, 0), 2)
                cv2.circle(display_img, (x, y), 2, (0, 0, 255), 3)
                cv2.putText(display_img, f"({x}, {y})", (x + 10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
        # Disegna le buche, compensando l'offset della ROI
        for pocket in pockets:
            px = pocket.get_x() #+ x_roi
            py = pocket.get_y()# + y_roi
            pr = pocket.get_r()
            cv2.circle(display_img, (px, py), pr, (0, 255, 255), 2)
            cv2.circle(display_img, (px, py), 2, (0, 0, 255), 3)
            cv2.putText(display_img, f"({px}, {py}) {pr}", (px + 10, py),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Imposta la finestra di visualizzazione in modalità full screen
        cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Result", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Aggiunge il callback del mouse per visualizzare le coordinate in tempo reale
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
            if key == 27:  # ESC per uscire
                break
        cv2.destroyAllWindows()
