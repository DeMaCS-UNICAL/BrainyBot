import os
import cv2
import numpy as np
import mahotas
import multiprocessing
from time import time
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from paddleocr import PaddleOCR
import logging
import json

from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH, GRID_CONFIG_PATH
from AI.src.vision.input_game_object import *
from AI.src.vision.output_game_object import *
from AI.src.abstraction.objectsMatrix import *


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
        
        logging.getLogger('ppocr').setLevel(logging.ERROR)

        self.validation=validation
        self.__img_matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=color) 
        self.__output = self.__img_matrix.copy()  
        self.__blurred = cv2.medianBlur(self.__img_matrix,7)  # Used to find the color of the balls
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=cv2.COLOR_BGR2GRAY)  # Used to find the balls
        self.__generic_object_methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__generic_object_method = eval(self.__generic_object_methodName)
        self.__threshold=threshold
        self.__paddle = None
        self.__grid_config = self.__load_grid_config()
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


    def is_circle(self,contour, circularity_threshold=0.85):
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
        print("possible containers",len(containers))
        coordinates = []
        to_return=[]
        for i in range(len(containers)):
            (x,y),axis,cont_a = cv2.fitEllipse(containers[i])
            if not rotate and abs(tem_a+cont_a)%179>5: #the 2 contours are aligned
                print("nope, rotated")
                continue
            if proportion_tolerance!=0 and abs(axis[1]/axis[0]-tem_axis[1]/tem_axis[0])>tem_axis[1]/tem_axis[0]*proportion_tolerance:
                print("nope, wrong proportion")
                continue
            if size_tolerance!=0 and abs(axis[1]-tem_axis[1])>tem_axis[1]*size_tolerance:
                print("nope, wrong size")
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

    def __extract_text_with_paddle(self, rectangle: OutputRectangle):
        if self.__paddle is None:
            self.__paddle = PaddleOCR(use_angle_cls=False, lang='en')
        img = self.extract_subimage(self.__img_matrix, rectangle).copy()
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.__paddle.ocr(img_rgb, cls=False)
        return [line[1][0] for line in results[0]] if results != [None] else []

    def __find_text(self, rectangle: OutputRectangle) -> str:
        texts = self.__extract_text_with_paddle(rectangle)
        return texts[0] if texts else None

    def __find_number(self, search_info: TextRectangle) -> int:
        texts = self.__extract_text_with_paddle(search_info.rectangle)
        numbers = [text for text in texts if text.isdigit()]
        return int(numbers[0]) if numbers else None

    def __find_text_from_dictionary(self, search_info: TextRectangle) -> str:
        texts = self.__extract_text_with_paddle(search_info.rectangle)
        with open(search_info.dictionary, 'r') as file:
            dictionary_words = set(word.strip() for word in file.readlines())
        for text in texts:
            if text in dictionary_words:
                return text
        return None

    def __find_text_from_regex(self, search_info: TextRectangle) -> str:
        texts = self.__extract_text_with_paddle(search_info.rectangle)
        for text in texts:
            if search_info.regex.match(text):
                return text
        return None

    def __load_grid_config(self):
        if os.path.exists(GRID_CONFIG_PATH):
            with open(GRID_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


    # Get the OutputTemplateMatch list representing the grid for the specified game name (e.g., "ccs_soda")
    # Uses the grid configuration from grid_config.json (cell_w, cell_h) must be defined for the game
    def getGrid(self, game_name: str, img=None) -> list[OutputTemplateMatch]:
        resolution = f"{self.__img_matrix.shape[0]}x{self.__img_matrix.shape[1]}"
        if not self.__grid_config or game_name not in self.__grid_config:
            raise KeyError(f"'{game_name}' not found in grid_config.json")
        params = self.__grid_config[game_name]
        if not resolution in params:
            raise KeyError(f"'{resolution}' not found for game {game_name} in grid_config.json")
        params = params[resolution]
        grid_region = self.__agn_retain_grid_region(self.__img_matrix)

        filtered_grid_region = self.__agn_process_image(grid_region)

        try:
            cw = float(params["cell_w"])
            ch = float(params["cell_h"])
        except KeyError as e:
            missing = [k for k in ("cell_w", "cell_h") if k not in params]
            raise KeyError(f"Missing {', '.join(missing)} in grid_config for game '{game_name}'") from e
        boxes = self.__agn_get_grid(filtered_grid_region, cw, ch)

        return self.__agn_boxes_to_output_template_matches(filtered_grid_region,boxes, game_name,img)



    # --- Agnostic methods for grid detection ---
    # Search the grid region in the image and blacken everything else
    def __agn_retain_grid_region(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Seal small gaps so the board becomes a single solid blob
        kernel = np.ones((5,5), np.uint8)
        binary_closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Find the outer board contour on the FILLED binary, not on edges
        contours, _ = cv2.findContours(binary_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            cv2.drawContours(mask, [largest], -1, (255,), thickness=cv2.FILLED)   # solid, no holes

            # Apply mask to the ORIGINAL image (color-safe)
            result = cv2.bitwise_and(image, image, mask=mask)
            return result
        
        return np.zeros_like(image)

    # --- Agnostic methods for grid detection ---
    # Process the image to blacken rows/columns that are mostly black (under threshold)
    def __agn_process_image(self, img: np.ndarray, threshold: int = 100) -> np.ndarray:
        img_array = img.copy()  
        if img_array.ndim == 2:
            nonblack = img_array != 0                 # (H,W)
        else:
            nonblack = np.any(img_array != 0, axis=2) # (H,W)

        H, W = nonblack.shape

        # --- Rows: find first/last with count > threshold
        row_counts = np.count_nonzero(nonblack, axis=1)           # (H,)
        row_hits = np.flatnonzero(row_counts > threshold)

        if row_hits.size == 0:
            # No row exceeds the threshold => whole image becomes black
            img_array[...] = 0
            return img_array

        top = row_hits[0]
        bottom = row_hits[-1]

        # Blacken rows outside [top, bottom]
        if top > 0:
            img_array[:top, :] = 0
        if bottom + 1 < H:
            img_array[bottom+1:, :] = 0


        # --- Columns: find first/last with count > threshold
        col_counts = np.count_nonzero(nonblack, axis=0)           # (W,)
        col_hits = np.flatnonzero(col_counts > threshold)

        if col_hits.size == 0:
            # All columns under threshold after row pass
            img_array[...] = 0
            return img_array

        left = col_hits[0]
        right = col_hits[-1]

        # Blacken columns outside [left, right]
        if left > 0:
            img_array[:, :left] = 0
        if right + 1 < W:
            img_array[:, right+1:] = 0

        return img_array

    # --- Agnostic methods for grid detection ---
    # Return (top, bottom, left, right) of non-black region to define limits
    @staticmethod
    def __agn_non_black_limits(img: np.ndarray):
        """Ritorna (top, bottom, left, right) della regione non-nera."""
        H, W = img.shape[:2]
        s = img if img.ndim == 2 else img.max(axis=2)
        row_max = s.max(axis=1)
        col_max = s.max(axis=0)
        if row_max.max() == 0:
            return -1, -1, -1, -1
        rows_has = row_max > 0
        cols_has = col_max > 0
        top    = int(np.argmax(rows_has))
        bottom = int(H - 1 - np.argmax(rows_has[::-1]))
        left   = int(np.argmax(cols_has))
        right  = int(W - 1 - np.argmax(cols_has[::-1]))
        return top, bottom, left, right

    # --- Agnostic methods for grid detection ---
    # Create boxes from horizontal and vertical lines
    @staticmethod
    def __agn_create_boxes(horizontal_lines: list, vertical_lines: list) -> list[dict]:
        boxes = []
        for i in range(len(horizontal_lines) - 1):
            for j in range(len(vertical_lines) - 1):
                top    = horizontal_lines[i]
                bottom = horizontal_lines[i + 1]
                left   = vertical_lines[j]
                right  = vertical_lines[j + 1]
                center_x = int((left + right) // 2)
                center_y = int((top  + bottom) // 2)
                width  = int(right - left)
                height = int(bottom - top)
                boxes.append({"center": (center_x, center_y), "width": width, "height": height})
        return boxes

    # --- Agnostic methods for grid detection ---
    # Generate boxes representing the grid cells
    def __agn_get_grid(self, image: np.ndarray, cell_width: float, cell_height: float):
        top, bottom, left, right = self.__agn_non_black_limits(image)
        if min(top, bottom, left, right) < 0:
            return []  # entire image is black -> no cells

        num_rows = round((bottom-top)/cell_height)
        num_col = round((right-left)/cell_width)

        center_horiz = top+((bottom-top)/2)
        center_vert = left+((right-left)/2)
        next_horiz_top = center_horiz-cell_height/2 if num_rows%2==1 else center_horiz
        next_horiz_bottom = center_horiz+cell_height/2 if num_rows%2==1 else center_horiz + cell_height
        next_vert_left = center_vert-cell_width/2 if num_col%2==1 else center_vert
        next_vert_right = center_vert +cell_width/2 if num_col%2==1 else center_vert + cell_width
        vertical_lines =[]
        horizontal_lines=[]
        while next_horiz_top>=top:
            horizontal_lines.insert(0,next_horiz_top)
            next_horiz_top -= cell_height
        while next_horiz_bottom<=bottom:
            horizontal_lines.append(next_horiz_bottom)
            next_horiz_bottom += cell_height
        while next_vert_left>=left:
            vertical_lines.insert(0,next_vert_left)
            next_vert_left -= cell_width
        while next_vert_right<=right:
            vertical_lines.append(next_vert_right)
            next_vert_right += cell_width

        boxes = self.__agn_create_boxes(horizontal_lines, vertical_lines)
        return boxes


    # --- Agnostic methods for grid detection ---
    # Convert boxes to OutputTemplateMatch objects
    # TODO: add label and confidence if needed
    def __agn_boxes_to_output_template_matches(self, filtered_grid_image,boxes: list[dict], game_name: str, img=None) -> list[OutputTemplateMatch]:
        objects = []
        boxes = self.__agn_filter_boxes_by_black_pixels(filtered_grid_image, boxes, black_threshold=50, max_black_ratio=0.40)
        _, _, _,_,_,labels_confidence = self.__agn_template_matching_fast(filtered_grid_image,boxes,out_image=img)
        for label_conf in sorted(labels_confidence,key= lambda x : x[0]):
            (cx, cy) = boxes[label_conf[0]]["center"]
            w = int(boxes[label_conf[0]]["width"])
            h = int(boxes[label_conf[0]]["height"])
            objects.append(OutputTemplateMatch(cx, cy, w, h, label_conf[1], label_conf[2]))
        return objects

    #Remove black patches form candidate boxes for TM
    def __agn_filter_boxes_by_black_pixels(self,image, boxes, black_threshold=50, max_black_ratio=0.40):

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        H, W = gray.shape[:2]
        kept_boxes = []
        received = len(boxes)
        removed = 0

        for b in boxes:
            cx, cy = b["center"]
            w, h = int(b["width"]), int(b["height"])

            # Reconstruct box coordinates and clip to image bounds
            left   = max(0, int(cx - w // 2))
            right  = min(W, int(left + w))
            top    = max(0, int(cy - h // 2))
            bottom = min(H, int(top + h))
            roi = gray[top:bottom, left:right]
            total = roi.size
            black_pixels = np.count_nonzero(roi < black_threshold)
            black_ratio = black_pixels / total

            if black_ratio <= max_black_ratio:
                kept_boxes.append(b)
            else:
                removed += 1
        return kept_boxes

    #Performs template matching in order to cluster objects in the screen
    def __agn_template_matching_fast(self,image, boxes, out_image=None, black_threshold=50, match_threshold=0.80, parallel=True, template_percentage=0.75, save_templates=False):
        img=image
        H, W,_ = img.shape
        if len(boxes)==0:
            return 0, np.inf, np.inf,0,0,[],img
        # 2) pack boxes to arrays
        centers = np.array([b["center"] for b in boxes], dtype=np.int32)   # (N,2): [cx, cy]
        wh      = np.array([[b["width"], b["height"]] for b in boxes], dtype=np.int32)  # (N,2): [w, h]

        # corners (clipped)
        x1 = np.clip(centers[:,0] - wh[:,0]//2, 0, W)
        y1 = np.clip(centers[:,1] - wh[:,1]//2, 0, H)
        x2 = np.clip(x1 + wh[:,0], 0, W)
        y2 = np.clip(y1 + wh[:,1], 0, H)
        areas = (x2 - x1) * (y2 - y1)
        # 5) arrays instead of dicts
        N = len(boxes)
        assigned = np.full(N, -1, dtype=np.int32)
        is_flat=np.full(N, False, dtype=bool)
        cur_id = 1

        # accumulate drawings; do once at end
        to_draw_rects = []
        to_draw_labels = []

        # stats (just compute once with numpy)
        widths  = wh[:,0].astype(np.float32)
        heights = wh[:,1].astype(np.float32)
        templates=[]
        for i in range(N):
            cx, cy = centers[i]
            w, h   = int(wh[i,0]), int(wh[i,1])

            # build template = 0.75 window around the same center
            tpl_w, tpl_h = int(w *template_percentage), int(h *template_percentage)
            tx1 = max(cx - tpl_w // 2, 0); ty1 = max(cy - tpl_h // 2, 0)
            tx2 = min(tx1 + tpl_w, W);     ty2 = min(ty1 + tpl_h, H)
            tpl = img[ty1:ty2, tx1:tx2]
            th, tw = tpl.shape[:2]
            if th == 0 or tw == 0:
                templates.append(None)
                is_flat[i]=True
                to_draw_rects.append((int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])))
                #plt.imshow(tpl)
                #plt.show()
                to_draw_labels.append((i, "ERR!",0))
                continue

            #temp_box = np.full(tpl.shape[:2],125, dtype=np.uint8)
            tpl_gray = cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY)
        
            #print(res.max())
            if not self.is_flat_patch(tpl_gray):
                templates.append(tpl)
            else:
                to_draw_rects.append((int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])))
                #plt.imshow(tpl)
                #plt.show()
                to_draw_labels.append((i, 0,0))
                templates.append(None)
                is_flat[i]=True

        for i in range(N):
            if assigned[i] != -1 or is_flat[i]:
                continue
            tpl = templates[i]
            th, tw = tpl.shape[:2]
            tpl_area = th * tw

            assigned[i] = cur_id
            to_draw_rects.append((int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])))
            to_draw_labels.append((i, cur_id, 0))

            # 4) vectorized candidate prefilter (size & area gating)
            area_factor = (1/(template_percentage**2))
            area_factor += area_factor*0.2
            ok_size = (wh[:,0] >= tw) & (wh[:,1] >= th) & (areas <= area_factor * tpl_area)
            cand_mask = (assigned == -1) & (~is_flat) & ok_size
            cand_mask[i] = False
            cand_idx = np.flatnonzero(cand_mask)
            def score(j):
                sr = img[y1[j]:y2[j], x1[j]:x2[j]]
                res = cv2.matchTemplate(sr, tpl, cv2.TM_CCOEFF_NORMED)
                
                return j, float(res.max())

            if cand_idx.size:
                for j in cand_idx:
                    _, m = score(j)
                    if m >= match_threshold:
                        assigned[j] = cur_id
                        to_draw_rects.append((int(x1[j]), int(y1[j]), int(x2[j]), int(y2[j])))
                        to_draw_labels.append((j, cur_id, m))

            cur_id += 1

        # 6) draw once at the end
        
        if out_image is not None:
            for rx1, ry1, rx2, ry2 in to_draw_rects:
                cv2.rectangle(out_image, (rx1, ry1), (rx2, ry2), (0, 255, 255), 2)
            for idx, cid, score in to_draw_labels:
                cx = (x1[idx] + x2[idx]) // 2
                cy = (y1[idx] + y2[idx]) // 2
                cv2.putText(out_image, f"{cid}:{score:.2f}", (x1[idx], cy + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1, cv2.LINE_AA)
            
        mean_width = widths.mean()
        mean_height = heights.mean()
        w_cv = float(widths.std() / max(mean_width, 1e-9)) if widths.size else float("inf")
        h_cv = float(heights.std() / max(mean_height, 1e-9)) if heights.size else float("inf")
        num_groups = int(np.unique(assigned[assigned != -1]).size)

        return num_groups, w_cv, h_cv,mean_width,mean_height,to_draw_labels
    
    def is_flat_patch(self,patch, var_thresh=130, range_thresh=15):
        """
        Returns True if `patch` is (almost) flat.
        - var_thresh: variance threshold (uint8 scale). 4 ≈ std dev of 2.
        - range_thresh: early-exit check using (max - min).
        """
        # Early cheap reject/accept via value range
        if (int(patch.max()) - int(patch.min())) <= range_thresh:
            return True
        # Robust variance (E[x^2] - E[x]^2)
        m = patch.mean(dtype=np.float32)
        v = (patch.astype(np.float32)**2).mean() - m*m
        return v <= var_thresh