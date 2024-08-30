from AI.src.abstraction.helpers import customExagonalSorter
from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.stack import Stack
import numpy as np
import cv2
import math

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

    def compute_rows_exagonal_matrix(self,bubbles:list,radius,grid_data):
        major_row=radius
        minor_row=2*radius
        row_type=None

        #search between the possible positions of a major_row or minor_row to determine which one is the first one
        for _ in range(grid_data[1]):

            if(bubbles[0][0] >= major_row - grid_data[0] and bubbles[0][0] <= major_row + grid_data[0]):
                row_type=grid_data[1]
                break

            if(bubbles[0][0] >= minor_row - grid_data[0] and bubbles[0][0] <= minor_row + grid_data[0]):
                row_type=grid_data[1]-1
                break

            minor_row+=2*radius
            major_row+=2*radius 
        
        #Defined the type of rows we then calculate the number of rows based on the bubbles detected
        number_of_rows = 0

        if(len(bubbles) > 0):
            number_of_rows = 1

        for i in range(len(bubbles)):
            if( i < len(bubbles)-1 and bubbles[i+1][1] > bubbles[i][1] + grid_data[0]):
                number_of_rows+= round((bubbles[i+1][1]-bubbles[i][1]) / grid_data[2])
        

        return row_type,number_of_rows
    
    def removing_false_matches(self,elements:list,radius,height_matching,grid_data):
        bubbles= []
        player_bubbles=[]
        #also changes the y value so that way there are no inconsistency with the y center of the bubbles on the same row
        #this is done to avoid problems when sorting the list based on the y values
        for bubble in range(len(elements)):
            if(elements[bubble][2] >= radius - grid_data[0] and elements[bubble][2]<= radius + grid_data[0]):
                if(elements[bubble][1] > height_matching[0]) and (elements[bubble][1] < height_matching[1]):
                    skip=False
                    for existing in bubbles:
                        if((elements[bubble][0] >= existing[0]-grid_data[0] and elements[bubble][0] <= existing[0] + grid_data[0]) and  
                            (elements[bubble][1] >= existing[1]-grid_data[0] and elements[bubble][1] <= existing[1] + grid_data[0])):
                            skip=True
                            break
                    if not skip:
                    #changes the value if the last bubble inserted has an y coord similar to yours
                        if(len(bubbles) > 0 and (elements[bubble][1]  >= bubbles[-1][1] - grid_data[0] and elements[bubble][1] <= bubbles[-1][1] + grid_data[0])):
                            elements[bubble][1]=bubbles[-1][1]
                            
                        bubbles.append(elements[bubble])
        
                elif(elements[bubble][1] > height_matching[1]) and (elements[bubble][1] < height_matching[2]):
                    skip=False
                    for existing in bubbles:
                        if((elements[bubble][0] >= existing[0]-grid_data[0] and elements[bubble][0] <= existing[0] + grid_data[0]) and  
                            (elements[bubble][1] >= existing[1]-grid_data[0] and elements[bubble][1] <= existing[1] + grid_data[0])):
                            skip=True
                            break
                    
                    if not skip and len(player_bubbles) < 2:
                        player_bubbles.append(elements[bubble])


        return bubbles,sorted(player_bubbles,key = customExagonalSorter)

    def exagonal_grid_to_matrix(self,bubbles:list,radius,grid_data):

        #Sort and then construct
        ExagonalMatrix=[[]]
        bubbles = sorted(bubbles,key=customExagonalSorter)
        bubbles_max_index=len(bubbles) - 1
        row=0

        #Finding row type based on the first bubble(first row)
        if(bubbles_max_index >= 0):

            row_type,number_of_rows=self.compute_rows_exagonal_matrix(bubbles,radius,grid_data)
            currentRowY = bubbles[0][1]

            if(row_type is None):
                return ExagonalMatrix
            elif(row_type == grid_data[1]):
                distance = radius
            else:
                distance = 2*radius

            ###   

            currentBubble = 0   

            #Constructs each row based on the number of rows, adding empty spots where no bubbles detected

            for value in range(number_of_rows):
                for _ in range(row_type):
                    if ((bubbles[currentBubble][0] >= distance - grid_data[0] and bubbles[currentBubble][0] <= distance + grid_data[0]) and 
                        (bubbles[currentBubble][1] >= currentRowY - grid_data[0] and bubbles[currentBubble][1] <= currentRowY + grid_data[0])):
                        ExagonalMatrix[row].append(bubbles[currentBubble])
                        if(currentBubble < bubbles_max_index):
                            currentBubble+=1
                    else:
                        ExagonalMatrix[row].append([distance,currentRowY,radius,[0,0,0]])
                    
                    distance+=2*radius
                
                #at the end of each row approx to next row
                currentRowY += grid_data[2]
                
                
                if(row_type == grid_data[1]):
                    row_type -= 1
                    distance = 2*radius
                else:
                    row_type += 1
                    distance = radius

                if(value < number_of_rows - 1):
                    ExagonalMatrix.append([])
                    row+=1

        return ExagonalMatrix
        