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


class ObjectsFinder:
    def __init__(self, screenshot, color=None, debug=False, threshold=0.8,validation=False ):
        #
        # Use Matrix2.png for testing
        #
        self.methods = {TemplateMatch:self.__template_matching,
                        Circle:self.__find_circles,
                        Container:self.__detect_container,
                        Rectangle:self.__find_rectangles,
                        TextRectangle:self.__find_text_or_number}

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

    def find_most_similar_image_template(self,target_image, image_list):
        best_match_image = None
        best_match_value = -float('inf')  # Minore è, meglio è per cv2.TM_SQDIFF
        idx=-1
        for i in range(len(image_list)):
            # Usa il template matching
            result = cv2.matchTemplate(image_list[i], target_image, self.__generic_object_method)
            max_val, _, _, _ = cv2.minMaxLoc(result)
            
            if max_val>0.5 and max_val > best_match_value:
                best_match_value = max_val
                best_match_image = image_list[i]
                idx=i
        return idx

    def find_from_existing_matrix(self,search_info:SimplifiedTemplateMatch,matrix:ObjectMatrix):
        width = search_info.width
        heigth = search_info.heigth
        objects_found=[]
        tm_labels = []
        tm_imgs = []
        for key in search_info.templates:
            tm_labels.append(key)
            tm_imgs.append(search_info.templates[key])
        for i in range(matrix.num_row):
            for j in range(len(matrix.matrix[i])):
                x=matrix.get_cell(i,j).x
                y=matrix.get_cell(i,j).y
                img=self.extract_subimage(self.__img_matrix,OutputRectangle(x,y,width,heigth))
                label_id = self.find_most_similar_image_template(img,tm_imgs)
                if label_id!=-1:
                    objects_found.append(OutputTemplateMatch(x,y,tm_labels[label_id],1))
                else:
                    objects_found.append(OutputTemplateMatch(x,y,"",1))
                
        return objects_found


    def find(self, search_info):
        return self.methods[type(search_info)](search_info)

    def __template_matching(self,search_info:TemplateMatch):
        if search_info.find_all:
                return self.__find_all(search_info)
        return self.find_one_among(search_info)
    
    def __find_rectangles(self,search_info:Rectangle):
            if search_info.hierarchy:
                return self.__find_boxes_and_hierarchy()
            return self.__find_boxes()
    
    def __find_text_or_number(self,search_info:TextRectangle):
            if search_info.numeric:
                return self.__find_number(search_info)
            if search_info.dictionary!=None:
                return self.__find_text_from_dictionary(search_info)
            if search_info.regex!=None:
                return self.__find_text_from_regex(search_info)
            return self.__find_text(search_info)
            

    def template_matching_worker_process(self,id,output_list,elements:list,regmax,img):
        for (tm_name,tm_img,tm_threshold) in elements:
            previous_len=len(output_list)
            output_list.extend(self.__find_matches(img,tm_name,tm_img,tm_threshold,regmax))
            #print(tm_name,"=",len(output_list)-previous_len)
            #print(tm_name,tm_threshold)
        #print(f"I'm done {id}")

        


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
    
    #def find_all(self, elements_to_find:dict, request_regmax=True) -> dict:
    def __find_all(self, search_info:TemplateMatch) -> dict:
        img, elements_to_find,thresholds = self.extract_tm_info(search_info)
        template_num=len(elements_to_find.keys())
        num_processes = min(multiprocessing.cpu_count(),template_num)
        template_per_process = template_num//num_processes
        residual = template_num % num_processes
        count=0
        limit = template_per_process+ (1 if residual>0 else 0)
        templates_for_process=[]
        for element in elements_to_find.keys():
            if count<limit:
                if count==0:
                    templates_for_process.append([])
                templates_for_process[-1].append((element,elements_to_find[element],thresholds[element]))
                count+=1
                if count==limit:
                    if len(templates_for_process)==residual:
                        limit=template_per_process
                    count=0
                    
        processes = []
        
        with multiprocessing.Manager() as manager:
        # Create a shared dictionary
            output_lists=manager.list()
            for i in range(num_processes):
                output_list = manager.list()
                output_lists.append(output_list)
                process = multiprocessing.Process(target=self.template_matching_worker_process, args=(i,output_list,templates_for_process[i],search_info.regmax,img))
                processes.append(process)
                process.start()

            for process in processes:
                process.join()

            main_list=[]
            for l in output_lists:
                main_list.extend(l)
            #print("All processes have finished.")
            '''
            objects_found={}
            for element in elements_to_find.keys():
                #print(f"{element} ")
                objects_found[element] = self.find_matches(self.__img_matrix,elements_to_find[element],request_regmax)
            '''
            return main_list
    
    def __find_matches(self, image,label, element_to_find,threshold, request_regmax=True) -> list:
        
        objects_found=[]
        # execute template match
        res = cv2.matchTemplate(image, element_to_find, self.__generic_object_method)
        # find regional maxElem
        if request_regmax:
            regMax = mahotas.regmax(res)
            res = res * regMax
        # modify this to change the algorithm precision
        loc = np.where(res >= threshold)
        #objects_found = list(zip(*loc[::-1]))
        #print(f"Found {len(objects_found)} matches")
        # Combine coordinates (x, y) with corresponding res values
        for pt in zip(*loc[::-1]):
            x, y = pt
            confidence = res[y, x]  # Extract the confidence value at the corresponding position
            objects_found.append(OutputTemplateMatch(x,y,label,confidence))
        #print(f"found {len(objects_found)} matches")
        return objects_found

    def is_circle(self,contour, circularity_threshold=0.85):
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return False
        
        circularity = 4 * 3.14159 * area / (perimeter * perimeter)
        
        return circularity >= circularity_threshold

    def __find_circles(self, search_info:Circle):
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

    def extract_subimage(self, img,rectangle):
        return img[rectangle.y:rectangle.y+rectangle.heigth, rectangle.x:rectangle.x+rectangle.width]

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

    
    #def detect_container(self,template,proportion_tolerance=0,size_tolerance=0,rotate=False):
    def __detect_container(self,search_info:Container):
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

        # Show the image
        #plt.figure(dpi=300)
        #return to_return,coordinates
        return to_return
    