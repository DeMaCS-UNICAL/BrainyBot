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





def choose_target_ball(balls_chart):
    # Suppongo che balls_chart fornisca una lista di oggetti Ball con coordinate,
    # e che get_balls_and_pockets() restituisca due liste: una di Pocket e una di Ball.
    balls, pockets, ghost_ball, player1_type = balls_chart

    chosen_ball, chosen_pocket, move_aim = get_best_pair_to_shoot(balls, pockets, player1_type, ghost_ball)
    #aim_situation = get_aimed_ball_and_aim_line( ghost_ball,stick, aimed_ball, aim_line)
    
    return  chosen_ball, chosen_pocket, ghost_ball, move_aim


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


def swipe_command(x1, y1, x2, y2):
    """Esegue il comando swipe tramite il client."""
    os.chdir(CLIENT_PATH)
    os.system(
        f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {x1} {y1} {x2} {y2}'"
    )


def ball_pool(screenshot_path, debug=True, vision_val=None, abstraction_val=True, iteration=0):

    # Inizializzazione dei target e della ghost ball
    ball_x, y_target = 1, 1

    # Inizializza il matcher per il Ball Pool
    matcher = MatchingBallPool(
        screenshot_path,
        debug=True,
        validation=(vision_val is not None),
        iteration=iteration
    )
    feedback = Feedback()

    MAX_ITERATIONS = 5   # Per evitare loop infiniti
    SHOOT_SCALE_FACTOR = 0.6
    iteration = 1

    while True:
        if iteration >1:
            feedback.take_screenshot()
        
        vision = matcher.vision(iteration)
        abstraction = matcher.abstraction(vision)

        s_x1, s_y1, s_x2, s_y2 = matcher.STICK_COORDS

        shoot_power = s_y2

        # Verifica il turno del giocatore
        player_turn = matcher.player_turn
        #player_turn = True  # Forzatura per debugging
        if not player_turn == 1:
            iteration += 1
            print("WAITING FOR PLAYER 1")
            time.sleep(1.5)
            continue
        if iteration > 1:
            try:
                print("Solving...")
 
                chosen_ball, chosen_pocket, ghost_ball, move_aim = choose_target_ball(abstraction)
    
                print(f"Palla rilevata in pocket: {chosen_pocket.get_id()}")
                if move_aim is not None:
                    print(f"Move aim: {move_aim}")
                    x_target, y_target = move_aim[0], move_aim[1]
                    tolerance = 16
                else:
                    x_target, y_target = chosen_pocket.get_x(), chosen_pocket.get_y()
                    tolerance = 50
                
                # Recupera la posizione corrente della ghost ball
                temp_g_x, temp_g_y = ghost_ball.get_coordinates()
                if temp_g_x == 400 and temp_g_y == 400:
                    print("Ghost ball NON TROVATA, swipo e redetecto")
                    need_to_redetect_cue_ball = True
                    # Esegue il comando swipe per muovere la ghost ball verso il punto intermedio
                    swipe_command(temp_g_x, temp_g_y, s_x1, s_y1)
                    continue
                else:
                    g_x, g_y = ghost_ball.get_coordinates()

            except Exception as e:
                print("Errore nell'elaborazione del solver:", e)
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

            print(f"Target ball: {chosen_ball.get_type()} in posizione ({x_target}, {y_target})")
            print(f"Distanza tra ghost ball e target: {dist}")

            if dist < tolerance:
                shoot_power *= 0.70
                shoot_power = int(shoot_power)
                break
            
            # Calcola lo spostamento del 30% della differenza tra ghost ball e target,
            # applicando il segno corretto in base alla posizione della ghost ball.

            new_x = x_target + int(0.25 * abs(g_x - x_target)) * (1 if g_x < x_target else -1)
            new_y = y_target + int(0.25 * abs(g_y - y_target)) * (1 if g_y < y_target else -1)

            #matcher.show_result()

            # Esegue il comando swipe per muovere la ghost ball verso il nuovo punto intermedio
            swipe_command(g_x, g_y, new_x, new_y)

            feedback.take_screenshot()
            vision = matcher.vision(iteration)
            abstraction = matcher.abstraction(vision)

            g_x, g_y = matcher.ghost_ball.get_coordinates()

            moves_before_shoot += 1
            iteration += 1
            print("++++++++++")


        # Swipe finale con lo stick per tirare la pallina verso la pocket
        print(f"TIRANDO{' per tempo' if moves_before_shoot == MAX_ITERATIONS else ''}")
        swipe_command(s_x1, s_y1, s_x2, int(shoot_power))

        iteration += 1
        print("------------------------")
        time.sleep(7.5)
        

            
            


