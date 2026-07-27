from AI.src.webservices.input_backend import tap
from AI.src.sudoku.detect.new_detect import MatchingSudoku
from AI.src.sudoku.abstraction.graph_sudoku import GraphSudoku
from AI.src.sudoku.dlvsolution.dlvsolution import DLVSolution


def sudoku(screenshot, debug=False, vision_validation=None, abstraction_validation=None, iteration=0, benchmark=False):
    print(f"START SUDOKU with screenshot {screenshot}")
    print(f"Debug: {debug}")
    print(f"Vision Validation: {vision_validation}")
    print(f"Abstraction Validation: {abstraction_validation}")
    print(f"Iteration: {iteration}")
    print(f"Benchmark: {benchmark}")


    ## Vision
    matcher = MatchingSudoku(screenshot, debug)
    values = matcher.find_grid_numbers()
    print(values)

    ## Abstraction
    graph = GraphSudoku()
    givens = graph.get_givens(values)

    ## DLV
    solver = DLVSolution()
    result = solver.solve(graph.get_cells(), graph.get_boxes(), givens)

    if result is None:
        print("UNSOLVABLE")
        return

    given_cells = {(g.get_row(), g.get_col()) for g in givens}
    result.sort(key=lambda value: (value.get_row(), value.get_col()))
    ## Gameplay
    for value in result:
        r, c = value.get_row(), value.get_col()
        if (r, c) in given_cells:
            continue
        cx, cy = matcher.get_cell_position(r, c)
        tap(cx, cy)
        kx, ky = matcher.get_keypad_position(value.get_value())
        tap(kx, ky)

    print("END SUDOKU")
