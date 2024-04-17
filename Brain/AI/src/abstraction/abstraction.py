from AI.src.abstraction.helpers import customExagonalSorter
from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.stack import Stack
import numpy as np
import cv2

from matplotlib import pyplot as plt
class Abstraction:
    
    
    
    def ToGraph(self, elements:dict, distance:())->ObjectGraph:
        graph = ObjectGraph(distance)
        main_id=9
        for label in sorted(elements.keys()):
            main_id+=1
            sub_id=9
            for match in elements[label]:
                sub_id+=1
                graph.add_another_node(match[0], match[1], label,int(str(main_id)+str(sub_id)))
        return graph

    def ToMatrix(self, elements:dict, distance:())->[]:
        offset, delta = self.compute_offest_delta_dict(elements, distance)
        max=[0,0]
        for label in elements.keys():            
            for match in elements[label]:
                for i in range(2):
                    current = (match[i]-offset[i])//delta[i]
                    if current > max[(i+1)%2]:
                        max[(i+1)%2]=current
        matrix=[]
        for i in range(max[0]+1):
            matrix.append([])
            for j in range(max[1]+1):
                matrix[i].append(None)
        for label in elements.keys():
            for match in elements[label]:
                r=(match[1]-offset[1])//delta[1]
                c=(match[0]-offset[0])//delta[0]
                if matrix[r][c]!=None and matrix[r][c][1][2]>match[2]:#matrix[r][c][1][2]: matrix stores the lable and the coordinates+value of the match
                    continue
                matrix[r][c]=(label,match)
        offset, delta = self.compute_offest_delta_matrix(matrix)
        for r in range(len(matrix)):
            for c in range(len(matrix[r])):
                if matrix[r][c]!=None:
                    matrix[r][c]=matrix[r][c][0]
        print(matrix)
        return matrix,offset,delta

    def compute_offest_delta_dict(self, elements, distance):
        offset=[10000,10000]
        delta=[distance[0]*10,distance[1]*10]
        all_matches=[[],[],]
        for match_list in elements.values():
            for match in match_list:
                all_matches[0].append(match[0])
                all_matches[1].append(match[1])
        for i in range(2):
            all_matches[i].sort()
            offset[i]=all_matches[i][0]
        for match_index in range(len(all_matches[0])):
            for i in range(2):
                if match_index<len(all_matches[i])-1:
                    current_delta=all_matches[i][match_index+1]-all_matches[i][match_index]
                    if current_delta>=distance[i] and current_delta<delta[i]:
                        delta[i]=current_delta
        return offset,delta
    
    def compute_offest_delta_matrix(self, matrix):
        offset=[0,0]
        for i in range(len(matrix)):
            if matrix[i][0]!=None:
                offset[0]=matrix[i][0][1][0]
        for i in range(len(matrix[0])):
            if matrix[0][i]!=None:
                offset[1]=matrix[0][i][1][1]
        delta=[0,0]
        cont=[0,0]
        for r in range(len(matrix)):
            for c in range(len(matrix[r])):
                if matrix[r][c]!=None:
                    if c<len(matrix[r])-1 and matrix[r][c+1]!=None:
                        delta[0]+=matrix[r][c+1][1][0]-matrix[r][c][1][0]
                        cont[0]+=1
                    if r<len(matrix)-1 and matrix[r+1][c]!=None:
                        delta[1]+=matrix[r+1][c][1][1]-matrix[r][c][1][1]
                        cont[1]+=1
        delta[0]//=cont[0]
        delta[1]//=cont[1]
        return offset,delta
                
                

    def Empty_Stacks(self,elements:list, width, matcher_width, matcher_height, distance_ratio)->list:
        stacks=[]
        match = []
        for p in elements:
            if all(abs(p[0] - m[0]) > (width/distance_ratio) for m in match):
                match.append(p)
        match = [(int(m[0] + matcher_width / 2), int(m[1] + matcher_height / 2)) for m in match]
        for c in match:
            stack = Stack()
            stack.set_x_coordinates(c[0])
            stack.set_y_coordinate(c[1])
            stacks.append(stack)
        return stacks
    
    def Stack(self, elements: list,tolerance=50,max_distance=150, min_number_elements=4)->list:
        stacks = []
        elements.sort(key=lambda x: x[1])
        while elements:
            element = elements.pop()  # ball object format: [ x coordinate, y coordinate, [R, G, B] ]
            stack_found = False
            for stack in stacks:
                if stack.get_x() - tolerance <= element[0] <= stack.get_x() + tolerance:
                    stack_elements = stack.get_elements()
                    for b in stack_elements:
                        if abs(element[1] - b[1]) <= max_distance:
                            stack.add_element(element)
                            stack_found = True
                            break
            if not stack_found:
                stack = Stack()
                stack.add_element(element)
                stack.set_x_coordinates(element[0])
                stacks.append(stack)

        stacks[:] = [stack for stack in stacks if len(stack.get_elements()) >= min_number_elements]
        [stack.set_y_coordinate() for stack in stacks]
        return stacks

    def assign_to_container_as_stack(self, contained,containers,containers_coord)->dict:
        elements_per_container =[]
        for i in range(len(containers)):
            elements_per_container.append([])
        contained.sort(reverse=True,key = lambda x: x[1])
        for obj in contained:
            for i in range(len(containers)):                
                dist = cv2.pointPolygonTest(containers[i],(float(obj[0]),float(obj[1])),True)

                if  dist>0 and dist>obj[2]:
                    skip=False
                    for existing in elements_per_container[i]:
                        if (existing[1] -obj[1])<existing[2]+obj[2]-(existing[2]+obj[2])*10/100:
                            skip=True
                    if not skip:
                        elements_per_container[i].append(obj)
                    break
        empty=[]
        non_empty=[]
        for i in range(len(containers)):
            if len(elements_per_container[i])==0:
                empty.append(Stack(containers_coord[i]))
            else:
                non_empty.append(Stack(containers_coord[i]))
                non_empty[-1].add_elements(elements_per_container[i])
        return empty,non_empty

    def stack_no_duplicates(self, elements:dict)->list:
        stacks = []
        for container in elements.keys:
            elements[container].sort(key=lambda x: x[1])
            stack = Stack()
            for element in elements[container]:
                stack.add_element(element)
            stack.set_x_coordinates(element[0])
            stack.set_y_coordinate(element[0])#? verifica vada bene
            stacks.append(stack)
        return stacks

    def compute_row_type_exagonal_matrix(self,bubble,radius,grid_metadata):
        major_row=radius
        minor_row=2*radius
        row_type=None
        starting_distance=None
        #search between the possible positions of a major_row or minor_row to determine which one is the first one
        for _ in range(grid_metadata[1]):

            if(bubble[0] >= major_row - grid_metadata[0] and bubble[0] <= major_row + grid_metadata[0]):
                row_type=grid_metadata[1]
                starting_distance=radius
                break

            if(bubble[0] >= minor_row - grid_metadata[0] and bubble[0] <= minor_row + grid_metadata[0]):
                row_type=grid_metadata[1]-1
                starting_distance=2*radius
                break

            minor_row+=2*radius
            major_row+=2*radius   

        return row_type,starting_distance  
    
    def removing_false_matches(self,elements:list,radius,height_matching,grid_metadata):
        bubbles= []
        #also changes the y value so that way there are no inconsistency with the y center of the bubbles on the same row
        for b in range(len(elements)):
            if(elements[b][1] > height_matching[0]) and (elements[b][1] < height_matching[1]):
                if(elements[b][2] >= radius - grid_metadata[0] and elements[b][2]<= radius + grid_metadata[0]):
                    skip=False
                    for existing in bubbles:
                        if((elements[b][0] >= existing[0]-grid_metadata[0] and elements[b][0] <= existing[0] + grid_metadata[0]) and  
                            (elements[b][1] >= existing[1]-grid_metadata[0] and elements[b][1] <= existing[1] + grid_metadata[0])):
                            skip=True
                            break
                    if not skip:
                       #changes the value if the last bubble inserted has an y coord similar to yours
                        if(len(bubbles) > 0 and (elements[b][1]  >= bubbles[-1][1] - grid_metadata[0] and elements[b][1] <= bubbles[-1][1] + grid_metadata[0])):
                            elements[b][1]=bubbles[-1][1]

                        bubbles.append(elements[b])
        
        return bubbles

    def ExagonalGridToMatrix(self,elements:list,height_matching,radius,grid_metadata):

        #Removing False match
        
        bubbles=self.removing_false_matches(elements,radius,height_matching,grid_metadata)

        #Now sort and then construct
        ExagonalMatrix=[[]]
        bubbles = sorted(bubbles,key=customExagonalSorter)
        bubbles_max_index=len(bubbles)
        row=0

        #Finding row type based on the first bubble(first row)
        row_type,distance=self.compute_row_type_exagonal_matrix(bubbles[0],radius,grid_metadata)
        ###                
        for i in range(bubbles_max_index):
            for _ in range(row_type):
                #decides whether the current bubble matches with the examinated position or not
                if(bubbles[i][0] >= distance - grid_metadata[0] and bubbles[i][0] <= distance + grid_metadata[0]):
                    ExagonalMatrix[row].append(bubbles[i])
                    distance+=2*radius
                    break
                else:
                    ExagonalMatrix[row].append([distance,bubbles[i][1],0])
                    distance+=2*radius
            
            #FillUp when is the last row
            if( i == bubbles_max_index -1):
                for _ in range(len(ExagonalMatrix[row]),row_type):
                    ExagonalMatrix[row].append([0,0,0])
            
            #FillUp if the next bubble is not on the same row and after start a new row and update parameters
            if(i != bubbles_max_index-1 and bubbles[i+1][1] > bubbles[i][1] + grid_metadata[0]):
                for _ in range(len(ExagonalMatrix[row]),row_type):
                    ExagonalMatrix[row].append([0,0,0])

                ExagonalMatrix.append([])
                row+=1
                
                if(row_type == grid_metadata[1]):
                    row_type-=1
                    distance=2*radius
                else:
                    row_type+=1
                    distance=radius
            
        #L'intera astrazione si basa sul fatto di non poter avere una riga della nostra matrice per cui non è stata trovata almeno una pallina  

        return ExagonalMatrix

        