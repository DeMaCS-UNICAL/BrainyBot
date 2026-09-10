from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.stack import Stack
import numpy as np
import cv2
from sklearn.cluster import AgglomerativeClustering
from matplotlib import pyplot as plt
from AI.src.vision.output_game_object import MonogramCell, MonogramHint, MonogramGrid, OutputTemplateMatch, OutputContainer, OutputCircle, OutputRectangle
from AI.src.vision.input_game_object import TemplateMatch, TextRectangle, Rectangle
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.monogram.detect.constants import TEMPLATES, THRESHOLDS, DISTANCE


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
                        # INFO: commented the print
                        #print(matrix[r][c].x,matrix[r][c].y,matrix[r][c].label)
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


class MonogramAbstraction:
    """
    Abstraction for Monogram using TemplateMatch:
    1. Uses template matching to detect cells with X or empty
    2. Extracts hint text from rectangles
    3. Organizes into game matrix
    """
    
    def __init__(self, grid_size: tuple = (5, 5), cell_size: tuple = (50, 50)):
        """
        Args:
            grid_size: Expected (rows, cols)
            cell_size: Expected (width, height)
        """
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    # ============ GRID PROCESSING USING TEMPLATE MATCHING ============
    
    def process_grid_cells(self, finder: ObjectsFinder, cell_size: tuple = None) -> tuple:
        """
        Detect grid cells using template matching.
        
        Args:
            finder: ObjectsFinder with loaded screenshot
            cell_size: Override cell size if needed
            
        Returns:
            Tuple of (matrix, detected_cells, offset, delta)
        """
        if cell_size is None:
            cell_size = self.cell_size
        
        # Use TemplateMatch to find all cells (cross and empty)
        template_matches = self._find_cells_with_templates(finder)
        
        # Convert template matches to MonogramCell objects
        detected_cells = self._process_template_matches(template_matches)
        
        # Organize into matrix
        matrix, offset, delta = self._organize_cells_to_matrix(detected_cells)
        
        return matrix, detected_cells, offset, delta
    
    def _find_cells_with_templates(self, finder: ObjectsFinder) -> list:
        """
        Use TemplateMatch to find all cells in the image.
        
        Args:
            finder: ObjectsFinder instance with loaded image
            
        Returns:
            List of OutputTemplateMatch objects
        """
        # Create TemplateMatch search object
        # This will match against all templates (cross and empty)
        search = TemplateMatch(
            templates=TEMPLATES,           # All templates: cross_*.png, empty_*.png
            thresholds=THRESHOLDS,         # Thresholds for each template
            find_all=True,                 # Find all matches
            regmax=True,                   # Use regional max suppression
            grayscale=False                # Color template matching
        )
        
        # Use finder to match templates
        matches = finder.find(search)
        
        return matches
    
    def _process_template_matches(self, matches: list) -> list:
        """
        Convert OutputTemplateMatch objects to MonogramCell objects.
        
        Args:
            matches: List of OutputTemplateMatch from template matching
            
        Returns:
            List of MonogramCell objects
        """
        cells = []
        
        for match in matches:
            # match.label contains: "cross_template1" or "empty_template1"
            is_cross = match.label.startswith("cross_")
            
            cell = MonogramCell(
                x=match.x,
                y=match.y,
                has_cross=is_cross,
                confidence=match.confidence,
                cell_id=None  # Will be set later
            )
            cell.cell_width = match.template_width
            cell.cell_height = match.template_heigth
            
            cells.append(cell)
        
        return cells
    
    def _organize_cells_to_matrix(self, detected_cells: list) -> tuple:
        """
        Organize detected cells into abstract matrix.
        
        Returns:
            Tuple of (matrix, offset, delta)
        """
        if not detected_cells:
            rows, cols = self.grid_size
            empty_matrix = [['.' for _ in range(cols)] for _ in range(rows)]
            return empty_matrix, (0, 0), self.cell_size
        
        # Compute grid geometry
        offset, delta = self._compute_grid_geometry(detected_cells)
        
        # Initialize empty matrix
        rows, cols = self.grid_size
        matrix = [['.' for _ in range(cols)] for _ in range(rows)]
        
        # Place detected cells
        for cell in detected_cells:
            row = int((cell.y - offset[1]) / delta[1])
            col = int((cell.x - offset[0]) / delta[0])
            
            if 0 <= row < rows and 0 <= col < cols:
                # Place cell state: 'X' if has cross, '.' if empty
                matrix[row][col] = str(cell)
                cell.cell_id = f"x{col}y{row}"
        
        return matrix, offset, delta
    
    def _compute_grid_geometry(self, detected_cells: list) -> tuple:

        """Determine grid geometry from detected cells"""

        x_coords = [cell.x for cell in detected_cells]

        y_coords = [cell.y for cell in detected_cells]
    
        # Cluster to find grid lines

        x_clusters = self._cluster_coordinates(x_coords, threshold=20)

        y_clusters = self._cluster_coordinates(y_coords, threshold=20)
    
        offset = (min(x_clusters), min(y_clusters))
    
        # NOTE: delta used to come from the average gap between detected cell

        # clusters (_compute_spacing). Since only crossed cells are matched

        # (there's no "empty" template), rows/columns without a cross create

        # gaps spanning more than one grid line, which inflates that average

        # and produces a wrong, screenshot-dependent cell pitch. Each detected

        # cell already carries its own template size (cell_width/cell_height),

        # which is a direct, detection-density-independent measure of one grid

        # step, so use that instead.

        delta = (

            int(np.mean([cell.cell_width for cell in detected_cells])),

            int(np.mean([cell.cell_height for cell in detected_cells])),

        )
    
        return offset, delta
    
    
    @staticmethod
    def _cluster_coordinates(coords: list, threshold: int = 20) -> list:
        """Group similar coordinates"""
        if not coords:
            return []
        
        sorted_coords = sorted(coords)
        clusters = []
        current_cluster = [sorted_coords[0]]
        
        for coord in sorted_coords[1:]:
            if coord - current_cluster[-1] <= threshold:
                current_cluster.append(coord)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [coord]
        
        if current_cluster:
            clusters.append(np.mean(current_cluster))
        
        return clusters
    
    @staticmethod
    def _compute_spacing(x_clusters: list, y_clusters: list) -> tuple:
        """Average spacing between clusters"""
        def avg_spacing(clusters):
            if len(clusters) < 2:
                return 50
            spacings = [clusters[i+1] - clusters[i] for i in range(len(clusters)-1)]
            return int(np.mean(spacings))
        
        return (avg_spacing(x_clusters), avg_spacing(y_clusters))
    
    # ============ HINT PROCESSING ============
    
    def process_hints(self, finder: ObjectsFinder) -> list:
        """
        Extract hint rectangles and their text.
        
        Args:
            finder: ObjectsFinder instance
            
        Returns:
            List of MonogramHint objects
        """
        # Find all rectangles in the image
        hint_rectangles = finder.find(Rectangle(hierarchy=False))
        
        hints = []
        for rect in hint_rectangles:
            # Extract text using TextRectangle
            hint_text = self._extract_hint_text(finder, rect)
            
            if hint_text:
                hint = MonogramHint(
                    x=float(rect.x),
                    y=float(rect.y),
                    width=float(rect.width),
                    height=float(rect.heigth),
                    hint_text=hint_text,
                    hint_type=self._classify_hint_type(hint_text)
                )
                hints.append(hint)
        
        return hints
    
    @staticmethod
    def _extract_hint_text(finder: ObjectsFinder, rectangle: OutputRectangle) -> str:
        """Extract text from rectangle"""
        try:
            text_search = TextRectangle(rectangle=rectangle, numeric=False)
            result = finder.find(text_search)
            
            if result:
                return str(result).strip()
            else:
                return None
        except Exception as e:
            print(f"Error extracting text from hint: {e}")
            return None
    
    @staticmethod
    def _classify_hint_type(hint_text: str) -> str:
        """Classify hint type"""
        hint_lower = hint_text.lower()
        
        if 'row' in hint_lower or 'r' in hint_lower:
            return 'horizontal'
        elif 'col' in hint_lower or 'c' in hint_lower or 'v' in hint_lower:
            return 'vertical'
        else:
            return 'clue'
    
    def validate_matrix(self, matrix: list) -> bool:
        """Validate matrix structure"""
        expected_rows, expected_cols = self.grid_size
        
        if len(matrix) != expected_rows:
            print(f"Row count mismatch: {len(matrix)} != {expected_rows}")
            return False
        
        for i, row in enumerate(matrix):
            if len(row) != expected_cols:
                print(f"Column count mismatch in row {i}: {len(row)} != {expected_cols}")
                return False
            
            for j, cell in enumerate(row):
                if cell not in ['X', '.', None]:
                    print(f"Invalid cell at [{i}][{j}]: {cell}")
                    return False
        
        return True