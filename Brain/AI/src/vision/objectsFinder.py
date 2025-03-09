import os
import sys
import cv2
import numpy as np
import mahotas
import pytesseract as ts
import multiprocessing
from time import time
from matplotlib import pyplot as plt

from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.input_game_object import *
from AI.src.vision.output_game_object import *
from AI.src.abstraction.objectsMatrix import *
import math


class ObjectsFinder:
    def __init__(self, screenshot, color=None, debug=False, threshold=0.8,validation=False ):
        #
        # Use Matrix2.png for testing
        #
        self.methods = {TemplateMatch:self._template_matching,
                        Circle:self._find_circles,
                        Container:self._detect_container,
                        Rectangle:self._find_rectangles,
                        TextRectangle:self._find_text_or_number}

        self.validation=validation
        self.__img_matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=color) 
        self.__output = self.__img_matrix.copy()  
        self.__blurred = cv2.medianBlur(self.__img_matrix,7)  # Used to find the color of the balls
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=cv2.COLOR_BGR2GRAY)  # Used to find the balls
        self.__generic_object_methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__generic_object_method = eval(self.__generic_object_methodName)
        self.__threshold=threshold
        #self.__graph = CandyGraph(difference)
        
        self.__hough_circles_method_name = 'cv2.HOUGH_GRADIENT'
        self.__hough_circles_method = eval(self.__hough_circles_method_name)
        self.debug=debug

    def get_image(self):
        return self.__img_matrix

    
    def get_image_width(self):
        return self.__img_matrix.shape[1]
    
    def get_image_height(self):
        return self.__img_matrix.shape[0]
    
    def find_most_similar_image_template(self,target_image, image_list):
        best_match_image = None
        best_match_value = -float('inf')
        idx=-1
        for i in range(len(image_list)):
            result = cv2.matchTemplate(target_image, image_list[i], self.__generic_object_method)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val>0.5 and max_val > best_match_value:
                best_match_value = max_val
                best_match_image = image_list[i]
                idx=i
        return idx

    def process_cell(self, args):
        i, j, matrix, tm_imgs, tm_labels, width, height = args
        x = matrix.get_cell(i, j).x
        y = matrix.get_cell(i, j).y
        img = self.extract_subimage(self.__img_matrix, OutputRectangle(x-width//2, y-height//2, width, height))
        label_id = self.find_most_similar_image_template(img, tm_imgs)
        if label_id != -1:
            return OutputTemplateMatch(x, y,width, height, tm_labels[label_id], 1)
        else:
            return OutputTemplateMatch(x, y,width, height, "", 1)

    def process_matrix_parallel(self,matrix, tm_imgs, tm_labels, width, height):
        objects_found = []
        tasks = [
            (i, j, matrix, tm_imgs, tm_labels, width, height)
            for i in range(matrix.num_row)
            for j in range(len(matrix.matrix[i]))
        ]
        num_processes = min(multiprocessing.cpu_count()//2, len(tasks)) 
        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.map(self.process_cell, tasks)

        objects_found.extend(results)
        return objects_found

    def find_from_existing_matrix(self,search_info:SimplifiedTemplateMatch,matrix:ObjectMatrix):
        width = search_info.width
        heigth = search_info.heigth
        objects_found=[]
        tm_labels = []
        tm_imgs = []
        cont=0
        for key in search_info.templates:
            tm_labels.append(key)
            tm_imgs.append(search_info.templates[key])
            cont+=1
        objects_found = self.process_matrix_parallel(matrix,tm_imgs,tm_labels,width,heigth)
        return objects_found


    def find(self, search_info):
        return self.methods[type(search_info)](search_info)

    def _template_matching(self,search_info:TemplateMatch):
        if search_info.find_all:
                return self.__find_all(search_info)
        return self.find_one_among(search_info)
    
    def _find_rectangles(self,search_info:Rectangle):
            if search_info.hierarchy:
                return self.__find_boxes_and_hierarchy()
            return self.__find_boxes()
    
    def _find_text_or_number(self,search_info:TextRectangle):
            if search_info.numeric:
                return self.__find_number(search_info)
            if search_info.dictionary!=None:
                return self.__find_text_from_dictionary(search_info)
            if search_info.regex!=None:
                return self.__find_text_from_regex(search_info)
            return self.__find_text(search_info)
            

    def template_matching_worker_process(self,elements:list,regmax,img):
        for (tm_name,tm_img,tm_threshold) in elements:
            return self.__find_matches(img,tm_name,tm_img,tm_threshold,regmax)     


    def extract_tm_info(self, search_info:TemplateMatch):
        img = self.__img_matrix.copy()
        if search_info.grayscale:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elements_to_find=search_info.templates
        thresholds = search_info.threshold_dictionary
        return img,elements_to_find,thresholds


    def find_one_among(self,  search_info:TemplateMatch) -> list:
        objects_found=[]
        img, elements_to_find,thresholds = self.extract_tm_info(search_info)
        for element in elements_to_find.keys():
            objects_found = self.__find_matches(img,element,elements_to_find[element],thresholds[element],search_info.regmax)
            if len(objects_found)>0:
                break
        return objects_found
    
    
    def process_template(self,args):
        element, template, threshold, regmax, img = args
        return self.template_matching_worker_process( [(element, template, threshold)], regmax, img
        )

    def __find_all(self, search_info: TemplateMatch) -> dict:
        # Estrai le informazioni necessarie
        img, elements_to_find, thresholds = self.extract_tm_info(search_info)
        
        # Prepara i dati come tuple (self, element, template, threshold, regmax, img)
        templates = [
            ( element, elements_to_find[element], thresholds[element], search_info.regmax, img)
            for element in elements_to_find.keys()
        ]
        
        # Usa un Pool per parallelizzare il lavoro sui template
        num_processes = min(multiprocessing.cpu_count()//2, len(templates))
        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.map(self.process_template, templates)
        
        # Raccogli tutti i risultati in una lista
        main_list = [item for sublist in results for item in sublist]
        return main_list

    def __find_matches(self, image,label, element_to_find,threshold, request_regmax=True) -> list:
        
        objects_found=[]
        # execute template match
        res = cv2.matchTemplate(image, element_to_find, self.__generic_object_method)
        template_height, template_width = element_to_find.shape[:2]
        if request_regmax:
            regMax = mahotas.regmax(res)
            res = res * regMax
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            x, y = pt
            confidence = res[y, x]  # Extract the confidence value at the corresponding position
            objects_found.append(OutputTemplateMatch(x+template_width//2,y+template_height//2,template_width,template_height,label,confidence))
        return objects_found


    def is_circle(self,contour, circularity_threshold=0.5):
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        
        if perimeter == 0:
            return False
        circularity = 4 * 3.14159 * area / (perimeter * perimeter)
        
        return circularity >= circularity_threshold

    def _find_circles(self, search_info:Circle):
        canny_threshold = search_info.canny_threshold
        min_radius = search_info.min_radius
        gray = self.__gray
        # threshold
        #blurred_img = cv2.blur(gray,ksize=(5,5))
        canny = cv2.Canny(gray, canny_threshold,int(canny_threshold*3.5))
        contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        circles = [cnt for cnt in contours if self.is_circle(cnt)]
        if self.debug and not self.validation:
            canny = cv2.cvtColor(canny, cv2.COLOR_GRAY2RGB)
            canny2 = canny.copy()
            canny3 = canny.copy()
            cv2.drawContours(canny, contours, -1, (255, 0, 0), 1)
            plt.imshow(canny)
            plt.show()
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        balls = []
        if circles is not None:
            for circle in circles:
                (center),r = cv2.minEnclosingCircle(circle)
                if r<min_radius:
                    continue
                # get the color of pixel (x, y) form the blurred image
                x=int(center[0])
                y=int(center[1])
                r=int(r)
                color = np.array(self.__blurred[y,x])
                if self.debug and not self.validation:
                    print(f"Found ball:({x}, {y}): {color}")
                # draw the circle
                cv2.circle(self.__img_matrix, (x, y), r, (0, 255, 0), 2)
                #cv2.circle(self.__output, (x, y), 6, (0, 0, 0), 1)
                #cv2.circle(self.__blurred, (x, y), r, (0, 255, 0), 2)
                #cv2.circle(self.__blurred, (x, y), 6, (0, 0, 0), 1)
                cv2.putText(self.__img_matrix, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                balls.append(OutputCircle(x,y,r,color.tolist()))
            if self.debug and not self.validation:
                plt.imshow(cv2.cvtColor(self.__img_matrix,cv2.COLOR_BGR2RGB))
                plt.show()
                cv2.waitKey(0)
        return balls
    
    
    def extract_subimage(self, img,rectangle):
        return img[rectangle.y:rectangle.y+rectangle.heigth, rectangle.x:rectangle.x+rectangle.width]

  
    def _detect_container(self,search_info:Container):
        template=search_info.template
        rotate=search_info.rotate
        proportion_tolerance=search_info.proportion_tolerance
        size_tolerance=search_info.size_tolerance
        # Convert to grayscale and apply edge detection
        tem_gray = template.copy()
        gray = self.__gray.copy()
        #edges = cv2.Canny(gray, 50, 150)
        ret, edges = cv2.threshold(gray, 127, 255, 0)
        #tem_edges = cv2.Canny(tem_gray, 50, 150)
        ret, tem_edges = cv2.threshold(tem_gray, 127, 255, 0)
        # Find contours
        tem_contours, _ = cv2.findContours(tem_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        tem_cnt = tem_contours[0]
        _,tem_axis,tem_a = cv2.fitEllipse(tem_cnt)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        containers = [cnt for cnt in contours if cv2.matchShapes(cnt,tem_cnt,3,0.0)<0.02]
        coordinates = []
        to_return=[]
        for i in range(len(containers)):
            (x,y),axis,cont_a = cv2.fitEllipse(containers[i])
            if not rotate and abs(tem_a+cont_a)%179>5: #the 2 contours are aligned
                    continue
            if proportion_tolerance!=0 and abs(axis[1]/axis[0]-tem_axis[1]/tem_axis[0])>tem_axis[1]/tem_axis[0]*proportion_tolerance:
                continue
            if size_tolerance!=0 and abs(axis[1]-tem_axis[1])>tem_axis[1]*size_tolerance:
                continue
            to_return.append(OutputContainer(x,y,containers[i]))

        return to_return
    
              
    def __find_boxes(self) -> list:
        contour = cv2.Canny(self.__img_matrix, 25, 80)
        contour = cv2.dilate(contour, None, iterations=1)
        contours, _ = cv2.findContours(contour, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        boxes = []
        for i in range(len(contours)):
            per = cv2.arcLength(contours[i], True)
            epsilon = 0.05 * per
            approx = cv2.approxPolyDP(contours[i], epsilon, True)
            
            # if the contour is not a rettangle or if it is too small, ignore it
            if len(approx) != 4 or cv2.isContourConvex(approx) == False or cv2.contourArea(approx) < 3000:
                continue
            x, y, w, h = cv2.boundingRect(approx)
            current_box= OutputRectangle(x,y,w,h)
            boxes.append(current_box)
        return boxes
    
    def __find_boxes_and_hierarchy(self):
        mat_contour = np.zeros((self.__img_matrix.shape[0], self.__img_matrix.shape[1]), dtype=np.uint8)
        boxes = self.__find_boxes() 
        for box in boxes:
            x, y, w, h = box.x,box.y,box.width,box.heigth
            cv2.rectangle(mat_contour, (x, y), (x + w, y + h), 255, thickness=1, lineType=cv2.LINE_AA)
        boxes, hierarchy = cv2.findContours(mat_contour, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return boxes, hierarchy[0]

    def __find_text(self, rectangle:OutputRectangle) -> str:
        img = self.extract_subimage(self.__img_matrix,rectangle).copy()
        elem = ts.image_to_string(img, config='--psm 8 --oem 3') 
        return elem if elem != '' else None

    def __find_number(self, search_info:TextRectangle) -> int:
        rectangle=search_info.rectangle
        img = self.extract_subimage(self.__img_matrix,rectangle).copy()
        # Upscale the image to improve the OCR if the image is too small
        if img.shape[0] < 150 or img.shape[1] < 150:
            img = cv2.resize(img, (round(img.shape[1]*1.5), round(img.shape[0]*1.5)))
        elem = ts.image_to_string(img, config='--psm 6 --oem 1 -c tessedit_char_whitelist=0123456789')
        if elem == '':
            elem = ts.image_to_string(img, config='--psm 7 --oem 1 -c tessedit_char_whitelist=0123456789')
        try:
            return int(elem)
        except:
            return None
    
    def __find_text_from_dictionary(self, search_info:TextRectangle) -> str:
        rectangle=search_info.rectangle
        dictionary_path = search_info.dictionary
        img = self.extract_subimage(self.__img_matrix,rectangle).copy()
        elem = ts.image_to_string(img, config='--psm 8 --oem 3 --user-words {}'.format(dictionary_path))
        return elem if elem != '' else None

    def __find_text_from_regex(self,search_info:TextRectangle) -> str:
        rectangle=search_info.rectangle
        regex = search_info.regex
        img = self.extract_subimage(self.__img_matrix,rectangle).copy()
        elem = ts.image_to_string(img, config='--psm 8 --oem 3')
        if regex.match(elem):
            return elem
        else:
            return None 
        

    def bp_is_circle(self,contour, circularity_threshold=0.65,area_threshold = None ):
        hull = cv2.convexHull(contour)
        area = cv2.contourArea(hull)
        perimeter = cv2.arcLength(hull, True)
        
        if area_threshold != None:
            if area < area_threshold:
                return False
        
        if perimeter == 0:
            return False
        circularity = 4 * 3.14159 * area / (perimeter * perimeter)
        
        return circularity >= circularity_threshold


    def _find_balls_pool_contour(self, search_info:Circle = None, area_threshold=50, circularity_threshold=0.24):
        
        gray = self.__gray
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
        # Thresholding adattivo per rilevare bordi e forme
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY_INV, 11, 2)
        
        # Trova i contorni
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        hierarchy = hierarchy[0]
        
        gray_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        balls = []
        if contours is not None:
            for i, cnt in enumerate(contours):
                area = cv2.contourArea(cnt)
                (center), r = cv2.minEnclosingCircle(cnt)                
                # Ottiene il colore del pixel al centro dalla versione già filtrata (o dalla immagine blurred se disponibile)
                x = int(center[0])
                y = int(center[1])
                r = int(r)
                    
                if search_info != None:
                    x_min, y_min, x_max, y_max = search_info.area
                    if not (x_min  <= x <= x_max and 
                            y_min +70 <= y <= y_max -70):
                        continue

                    if not (search_info.min_radius <= r <= search_info.max_radius):
                        #print("Scartata per radius")
                        continue
                
                circularity = area / (math.pi * r * r)
                if circularity < circularity_threshold:
                    continue
                
                # Controlla se non è un contorno esterno
                if hierarchy[i][3] == -1:  # Se non ha un genitore, è esterno
                    continue

                color = np.array(self.__blurred[y, x])
                if self.debug and not self.validation:
                    print(f"Found ball pool:({x}, {y}): {color}")
            
                balls.append(OutputCircle(x, y, r, color.tolist()))

        balls = self.filter_duplicate_circles(balls)
        return balls
    
    def _find_pockets_pool_contour(self, search_info:Circle):
            # Valori minimi di raggio, area e eventuale area di interesse
        min_radius = search_info.min_radius

        # 1. Pre-elaborazione: Conversione in grigio e Blur
        gray = self.__gray
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # 2. Adaptive Thresholding
        # Utilizza una dimensione del blocco (blockSize) più grande e un parametro costante maggiore
        # per enfatizzare le zone scure (tipiche delle buche)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 77, 27
        )
        # Puoi sperimentare: se 15,5 non funziona bene, prova ad aumentare il blockSize (es. 17 o 19)
        # o modificare il valore costante (5, 7, o 3)

        # 3. Operazione morfologica: Closing per “riempire” piccoli gap
        # Usa un kernel più piccolo per non unire troppo le aree adiacenti
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # 4. Estrazione dei contorni dalla maschera
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        pockets = []
        #print(f"Len pocket circles {len(contours)}")
        circles = [cnt for cnt in contours if self.bp_is_circle(cnt, circularity_threshold=0.35, area_threshold=70)]
        #circles = contours
        if circles is not None:
            for circle in circles:
                (center), r = cv2.minEnclosingCircle(circle)
                if r < min_radius:
                    continue

                if search_info.min_radius is not None:
                    max_radius = search_info.max_radius
                    if r > max_radius:
                        continue
                
                # Ottiene il colore del pixel al centro dalla versione già filtrata (o dalla immagine blurred se disponibile)
                x = int(center[0])
                y = int(center[1])
                r = int(r)

                if search_info.area != None:
                    x_min, y_min, x_max, y_max = search_info.area
                    if not (x_min <= x <= x_max and 
                            y_min <= y <= y_max):
                        #print("Scartata buca")
                        continue

                color = np.array(self.__blurred[y, x])
                    
                pockets.append(OutputCircle(x, y, r, color.tolist()))

            if self.debug and not self.validation:
                """plt.imshow(cv2.cvtColor(self.__img_matrix, cv2.COLOR_BGR2RGB))
                plt.show()
                cv2.waitKey(0)"""

        pockets = self.filter_duplicate_circles(pockets, CIRCLE_MIN_DISTANCE=700)
        return pockets
    
    def filter_duplicate_circles(self, circles, CIRCLE_MIN_DISTANCE=10):
        """
        Se due cerchi sono troppo vicini, elimina i duplicati.
        """
        filtered = []
        for obj in circles:
            x, y, r = obj.x, obj.y, obj.radius
        
            duplicate = False
            for f_obj in filtered:
                fx, fy, fr = f_obj.x, f_obj.y, f_obj.radius
                dist = np.sqrt((float(x) - float(fx)) ** 2 + (float(y) - float(fy)) ** 2)

                if dist < CIRCLE_MIN_DISTANCE or dist < r *0.7:
                    duplicate = True
                    break
            if not duplicate:
                filtered.append(obj)
        return filtered
    


    def detect_target_ball(self, 
                           search_info:Circle = None,
                       area_threshold=50, 
                       circularity_threshold=0.4,
                       border_intensity_threshold=25,   # soglia massima per il bordo (nero)
                       inner_intensity_threshold=105):  # soglia minima per il bianco
        """
        Rileva la palla mirino in un'immagine, caratterizzata da:
        - un contorno esterno (nero) sottile,
        - un interno (bianco).

        Il metodo sfrutta la gerarchia dei contorni per individuare contorni che possiedono
        un "figlio": il contorno esterno (nero) che racchiude un'area interna (bianca).

        Parametri:
        area_threshold: area minima del contorno esterno.
        circularity_threshold: rapporto minimo (area_contorno / area_cerchio inscritto) per considerare
                                la forma sufficientemente circolare.
        border_intensity_threshold: valore massimo medio (0-255) lungo il bordo (da aspettarsi scuro).
        inner_intensity_threshold: valore minimo medio (0-255) all'interno (da aspettarsi chiaro).

        Ritorna:
        Una lista di tuple (x, y, r) per ogni candidato palla mirino rilevato.
        """
        # Utilizzo dell'immagine in scala di grigi già presente in self.__gray
        gray = self.__gray.copy()
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Utilizziamo la sogliatura automatica (Otsu) per ottenere una immagine binaria.
        ret, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Troviamo i contorni e la relativa gerarchia
        contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None:
            return []
        hierarchy = hierarchy[0]  # si lavora sulla prima (ed unica) dimensione della gerarchia
        
        candidates = []
        
        for i, cnt in enumerate(contours):
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            area_outer = cv2.contourArea(cnt)
            #print(f"x {x}, y {y}, r {radius}")

            if search_info != None:
                x_min, y_min, x_max, y_max = search_info.area
                if not (x_min <= x <= x_max and
                        y_min <= y <= y_max):
                    #print("Scartata per area")
                    continue

                if not (search_info.min_radius <= radius <= search_info.max_radius):
                    #print("Scartata per radius")
                    continue

                # Verifichiamo che sia un contorno esterno (padre = -1) che ha un figlio
            if hierarchy[i][3] == -1:  # Se ha un genitore, non è un contorno esterno
                print("Non ha genitore")
                continue

            # Se il contorno non ha un "figlio", non consideriamo questo contorno come candidato
            """if hierarchy[i][2] == -1:
                print("Non ha figlio")
                continue"""
            
            # Filtraggio per area minima
            
            if area_outer < area_threshold:
                #print("Scartata per area")
                continue
            
            # Verifica della forma circolare: rapporto area_contorno / area del cerchio inscritto
            
            if radius <= 0:
                #print("Scartata per radius")
                continue
            
            circle_area = np.pi * (radius ** 2)
            circ_ratio = area_outer / circle_area
            if circ_ratio < circularity_threshold:
                #print("Scartata per circularity")
                continue
            
            # Recupero del contorno interno (si prende il primo figlio)
            inner_index = hierarchy[i][2]
            inner_cnt = contours[inner_index]

            (inner_x, inner_y), inner_r = cv2.minEnclosingCircle(inner_cnt)
            
            # Creazione di una maschera per il contorno esterno
            mask_outer = np.zeros_like(gray)
            cv2.drawContours(mask_outer, [cnt], -1, 255, -1)

            # Creazione della maschera per il contorno interno
            mask_inner = np.zeros_like(gray)
            cv2.drawContours(mask_inner, [inner_cnt], -1, 255, -1)
            
            # La zona del bordo è data dalla differenza tra il contorno esterno e quello interno
            mask_border = cv2.subtract(mask_outer, mask_inner)
            
            # Calcolo dell'intensità media lungo il bordo e all'interno
            mean_border = cv2.mean(gray, mask=mask_border)[0]
            mean_inner = cv2.mean(gray, mask=mask_inner)[0]
            
            # MODIFICATO: Controlliamo che il bordo sia sufficientemente CHIARO ed l'interno sufficientemente chiaro
            #print(f"Mean border: {mean_border}/ {border_intensity_threshold}, Mean inner: {mean_inner} / {inner_intensity_threshold}")
            if mean_border > border_intensity_threshold: #25
                """print("Scartata per mean_border")
                print("----------------------------")
                """
                continue
            if mean_inner < inner_intensity_threshold: #120
                """print("Scartata per mean_inner")
                print("----------------------------")"""

                continue
            candidate = (int(x), int(y), int(radius))
            
            candidates.append(candidate)
        
        return candidates



    
    
    def _find_white_lines(self, area = None):
        """
        Rileva le linee bianche (mirino) utilizzando una combinazione di filtraggio per il colore bianco,
        operazioni morfologiche, Canny e HoughLinesP.
        """
        # Converti in HSV per facilitare l'isolamento del bianco
        hsv = cv2.cvtColor(self.__img_matrix, cv2.COLOR_BGR2HSV)
        # Definisci una maschera per il bianco (puoi adattare questi valori in base alle condizioni di illuminazione)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Operazioni morfologiche per eliminare piccoli rumori e unire segmenti vicini
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Rilevamento dei bordi
        edges = cv2.Canny(mask, 40, 160, apertureSize=3)
        
        # Rilevamento delle linee con HoughLinesP
        # I parametri possono essere adattati in base alla risoluzione e alle caratteristiche dell'immagine
        lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=90, 
                                minLineLength=12, maxLineGap=50)
        
        output_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if area != None:
                    x1_area,y1_area, x2_area, y2_area = area 
                    if not (x1_area <= x1 <= x2_area and
                            y1_area <= y2 <= y2_area  ):
                        continue
                
                output_lines.append((x1, y1, x2, y2))
                # Disegna la linea sull'immagine di output per il debug
                cv2.line(self.__img_matrix, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        return output_lines

