class Meowgrid:

    # takes as input cells from the vision module 
    def __init__(self, cells : dict):
        self.map_size = int(len(cells.keys()) ** .5)
        self.x_sources, self.y_sources = self._discrete_sources(cells)
        self.colours = self._discrete_colours(cells)
        self.matrix = self.generate_matrix(cells)

    def _discrete_sources(self, cells):
        x_sources = []
        y_sources = []

        for cell_id in cells.keys():
            _,_, sample_point, side_size = cells[cell_id]
            round_size = int(side_size * 0.3) 
            # range not yet saved ... 
            if not any((xofs in x_sources) for xofs in range(sample_point[0] - round_size, sample_point[0] + round_size)):
                x_sources.append(sample_point[0])
            if not any((yofs in y_sources) for yofs in range(sample_point[1] - round_size, sample_point[1] + round_size)):
                y_sources.append(sample_point[1])

        return sorted(x_sources), sorted(y_sources)

    def generate_matrix(self, cells): # i want to have a matrix n x n of ints containing ids of the corresponding box
        # mat = [[-1] * self.map_size] * self.map_size errore assurdo di python indecoroso proprio 
        mat = [[-1 for _ in range(self.map_size)] for _ in range(self.map_size)]
        for cell_id in cells.keys():
            colour, cat, sample_point, _ = cells[cell_id]
            x = self._get_closest_source(self.x_sources, sample_point[0])
            y = self._get_closest_source(self.y_sources, sample_point[1])

            mat[self.y_sources.index(y)][self.x_sources.index(x)] = (cell_id, colour.get_id(), cat) # id of the box and index of the color in the discrete colors list
        #self.__pretty_print_matrix(mat)
        return mat

    def _get_closest_source(self, sources, point):
        closest = sources[0]
        for source in sources:
            if abs(source - point) < abs(closest - point):
                closest = source
        return closest

    def _discrete_colours(self,cells):
        colours = []
        for cell_id in cells.keys():
                colour,_,_,_ = cells[cell_id]
                if colour.get_id() not in colours:
                    colours.append(colour.get_id())
        return colours
    
    def get_grid(self):
        return self.matrix

    def get_cell_id(self,x,y):
        return self.matrix[x][y]

    def __pretty_print_matrix(self,matrix):
        for row in matrix:
            print(row)

    def export_facts(self):
        facts = []
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[i])):
                _, colour, cat = self.matrix[i][j]
                facts.append(f"cell({i},{j},{colour},{str(cat).lower()}).")
        return facts