import os
from languages.asp.asp_input_program import ASPInputProgram
from  numpy import array_equal

from AI.src.constants import RESOURCES_PATH
from AI.src.candy_crush.dlvsolution.helpers import chooseDLVSystem

class Validation:
    def __init__(self):
        pass
    
    def stringfy(self,matrix):
        string = []
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                    if matrix[i][j]!=None:
                        string.append(matrix[i][j])
                    else:
                        string.append('None')
            string.append("||")
        return string
    def validate_matrix(self, abstraction_result, validation_input):
        abstraction = self.stringfy(abstraction_result)
        validation=[]
        #print(abstraction)
        #print()
        with open(validation_input) as file:
            for line in file:
                line=line.strip('\n ')
                validation.extend(line.split(" "))
                validation.append("||")
        #print(validation)
       # return self.levensthein(abstraction_result,expected_result)
        print(self.levensthein(abstraction,validation))
    
    def levensthein(self,first,second):
        dist = [[0 for col in range(len(second)+1)] for row in range(len(first)+1)]
        for i in range(1,len(first)+1):
            dist[i][0]=i
        for j in range(1,len(second)+1):
            dist[0][j] = j
            for i in range(1,len(first)+1):
                if first[i-1]==second[j-1]:
                    sub=0
                else:
                    sub=1
                dist[i][j]=min(dist[i-1][j]+1,dist[i][j-1]+1,dist[i-1][j-1]+sub)
        print(f"Distance {dist[-1][-1]}")
                    
            
            