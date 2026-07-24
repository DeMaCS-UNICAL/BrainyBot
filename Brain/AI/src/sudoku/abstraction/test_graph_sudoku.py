import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from AI.src.sudoku.abstraction.graph_sudoku import GraphSudoku


class TestGraphSudoku(unittest.TestCase):
    def test_builds_81_cells(self):
        g = GraphSudoku()
        cells = g.get_cells()
        self.assertEqual(len(cells), 81)
        coords = {(c.get_row(), c.get_col()) for c in cells}
        self.assertEqual(len(coords), 81)
        for r in range(9):
            for c in range(9):
                self.assertIn((r, c), coords)

    def test_builds_81_box_assignments(self):
        g = GraphSudoku()
        boxes = g.get_boxes()
        self.assertEqual(len(boxes), 81)
        # cell (0,0) and (2,2) share box 0; (0,0) and (0,3) do not
        box_of = {(b.get_row(), b.get_col()): b.get_box() for b in boxes}
        self.assertEqual(box_of[(0, 0)], box_of[(2, 2)])
        self.assertNotEqual(box_of[(0, 0)], box_of[(0, 3)])
        self.assertEqual(box_of[(8, 8)], box_of[(6, 6)])

    def test_get_givens_skips_zeros(self):
        g = GraphSudoku()
        values = [0] * 81
        values[0] = 5      # (0,0) = 5
        values[9 + 1] = 7  # (1,1) = 7
        givens = g.get_givens(values)
        self.assertEqual(len(givens), 2)
        result = {(gi.get_row(), gi.get_col()): gi.get_value() for gi in givens}
        self.assertEqual(result[(0, 0)], 5)
        self.assertEqual(result[(1, 1)], 7)


if __name__ == "__main__":
    unittest.main()
