import math
import os
import sys
import time
import re
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
# Importa le classi aggiornate per ball_pool
from AI.src.ball_pool.dlvsolution.dlvsolution import DLVSolution, Ball, Color, Pocket, MoveAndShoot
# Funzioni helper per ottenere colori e per estrarre palline e pocket
from AI.src.ball_pool.dlvsolution.helpers import  get_best_pair_to_shoot
from AI.src.ball_pool.detect.new_detect import MatchingBallPool
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.constants import SRC_PATH
from AI.src.vision.feedback import Feedback
from matplotlib import pyplot as plt





def asp_input(balls_chart):
    # Suppongo che balls_chart fornisca una lista di oggetti Ball con coordinate,
    # e che get_balls_and_pockets() restituisca due liste: una di Pocket e una di Ball.
    balls, pockets, ghost_ball, aim_line, stick, player1_type = balls_chart

    pocket_ord = get_best_pair_to_shoot(balls, pockets, player1_type)
    #aim_situation = get_aimed_ball_and_aim_line( ghost_ball,stick, aimed_ball, aim_line)
    

    return  pocket_ord, balls, ghost_ball, aim_line, stick, player1_type
 


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


def ball_pool(screenshot_path, debug=True, vision_val=None, abstraction_val=True, iteration=0):

    # Inizializzazione dei target e della ghost ball
    x_target, y_target = 1, 1
    target_ball = None

    # Inizializza il matcher per il Ball Pool
    matcher = MatchingBallPool(
        screenshot_path,
        debug=True,
        validation=(vision_val is not None),
        iteration=iteration
    )


    TOLERANCE = 60         # Soglia minima per considerare raggiunto il target
    MAX_ITERATIONS = 100   # Per evitare loop infiniti
    MIN_STEP_FACTOR = 0.8  # Valore minimo dello step factor
    BASE_STEP_FACTOR = 2.0 # Step factor di base

    iteration = 1
    
    while True:
        feedback = Feedback()
        if iteration >1:
            feedback.take_screenshot()
        
        vision = matcher.vision(iteration)
        abstraction = matcher.abstraction(vision)

        s_x1, s_y1, s_x2, s_y2 = matcher.STICK_COORDS


        # Verifica il turno del giocatore
        player1_turn = matcher.player1_turn
        player1_turn = True  # Forzatura per debugging
        if not player1_turn:
            time.sleep(1.5)
            continue
        if iteration > 1:
            try:
                pocket, balls, ghost_ball, aim_line, stick, player1_type = asp_input(abstraction)
    
                if len(pocket.get_all_balls()) > 0:
                    print(f"Palla rilevata in pocket: {pocket.get_all_balls()[0].get_type()}")
                    target_ball = pocket.get_all_balls()[0]
                    x_target, y_target = target_ball.get_x(), target_ball.get_y()

                # Recupera la posizione corrente della ghost ball
                g_x, g_y = ghost_ball.get_coordinates()
            except Exception as e:
                print("Errore nell'elaborazione dell'astrazione:", e)
                return

        moves_before_shoot = 0
        while moves_before_shoot < MAX_ITERATIONS:
            if iteration == 1:
                shoot_power = s_y2
                break
            
            # Calcola la distanza corrente tra ghost ball (g_x, g_y) e target (x_target, y_target)
            dx_total = abs(g_x - x_target)
            dy_total = abs(g_y - y_target)
            dist = math.sqrt(dx_total ** 2 + dy_total ** 2)

            print(f"Target ball: {target_ball.get_type()} in posizione ({x_target}, {y_target})")
            print(f"Distanza tra ghost ball e target: {dist}")
            if dist < TOLERANCE:
                shoot_power = s_y2
                break
            
            # Calcola lo spostamento del 20% della differenza tra ghost ball e target,
            # applicando il segno corretto in base alla posizione della ghost ball.
            new_x = x_target + int(0.20 * abs(g_x - x_target)) * (1 if g_x < x_target else -1)
            new_y = y_target + int(0.20 * abs(g_y - y_target)) * (1 if g_y < y_target else -1)

            matcher.show_result()

            # Esegue il comando swipe per muovere la ghost ball verso il punto intermedio
            os.chdir(CLIENT_PATH)
            os.system(
                f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {g_x} {g_y} {new_x} {new_y}'"
            )

            feedback.take_screenshot()
            vision = matcher.vision(iteration)
            abstraction = matcher.abstraction(vision)

            g_x, g_y = matcher.ghost_ball.get_coordinates()
            moves_before_shoot += 1


        # Swipe finale con lo stick per tirare la pallina verso la pocket
        print("TIRANDO")
        os.chdir(CLIENT_PATH)
        os.system(
            f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {s_x1} {s_y1} {s_x2} {int(shoot_power)}'"
        )
        iteration += 1
        time.sleep(7)
        

            
            


