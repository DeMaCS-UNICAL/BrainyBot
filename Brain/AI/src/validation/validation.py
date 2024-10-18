import os
from languages.asp.asp_input_program import ASPInputProgram
from  numpy import array_equal

from AI.src.constants import RESOURCES_PATH
from AI.src.candy_crush.dlvsolution.helpers import chooseDLVSystem

from AI.src.abstraction.elementsStack import ElementsStacks

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
        print("validating abstraction")
        real = set(validation_input)
        found = set(abstraction_result)
        fp=0
        fn=0
        tp=0
        for detected in found:
            if detected not in real:
                fp += 1
            else:
                tp+=1
        for existing in real:
            if existing not in found:
                fn += 1
        #print(fp,fn,tp)
        return fp,fn

    
    def validate_matches(self,matches_list,validation:dict):
        print("validating vision")
        validation_result={}
        count=0
        current_match=""
        for m in matches_list:
            if current_match == "":
                current_match=m.label
            if m.label!=current_match:
                validation_result[current_match]= count-validation[current_match]
                count=1
                current_match = m.label
            else:
                count+=1
        if current_match != "":
            validation_result[current_match]= count-validation[current_match]
        for key in validation.keys():
            if validation_result.get(key)==None:
                validation_result[key]=-validation[key]
            if validation_result[key]<0:
                print(key,validation_result[key])
        return validation_result


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
    def validate_stacks(self, abstraction_result, validation_input):
        validation=""
        with open(validation_input) as file:
            for line in file:
                validation+=line
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

            