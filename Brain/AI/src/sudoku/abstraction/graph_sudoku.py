from AI.src.sudoku.dlvsolution.helpers import Cell, Box, Given


class GraphSudoku:
    def __init__(self):
        self.__cells = []
        self.__boxes = []
        for r in range(9):
            for c in range(9):
                self.__cells.append(Cell(r, c))
                self.__boxes.append(Box(r, c, (r // 3) * 3 + (c // 3)))

    def get_cells(self):
        return self.__cells

    def get_boxes(self):
        return self.__boxes

    def get_givens(self, values):
        givens = []
        for r in range(9):
            for c in range(9):
                v = values[r * 9 + c]
                if v != 0:
                    givens.append(Given(r, c, v))
        return givens
