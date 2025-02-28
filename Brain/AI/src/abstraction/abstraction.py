from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.stack import Stack
import numpy as np
import cv2
from sklearn.cluster import AgglomerativeClustering
from matplotlib import pyplot as plt
from AI.src.vision.output_game_object import OutputGameObject, OutputTemplateMatch, OutputContainer, OutputCircle

class Abstraction:
    
    def reset(self):
        Cluster.clear_clusters()
    
    def ToGraph(self, elements:dict, distance:tuple)->ObjectGraph:
        graph = ObjectGraph(distance)
        main_id=9
        for label in sorted(elements.keys()):
            main_id+=1
            sub_id=9
            for match in elements[label]:
                sub_id+=1
                graph.add_another_node(match[0], match[1], label,int(str(main_id)+str(sub_id)))
        return graph

    #elements.values are OutputGameObject
    def ToMatrix(self, elements:list, distance:tuple, labelMatrix:bool=True)->list:
        offset, delta, clusters = self.compute_offest_delta_dict(elements, distance)
        max_row_col=[0,0]
        #print(offset,delta,sep="\n")
        for j in range(len(elements)):
                coord=[0,0]       
                for i in range(2):
                    key = "x" if i==0 else "y"
                    current_coord = Cluster.get(key,clusters[i][j]).get_mean()
                    coord[i]=current_coord
                    current = (current_coord-offset[i])//delta[i]
                    if current > max_row_col[(i+1)%2]:
                        max_row_col[(i+1)%2]=int(current)
                elements[j].x=coord[0]
                elements[j].y=coord[1]
        matrix=[]
        for i in range(max_row_col[0]+1):
            matrix.append([])
            for j in range(max_row_col[1]+1):
                matrix[i].append(None)
        for element in elements:
                r=int((element.y-offset[1])//delta[1])
                c=int((element.x-offset[0])//delta[0])
                if isinstance(element,OutputTemplateMatch):
                    if matrix[r][c]!=None and matrix[r][c].confidence> element.confidence:
                        continue
                matrix[r][c]=element
        offset, delta = self.compute_offest_delta_matrix(matrix)
        for r in range(len(matrix)):
            for c in range(len(matrix[r])):
                if matrix[r][c]!=None:
                    if labelMatrix and isinstance(matrix[r][c],OutputTemplateMatch) :
                        print(matrix[r][c].x,matrix[r][c].y,matrix[r][c].label)
                        matrix[r][c]=matrix[r][c].label
                    else:
                        matrix[r][c]=(matrix[r][c].x,matrix[r][c].y)
        '''
        for r in range(len(matrix)):
            for c in range(len(matrix[r])):
                print(matrix[r][c],end="\t")
            print()
        #print(matrix)
        '''
        return matrix,offset,delta
    def compute_offest_delta_dict(self, elements:list, distance):
        #print(distance)
        offset=[10000,10000]
        delta=[10000,10000]
        all_coordinates=[[],[],]
        for element in elements:
            all_coordinates[0].append(element.x)
            all_coordinates[1].append(element.y)
            #print(element.label,element.x,element.y)
        Cluster.clear_clusters()
        x_clusters  = Cluster.generate_initial_clusters(all_coordinates[0],"x")
        y_clusters  = Cluster.generate_initial_clusters(all_coordinates[1],"y")
        representative_coord = []
        index=0
        for key in Cluster.clusters.keys():
            representative_coord.append([])
            for cluster in Cluster.clusters[key]:
                representative_coord[-1].append(cluster.get_mean())
            representative_coord[-1].sort()
            offset[index] = representative_coord[-1][0]
            index+=1
        for i in range(2):
            for j in range(len(representative_coord[i])-1):
                current_delta = representative_coord[i][j+1]-representative_coord[i][j]
                #print(i,current_delta)
                if current_delta>=distance[i] and current_delta<delta[i]:
                    if current_delta < delta[i]:
                        delta[i]=current_delta
        return offset,delta,(x_clusters,y_clusters)
    
    def compute_offest_delta_matrix(self, matrix):
        offset=[0,0]
        for i in range(len(matrix)):
            if matrix[i][0]!=None:
                offset[0]=matrix[i][0].x
        for i in range(len(matrix[0])):
            if matrix[0][i]!=None:
                offset[1]=matrix[0][i].y
        delta=[0,0]
        cont=[0,0]
        for r in range(len(matrix)):
            for c in range(len(matrix[r])):
                if matrix[r][c]!=None:
                    if c<len(matrix[r])-1 and matrix[r][c+1]!=None:
                        delta[0]+=matrix[r][c+1].x-matrix[r][c].x
                        cont[0]+=1
                    if r<len(matrix)-1 and matrix[r+1][c]!=None:
                        delta[1]+=matrix[r+1][c].y-matrix[r][c].y
                        cont[1]+=1
        if(cont[0]!=0):
            delta[0]//=cont[0]
        if(cont[1]!=0):
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

    def assign_to_container_as_stack(self, contained:list[OutputCircle],containers:list[OutputContainer])->dict:
        elements_per_container =[]
        for i in range(len(containers)):
            elements_per_container.append([])
        contained.sort(reverse=True,key = lambda x: x.y)
        for obj in contained:
            for i in range(len(containers)):                
                dist = cv2.pointPolygonTest(containers[i].contour,(float(obj.x),float(obj.y)),True)

                if  dist>0 and dist>obj.radius:
                    skip=False
                    for existing in elements_per_container[i]:
                        if (existing.y -obj.y)<existing.radius+obj.radius-(existing.radius+obj.radius)*10/100:
                            skip=True
                    if not skip:
                        elements_per_container[i].append(obj)
                    break
        empty=[]
        non_empty=[]
        for i in range(len(containers)):
            container_coord = (containers[i].x,containers[i].y)
            to_append = Stack(container_coord,containers[i].id)
            if len(elements_per_container[i])==0:
                empty.append(to_append)
            else:
                non_empty.append(to_append)
                non_empty[-1].add_elements(elements_per_container[i])
        self.assign_id_to_containers(empty,non_empty)
        
        return empty,non_empty

    def assign_id_to_containers(self, empty,non_empty):
        l:list[Stack] = []
        l.extend(empty)
        l.extend(non_empty)
        coordinates=[]
        for container in l:
            coordinates.append((container.get_x(),container.get_y()))
        if len(Cluster.clusters)==0:
            Cluster.generate_initial_clusters([x[0] for x in coordinates],"x")
            Cluster.generate_initial_clusters([x[1] for x in coordinates],"y")
            '''
            for key in Cluster.clusters.keys():
                print(key)
                for cluster in Cluster.clusters[key]:
                    print(cluster.cluster_id)
            '''
        for i in range(len(l)):
            cluster_x_id = Cluster.find_or_add_cluster(l[i].get_x(),"x").cluster_id
            cluster_y_id = Cluster.find_or_add_cluster(l[i].get_y(),"y").cluster_id
            l[i].set_id(f"x{cluster_x_id}y{cluster_y_id}")

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


class Cluster:
    clusters = {} 
    def __init__(self, cluster_id, coordinates, cluster_threshold=10):
        self.cluster_id = cluster_id
        self.coordinates = coordinates
        self.cluster_threshold = cluster_threshold

    def get_mean(self):

        return custom_median(self.coordinates)

    @classmethod
    def return_belonging_cluster(cls, coord, cluster_key):
        for cluster in cls.clusters[cluster_key]:
                if all(abs(coord - c) <= cluster.cluster_threshold for c in cluster.coordinates):
                    return cluster
        return None

    @classmethod
    def find_or_add_cluster(cls, coord, cluster_key, cluster_threshold=10):
        if cluster_key not in Cluster.clusters.keys():
            cls.clusters[cluster_key]=[]
        existing_cluster = cls.return_belonging_cluster(coord,cluster_key)
        if existing_cluster:
            existing_cluster.coordinates.append(coord)
            return existing_cluster

        new_cluster = Cluster(len(cls.clusters[cluster_key]) + 1, [coord], cluster_threshold)
        cls.clusters[cluster_key].append(new_cluster)
        cls.clusters[cluster_key].sort(key=lambda c: min(c.coordinates))
        
        return new_cluster

    @classmethod
    def clear_clusters(cls):
        cls.clusters = {}
    @classmethod
    def generate_initial_clusters(cls, coordinates, cluster_key, cluster_threshold=10):
        if cluster_key not in cls.clusters.keys():
                    cls.clusters[cluster_key]=[]
        '''
        sorted_coords = sorted(coordinates)
        current_cluster = Cluster(cluster_id=len(cls.clusters[cluster_key]) + 1, coordinates=[], cluster_threshold=cluster_threshold)

        for coord in sorted_coords:
            if all(abs(coord - c) <= cluster_threshold for c in current_cluster.coordinates):
                current_cluster.coordinates.append(coord)
            else:
                
                cls.clusters[cluster_key].append(current_cluster)
                current_cluster = Cluster(cluster_id=len(cls.clusters[cluster_key]) + 1, coordinates=[coord], cluster_threshold=cluster_threshold)
        cls.clusters[cluster_key].append(current_cluster)
        '''
        coordinates2 = np.array(coordinates).reshape(-1,1)
        agglomerative = AgglomerativeClustering(n_clusters=None, distance_threshold=cluster_threshold)
        labels = agglomerative.fit_predict(coordinates2)
        for i in range(len(coordinates)):
            cls.get(cluster_key,labels[i]).coordinates.append(coordinates[i])
        return labels

    @classmethod
    def get(cls,key,cluster_id):
        for cluster in cls.clusters[key]:
            if cluster.cluster_id == cluster_id:
                return cluster
        cluster = Cluster(cluster_id=cluster_id, coordinates=[])
        cls.clusters[key].append(cluster)
        return cluster

def custom_median(lst):
    lst_sorted = sorted(lst)
    mid_index = len(lst_sorted) // 2
    return lst_sorted[mid_index]