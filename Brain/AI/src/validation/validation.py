import os
from languages.asp.asp_input_program import ASPInputProgram
import numpy as np
from scipy.optimize import linear_sum_assignment
from AI.src.constants import RESOURCES_PATH
from AI.src.candy_crush.dlvsolution.helpers import chooseDLVSystem

from AI.src.abstraction.elementsStack import ElementsStacks
from collections import defaultdict
class Validation:
    def __init__(self):
        pass
    
    def stringfy_matrix(self,matrix):
        string = []
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                    if matrix[i][j]!=None:
                        string.append(matrix[i][j])
                    else:
                        string.append('None')
            string.append("||")
        return string
    
    def validate_facts(self, abstraction_result:list, validation_input:list):
        #print("validating abstraction")
        real = set(validation_input)
        found = set(abstraction_result)
        fp=0
        fn=0
        tp=0
        for detected in found:
            if detected not in real:
                #print("wrongly detected",detected)
                fp += 1
            else:
                tp+=1
        for existing in real:
            if existing not in found:
                #print("missed",existing)
                fn += 1
        #print("fp",fp,"fn",fn,"tp",tp)
        return fp,fn

    def calculate_distance(self,coord1, coord2):
        return np.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

    def create_cost_matrix(self,detected_objects, ground_truth, label_penalty=1000):
        cost_matrix = np.zeros((len(detected_objects), len(ground_truth)))
        for i, det in enumerate(detected_objects):
            for j, gt in enumerate(ground_truth):
                if det[1] != gt[1]:
                    cost_matrix[i, j] = label_penalty
                else:
                    cost_matrix[i, j] = self.calculate_distance(det[0], gt[0])
        return cost_matrix
    
    def count_false_positives_negatives(self,detected_objects, ground_truth, distance_threshold=50):
        cost_matrix = self.create_cost_matrix(detected_objects, ground_truth)

        # Hungarian algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        #for i, j in zip(row_ind, col_ind):
         #   print(f"Oggetto rilevato {i} abbinato all'oggetto ground truth {j} con costo {cost_matrix[i, j]}")
          #  print(detected_objects[i],ground_truth[j])
        false_positives_by_label = defaultdict(int)
        false_negatives_by_label = defaultdict(int)

        matched_detected = [False] * len(detected_objects)
        matched_ground_truth = [False] * len(ground_truth)
        
        for i, j in zip(row_ind, col_ind):
            if cost_matrix[i, j] > distance_threshold: 
                false_positives_by_label[detected_objects[i][1]] += 1
                false_negatives_by_label[ground_truth[j][1]] += 1
          

            matched_detected[i] = True
            matched_ground_truth[j] = True
        
        for i, matched in enumerate(matched_detected):
            if not matched:
                false_positives_by_label[detected_objects[i][1]] += 1
       
        for j, matched in enumerate(matched_ground_truth):
            if not matched:
                false_negatives_by_label[ground_truth[j][1]] += 1

        return false_negatives_by_label,false_positives_by_label
    
    def validate_matches(self,matches_list,validation:list,threshold=50):
        #print("validating vision")
        matches=[]
        for m in matches_list:
                matches.append(((m.x,m.y),m.label))
        #print(matches)
       
        return self.count_false_positives_negatives(matches,validation,threshold)


    def levensthein(self,first,second):
        dist = [[0 for col in range(len(second)+1)] for row in range(len(first)+1)]
        for i in range(0,len(first)+1):
            dist[i][0]=i
        for j in range(0,len(second)+1):
            dist[0][j] = j
            if j>0:
                for i in range(1,len(first)+1):
                    if first[i-1]==second[j-1]:
                        dist[i][j]=dist[i-1][j-1]
                    else:
                        dist[i][j]=1 + min(dist[i-1][j],dist[i][j-1],dist[i-1][j-1])
        return dist[-1][-1]

#TODO: fix here, validation file should be read by the specific game script
    def validate_stacks(self, abstraction_result, validation):
        
        abstraction=""
        for i in range(len(abstraction_result)):
            abstraction+=abstraction_result[i].custom_str()
        #print("abstr:",abstraction)
        #print("valid:",validation)
        #print(abstraction,end="")
        return self.levensthein(abstraction,validation)
        

class ValidationOutput:
    def __init__(self):
        pass
class CCSOutput(ValidationOutput):
    def __init__(self):
        super().__init__()
        self.vision_output=dict()
        self.abstraction_output=list()

class CCSValidationStats:
    vision_stats=dict()
    abstraction_stats=0

            
