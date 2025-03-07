import os
import sys
import time
import re
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
# Importa le classi aggiornate per ball_pool
from AI.src.ball_pool.dlvsolution.dlvsolution import DLVSolution, Ball, Color, Pocket, MoveAndShoot
# Funzioni helper per ottenere colori e per estrarre palline e pocket
from AI.src.ball_pool.dlvsolution.helpers import get_colors, get_balls_and_pockets
from AI.src.ball_pool.detect.new_detect import MatchingBallPool
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.constants import SRC_PATH
from AI.src.vision.feedback import Feedback




def asp_input(balls_chart):
    # Suppongo che balls_chart fornisca una lista di oggetti Ball con coordinate,
    # e che get_balls_and_pockets() restituisca due liste: una di Pocket e una di Ball.
    balls = balls_chart["balls"]
    pockets = balls_chart["pockets"]
    facts = []

    # Se non vengono rilevate pocket, definisci alcune pocket di default (per test)
    print("Balls:", len(balls))
    piena = 0
    nera = 0
    mezza = 0
    bianca = 0

    for ball in balls:
        #print(f"Ball in loop{ball}")
        if ball.get_type() == "solid":
            piena += 1
            
        elif ball.get_type() == "striped":
            mezza += 1

        elif ball.get_type() == "eight":
            nera += 1
        
        
        elif ball.get_type() == "cue":
            bianca += 1
        
        #print(f"x = {ball.get_x()}, y = {ball.get_y()}")
        
    
    print ("Piena:", piena, "Nera:", nera, "Mezza:", mezza, "Bianca:", bianca)
   
    #print(f"Pockets:, {len(pockets)}, {[p.get_x() for p in pockets]}")
    

    """
    print("Colors:", [str(c) for c in colors])
    """

    return balls,pockets


def check_if_to_revalidate(output, last_output):
    not_done = True
    distance_sum = 0
    threshold = output[0][1]

    for o in output:
        distance_sum += o[0]
    
    if len(last_output) == 0:
        last_output = [10000, 0]
    
    last_distance_sum = last_output[0]
    last_threshold = last_output[1]
    print("distance sum:", distance_sum, "threshold:", threshold)
    if distance_sum < 2:
        persist_threshold(threshold)
        not_done = False
    elif distance_sum > last_distance_sum:
        print("distance sum:", distance_sum, "last distance:", last_distance_sum)
        persist_threshold(last_threshold)
        not_done = False
    return not_done, [distance_sum, threshold]

def persist_threshold(value):
    with open(os.path.join(SRC_PATH, "config"), "r") as f:
        x = f.read()
    with open(os.path.join(SRC_PATH, "config"), "w") as f:
        f.write(re.sub('CANNY_THRESHOLD=([^\n]+)', 'CANNY_THRESHOLD=' + str(value), x, flags=re.M))
    print("threshold set to:", value)



def ball_pool(screenshot, debug=True, vision_val = None, abstraction_val=True, iteration=0):
    #screenshot,args.debugVision,vision,abstraction,iteration

    matcher = MatchingBallPool(screenshot_path=screenshot, debug=True, validation= 
                               vision_val!= None, iteration=iteration)
    pool_chart = matcher.get_balls_chart()  # Rileva le palline e (eventualmente) le pocket o le informazioni sul tavolo
    #balls_chart = {"balls": [], "pockets": []}

    if pool_chart is not None:
        balls,pockets = asp_input(pool_chart)
    else:
        facts = []
        pockets = []
        balls = []

    
    if debug:
        return matcher.canny_threshold

    solution = DLVSolution()
    try:
        moves = solution.call_asp(balls, pockets)
    except ValueError as e:
        # In caso di errore (ad es. nessun answer set ottimale), mostra il risultato della visione
        # Nota: per accedere a __show_result, puoi usare il nome _MatchingBallPool__show_result
        matcher._MatchingBallPool__show_result()
        raise e
    moves.sort(key=lambda x: x.get_step())
 
    os.chdir(CLIENT_PATH)
    coordinates = []
    if len(moves) == 0:
        print("No moves found.")
        return
    feedback = Feedback()
    for move in moves:
        # Per ogni mossa, estraiamo l'ID della pallina da colpire e della pocket di destinazione
        ball_id = move.get_ball()
        pocket_id = move.get_pocket()
        x1, y1 = 0, 0
        x2, y2 = 0, 0
        # Otteniamo le coordinate della pallina
        for ball in balls:
            if ball.get_id() == ball_id:
                x1 = ball.get_x()
                y1 = ball.get_y()
                break
        # Otteniamo le coordinate della pocket
        for pocket in pockets:
            if pocket.get_id() == pocket_id:
                x2 = pocket.get_x()
                y2 = pocket.get_y()
                break
        coordinates.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x1} {y1}'")
        time.sleep(0.25)
        os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {x2} {y2}'")
    
    return coordinates