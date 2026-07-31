import os
import random

from AI.src.constants import TAPPY_ORIGINAL_SERVER_IP
from AI.src.meowdoku.abstraction.Meowgrid import Meowgrid
from AI.src.meowdoku.detect.grid_detection import MatchingMeowdoku
from AI.src.meowdoku.thinking.solver import Solver


def meowdoku(screenshot, debug = False, vision_validation=None, abstraction_validation=None, iteration=0, benchmark=False):

    # istanza di classe vision ...

    matching = MatchingMeowdoku(screenshot_path=screenshot, debug = False, vision_validation=None, abstraction_validation=None, iteration=0, benchmark=False)

    # matching.vision()

    # produco l'abstraction ... 
    # matching._print_boxes()
    # matching._print_all()
    #exit(0)

    abstraction = Meowgrid(matching.cells)

    solver = Solver("AI/src/meowdoku/resources/encoding.asp")

    actions = solver.solve(abstraction.export_facts())

    # non voglio vederli in ordine 
    random.shuffle(actions)

    for r,c,_ in actions: 
        box_id = abstraction.get_cell_id(r,c)[0]
        x,y = matching.get_box_touch_point(box_id)
        print(f"Touching box at row {r}, column {c} with source point ({x},{y})")
        os.system(f"python3 ../tappy-client/clients/python/client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'double-tap {x} {y} 50'")
        #os.system(f"python3 ../tappy-client/clients/python/client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x} {y}'")
        os.system("sleep 0.5")

    exit(0)


    # chiamo il solver ... (una quattro formaggi)
    # solver = DLVSolution()  
    # solver.start_asp("encoding.asp")
    # act non so che modulo era poi ci pensiamo ... 