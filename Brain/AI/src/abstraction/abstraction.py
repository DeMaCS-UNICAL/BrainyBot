from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.stack import Stack
import numpy as np

class Abstraction:
    
    
    
    def ToGraph(self, elements:dict, distance:())->ObjectGraph:
        graph = ObjectGraph(distance)
        for label in elements.keys():
            for match in elements[label]:
                graph.add_another_node(match[0], match[1], label)
        return graph

    def ToMatrix(self, elements:dict, distance:())->[]:
        # Extract A and B values into NumPy array
        # Extract A and B values into a flat NumPy array
        #values_array = np.array([item for sublist in elements.values() for item in sublist])
        offset=[10000,10000]
        delta=[distance[0]*10,distance[1]*10]
        all_matches=[[],[]]
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
        # Reshape the array to have two columns (A and B)
        #values_array = values_array.reshape(-1, 2)
        # Use numpy.min once to find minimum values along both axes
        #min= np.min(values_array, axis=0)
        max=[0,0]
        #print(offset)
        #print(delta)
        for label in elements.keys():            
            for match in elements[label]:
                for i in range(2):
                    current = (match[i]-offset[i])//delta[i]
                    if current > max[(i+1)%2]:
                        max[(i+1)%2]=current
        matrix=[]
        #print(max)
        for i in range(max[0]+1):
            matrix.append([])
            for j in range(max[1]+1):
                matrix[i].append(None)
        #print("rows :",max[0]-min[0])
        #print("cloumns :",max[1]-min[1])
        #print("sizes: ",len(matrix),len(matrix[0]))
        for label in elements.keys():
            for match in elements[label]:
                #print(match[0],offset[0],delta[0])
                #print(match[1],offset[1],delta[1])
                r=(match[1]-offset[1])//delta[1]
                c=(match[0]-offset[0])//delta[0]
                #print(r,c)
                #print(label)
                matrix[r][c]=label
                #print(matrix)
        return matrix,offset,delta
                
                

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
        