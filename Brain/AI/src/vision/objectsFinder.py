import os
import cv2
import numpy as np
import mahotas
import multiprocessing
from time import time
from matplotlib import pyplot as plt
import logging
import os, psutil

from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
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
        
        

        self.validation=validation
        self.__img_matrix = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=color) 
        self.__output = self.__img_matrix.copy()  
        self.__blurred = cv2.medianBlur(self.__img_matrix,7)  # Used to find the color of the balls
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, screenshot),color_conversion=cv2.COLOR_BGR2GRAY)  # Used to find the balls
        self.__generic_object_methodName = 'cv2.TM_CCOEFF_NORMED'
        self.__generic_object_method = eval(self.__generic_object_methodName)
        self.__threshold=threshold
        self.__paddle = None
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
            logging.getLogger('ppocr').setLevel(logging.ERROR)
            if search_info.numeric:
                return self.__find_number(search_info)
            if search_info.dictionary!=None:
                return self.__find_text_from_dictionary(search_info)
            if search_info.regex!=None:
                return self.__find_text_from_regex(search_info)
            return self.__find_text(search_info)
            

    def template_matching_worker_process(self,element,regmax,img):
        tm_name,tm_img,tm_threshold= element
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
        return self.template_matching_worker_process( (element, template, threshold), regmax, img)


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
        #canny = cv2.Canny(gray, canny_threshold,int(canny_threshold*3.5))
        min_radius_odd = min_radius if min_radius % 2 ==1 else min_radius+1
        contours,edged = self.get_circle_contours(gray,min_radius_odd)
        edged = cv2.cvtColor(edged,cv2.COLOR_GRAY2BGR)
        print("found",len(contours),"contours")
        circles = [cnt for cnt in contours if self.is_circle(cnt)]
        #colored = edged
        if self.debug and not self.validation:
            cv2.drawContours(edged, circles, -1, (255, 0, 0), 3)
            plt.imshow(edged)
            plt.show()
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
    def get_circle_contours(self, gray,min_radius):
        sigma=1.6
        k=1.6
        zc_thresh=0.01
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        gray = cv2.morphologyEx(self.__img_matrix, cv2.MORPH_GRADIENT,kernel)
        gray = cv2.cvtColor(gray,cv2.COLOR_BGR2GRAY)
        b1 = cv2.bilateralFilter(gray,-1,12,12)
        dog = cv2.subtract(b1,gray)  # sign convention doesn't matter for zero-crossings
        #dog = cv2.cvtColor(dog,cv2.COLOR_BGR2GRAY)
        #dog = cv2.normalize(np.abs(dog), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        edged_1 = gray
        edged_2 = cv2.bilateralFilter(dog,-1,12,12)
        edged = cv2.subtract(edged_2,dog)
        mask1 = dog>0
        mask2 = dog==0
        dog[mask1]=0
        dog[mask2]=255
        mask1 = edged>0
        mask2 = edged==0
        edged[mask1]=0
        edged[mask2]=255
        
        self.show_comparison(dog, edged, edged_1, edged_2)
        contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        temp = cv2.cvtColor(edged,cv2.COLOR_GRAY2BGR)
        cv2.drawContours(temp,contours,-1,(255,0,0),3)
        print("contours")
        plt.imshow(temp)
        plt.show()
        print("detection done")
        return contours,edged

    def show_comparison(self, dog, edged, edged_1, edged_2):
        width = int(self.__img_matrix.shape[1] * 0.3)
        height = int(self.__img_matrix.shape[0] * 0.3)
        dim = (width, height)
        resized1 = cv2.cvtColor(cv2.resize(dog, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized2 = cv2.cvtColor(cv2.resize(edged_1, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized3 = cv2.cvtColor(cv2.resize(edged_2, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        resized4 = cv2.cvtColor(cv2.resize(edged, dim, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        result = np.concatenate((resized1,resized2,resized3,resized4), axis=1)
        plt.imshow(result)
        plt.show()

    '''
    def get_circle_contours(self, gray,min_radius):
        edged = self.__img_matrix
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
        morph=cv2.morphologyEx(edged,cv2.MORPH_OPEN  ,kernel,iterations=2)
        morph=cv2.morphologyEx(morph,cv2.MORPH_GRADIENT,kernel)

        plt.imshow(morph)
        plt.show()
        gray = cv2.cvtColor(morph, cv2.COLOR_BGR2GRAY)

        # 2) Build a kernel of ones with zero at the center (exclude center pixel)
        k = np.ones((3, 3), dtype=np.float32)
        center = 3 // 2
        k[center, center] = 0.0
        k /= k.sum()  # normalize to compute the mean of neighbors only

        # 3) Convolve to get the neighbor-mean brightness (excluding center)
        kernel = np.array([[0, -1,  0],
                   [-1,  5, -1],
                   [0, -1,  0]], np.float32)
        neigh_mean = cv2.filter2D(edged, ddepth=-1, kernel=kernel, borderType=cv2.BORDER_REPLICATE)
        neigh_mean = cv2.filter2D(neigh_mean, ddepth=-1, kernel=kernel, borderType=cv2.BORDER_REPLICATE)
        plt.imshow(neigh_mean)
        plt.show()
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
        morph=cv2.morphologyEx(cv2.cvtColor(neigh_mean,cv2.COLOR_BGR2GRAY),cv2.MORPH_GRADIENT  ,kernel)
        plt.imshow(morph)
        plt.show()
        # 4) Mask where neighbors are "close to black"
        mask = neigh_mean < 20  # True where avg neighbors are dark

        # 5) Apply mask: set those pixels to black
        out = morph.copy()
        out[mask] = (0, 0, 0)
        mask = np.any(out != 0, axis=2)
        out[mask]=(255,255,255)
        out = cv2.morphologyEx(out,cv2.MORPH_OPEN,kernel,iterations=1)
        out = cv2.morphologyEx(out,cv2.MORPH_CLOSE,kernel,iterations=3)
        mask = np.any(out != 0, axis=2)
        #edged =cv2.adaptiveThreshold(edged,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,min_radius,1)
        plt.imshow(out)
        plt.show()
        edged[mask] = (255,255,255)
        #plt.imshow(edged)
        #plt.show()
        
        #edged=cv2.morphologyEx(edged,cv2.MORPH_GRADIENT  ,kernel)
        #plt.imshow(edged)
        #plt.show()
        _,edged =cv2.threshold(cv2.cvtColor(edged,cv2.COLOR_BGR2GRAY), 0, 255,cv2.THRESH_OTSU)
        plt.imshow(cv2.cvtColor(edged,cv2.COLOR_GRAY2BGR))
        plt.show()
        contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        temp = cv2.cvtColor(edged,cv2.COLOR_GRAY2BGR)
        cv2.drawContours(temp,contours,-1,(255,0,0),3)
        print("contours")
        plt.imshow(temp)
        plt.show()
        print("detection done")
        # 2. Smooth to reduce noise (optional but recommended)
        return contours,edged
    
    '''    
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
        #ret, edges = cv2.threshold(gray, 127, 255, 0)
        edges = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
        #tem_edges = cv2.Canny(tem_gray, 50, 150)
        #ret, tem_edges = cv2.threshold(tem_gray, 127, 255, 0)
        tem_edges = cv2.adaptiveThreshold(tem_gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
        # Find contours
        tem_contours, _ = cv2.findContours(tem_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if tem_contours:
            largest_contour = max(tem_contours, key=cv2.contourArea)
        else:
            return []

        tem_cnt = largest_contour
        _,tem_axis,tem_a = cv2.fitEllipse(tem_cnt)
        if tem_axis[0]==0:
            return []
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        containers = [cnt for cnt in contours if cv2.matchShapes(cnt,tem_cnt,3,0.0)<0.02]
        coordinates = []
        to_return=[]
        for i in range(len(containers)):
            (x,y),axis,cont_a = cv2.fitEllipse(containers[i])
            if axis[0]==0:
                continue
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

    def __extract_text_with_paddle(self, rectangle: OutputRectangle):
        if self.__paddle is None:
            from paddleocr import PaddleOCR
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

    




















def gs_bilateral_smooth(img_bgr, r=2, sigma_s=2.0, sigma_r=25.0, passes=1, do_backward=True):
    """
    Gauss–Seidel (in-place) bilateral smoothing on a color (BGR) image.
    Updates propagate within the same sweep (edge-preserving).
    
    Args:
        img_bgr   : uint8/float32 BGR image, shape (H,W,3).
        r         : neighborhood radius (e.g., 1->3x3, 2->5x5).
        sigma_s   : spatial sigma (pixels).
        sigma_r   : range sigma (intensity; use ~10-40 for uint8 images).
        passes    : number of forward/(optional) backward cycles.
        do_backward: if True, run a backward sweep after each forward sweep.

    Returns:
        Smoothed image with same dtype as input.
    """
    assert img_bgr.ndim == 3 and img_bgr.shape[2] == 3
    H, W, _ = img_bgr.shape
    dtype = img_bgr.dtype

    # Work in float32 for stable math
    I = img_bgr.astype(np.float32).copy()

    # Precompute spatial Gaussian weights for the (2r+1)x(2r+1) window
    # w_s(d) = exp( - (dx^2 + dy^2) / (2*sigma_s^2) )
    if sigma_s <= 0:
        raise ValueError("sigma_s must be > 0")
    if sigma_r <= 0:
        raise ValueError("sigma_r must be > 0")

    xs = np.arange(-r, r + 1, dtype=np.float32)
    ys = np.arange(-r, r + 1, dtype=np.float32)
    XX, YY = np.meshgrid(xs, ys, indexing='xy')
    spatial = np.exp(-(XX**2 + YY**2) / (2.0 * sigma_s * sigma_s)).astype(np.float32)

    # Helper for clamped indexing (replicate border)
    def clamp(v, lo, hi):
        return lo if v < lo else (hi if v > hi else v)

    # Main sweeps
    for _ in range(passes):
        # -------- Forward pass (top-left -> bottom-right) --------
        for y in range(H):
            print(y)
            y0 = clamp(y - r, 0, H - 1); y1 = clamp(y + r, 0, H - 1)
            for x in range(W):
                x0 = clamp(x - r, 0, W - 1); x1 = clamp(x + r, 0, W - 1)

                # Current center value (already updated earlier in the sweep)
                center = I[y, x, :]  # shape (3,)

                # Extract neighborhood view over CURRENT state
                P = I[y0:y1+1, x0:x1+1, :]  # (hh, ww, 3)

                # Compute range weights vs current center (color distance)
                # range = exp( - ||P - center||^2 / (2*sigma_r^2) )
                dB = P[..., 0] - center[0]
                dG = P[..., 1] - center[1]
                dR = P[..., 2] - center[2]
                dist2 = dB*dB + dG*dG + dR*dR
                range_w = np.exp(-dist2 / (2.0 * sigma_r * sigma_r)).astype(np.float32)

                # Combine spatial and range weights
                # Note: spatial may be larger than the patch at borders; slice it.
                sh, sw = P.shape[:2]
                Wsr = spatial[:sh, :sw] * range_w

                denom = Wsr.sum()
                if denom > 1e-12:
                    # Weighted sum per channel
                    # (Wsr[..., None] broadcasts to (sh, sw, 3))
                    num = (P * Wsr[..., None]).sum(axis=(0, 1))
                    I[y, x, :] = num / denom
                # else: keep the current center (rare, but guard for numerical issues)

        if do_backward:
            # -------- Backward pass (bottom-right -> top-left) --------
            for y in range(H - 1, -1, -1):
                y0 = clamp(y - r, 0, H - 1); y1 = clamp(y + r, 0, H - 1)
                for x in range(W - 1, -1, -1):
                    x0 = clamp(x - r, 0, W - 1); x1 = clamp(x + r, 0, W - 1)

                    center = I[y, x, :]
                    P = I[y0:y1+1, x0:x1+1, :]

                    dB = P[..., 0] - center[0]
                    dG = P[..., 1] - center[1]
                    dR = P[..., 2] - center[2]
                    dist2 = dB*dB + dG*dG + dR*dR
                    range_w = np.exp(-dist2 / (2.0 * sigma_r * sigma_r)).astype(np.float32)

                    sh, sw = P.shape[:2]
                    Wsr = spatial[:sh, :sw] * range_w

                    denom = Wsr.sum()
                    if denom > 1e-12:
                        num = (P * Wsr[..., None]).sum(axis=(0, 1))
                        I[y, x, :] = num / denom

    # Back to original dtype
    if dtype == np.uint8:
        I = np.clip(I, 0, 255).astype(np.uint8)
    else:
        I = I.astype(dtype)
    return I