import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from AI.src.sudoku.dlvsolution.dlvsolution import DLVSolution
from AI.src.sudoku.dlvsolution.helpers import Cell, Box, Given

# A known-solvable easy puzzle (0 = blank). Row-major, 9x9.
PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION = {
    (0, 0): 5, (0, 1): 3, (0, 2): 4, (0, 3): 6, (0, 4): 7, (0, 5): 8, (0, 6): 9, (0, 7): 1, (0, 8): 2,
    (1, 0): 6, (1, 1): 7, (1, 2): 2, (1, 3): 1, (1, 4): 9, (1, 5): 5, (1, 6): 3, (1, 7): 4, (1, 8): 8,
    (2, 0): 1, (2, 1): 9, (2, 2): 8, (2, 3): 3, (2, 4): 4, (2, 5): 2, (2, 6): 5, (2, 7): 6, (2, 8): 7,
}


def build_facts(puzzle):
    cells, boxes, givens = [], [], []
    for r in range(9):
        for c in range(9):
            cells.append(Cell(r, c))
            boxes.append(Box(r, c, (r // 3) * 3 + (c // 3)))
            if puzzle[r][c] != 0:
                givens.append(Given(r, c, puzzle[r][c]))
    return cells, boxes, givens


class TestDLVSolution(unittest.TestCase):
    def test_solves_easy_puzzle(self):
        cells, boxes, givens = build_facts(PUZZLE)
        solver = DLVSolution()
        values = solver.solve(cells, boxes, givens)

        self.assertIsNotNone(values)
        self.assertEqual(len(values), 81)

        result = {(v.get_row(), v.get_col()): v.get_value() for v in values}
        for (r, c), n in SOLUTION.items():
            self.assertEqual(result[(r, c)], n, f"cell ({r},{c}) expected {n}, got {result[(r, c)]}")

        # solver must never change a given cell's value
        for r in range(9):
            for c in range(9):
                if PUZZLE[r][c] != 0:
                    self.assertEqual(
                        result[(r, c)], PUZZLE[r][c],
                        f"given cell ({r},{c})={PUZZLE[r][c]} was overwritten with {result[(r, c)]}"
                    )

        # every row/col/box must contain 1-9 exactly once
        for r in range(9):
            row_vals = sorted(result[(r, c)] for c in range(9))
            self.assertEqual(row_vals, list(range(1, 10)))
        for c in range(9):
            col_vals = sorted(result[(r, c)] for r in range(9))
            self.assertEqual(col_vals, list(range(1, 10)))
        for b in range(9):
            box_vals = sorted(
                result[(r, c)]
                for r in range(9) for c in range(9)
                if (r // 3) * 3 + (c // 3) == b
            )
            self.assertEqual(box_vals, list(range(1, 10)))


if __name__ == "__main__":
    unittest.main()
