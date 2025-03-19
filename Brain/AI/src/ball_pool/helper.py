import math
import os
import sys
import time
import re
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
# Importa le classi aggiornate per ball_pool
from AI.src.ball_pool.dlvsolution.dlvsolution import DLVSolution, Ball, Color, Pocket, MoveAndShoot
# Funzioni helper per ottenere colori e per estrarre palline e pocket
from AI.src.ball_pool.dlvsolution.helpers import  get_balls_and_near_pockets, get_aimed_ball_and_aim_line
from AI.src.ball_pool.detect.new_detect import MatchingBallPool
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.constants import SRC_PATH
from AI.src.vision.feedback import Feedback
from matplotlib import pyplot as plt





def asp_input(balls_chart):
    # Suppongo che balls_chart fornisca una lista di oggetti Ball con coordinate,
    # e che get_balls_and_pockets() restituisca due liste: una di Pocket e una di Ball.
    pockets = balls_chart["pockets"]
    balls = balls_chart["balls"]
    ghost_ball = balls_chart["ghost_ball"]
    aim_line = balls_chart["aim_line"]
    aimed_ball = balls_chart["aimed_ball"]
    stick = balls_chart["stick"]

    pocket_ord, balls = get_balls_and_near_pockets(balls, pockets, )
    aim_situation = get_aimed_ball_and_aim_line( ghost_ball,stick, aimed_ball, aim_line)
    
    input = pocket_ord.copy()
    input.extend(balls)

    return input, pockets, balls, ghost_ball, aim_line, aimed_ball, aim_situation, stick



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



def ball_pool(screenshot_path, debug=True, vision_val = None, abstraction_val=True, iteration=0):
    #screenshot,args.debugVision,vision,abstraction,iteration
    
    x_test_aim_to, y_test_aim_to= 1870,935
    
    # Ciclo di validazione del feedback: acquisisce una nuova immagine e confronta l'output con quello atteso

    x_target, y_target = 1870, 935
    
    iteration = 1
    while True:
        feedback = Feedback()
        feedback.take_screenshot()
        matcher = MatchingBallPool(screenshot_path, debug=True, validation= 
                               vision_val!= None, iteration=iteration)
        
        vision = matcher.vision()

        abstraction, g_ball_detected = matcher.abstraction(vision)
        print("Abstraction:", abstraction, "Ghost ball detected:", g_ball_detected)

        player1_turn = matcher.player1_turn
        print("Player1 turn:", player1_turn)
        player1_turn = True #debugging
        if not player1_turn:
            time.sleep(1.5)
            continue
        
        if abstraction is not None:
                input, pockets, balls, ghost_ball, aim_line, aimed_ball, aim_situation, stick = asp_input(abstraction)
        else:
            print("No balls found.")
            return
                                                                                    
        if debug:
            return matcher.canny_threshold

        solution = DLVSolution()

        try:
            moves = solution.call_asp(balls, pockets, aim_situation)
        except Exception as e:
            raise e

    
        os.chdir(CLIENT_PATH)
        coordinates = []
        if len(moves) == 0:
            print("No moves found.")
            return
        
        # Per ogni mossa individuata, esegue le operazioni necessarie
        s_x1, s_y1, s_x2, s_y2 = stick.get_coordinates()

        for move in moves:
            # Estrae l'ID della pallina da colpire, quello della pocket di destinazione e dello stick
            ball_id = move.get_aimed_ball()
            pocket_id = move.get_pocket()
            stick_id = move.get_stick()

            # Ottieni le coordinate dello stick (necessarie per eseguire lo swipe finale)

            # Ottiene le coordinate attuali della ghost ball
            g_x, g_y = ghost_ball.get_coordinates()

            # Ricava le coordinate della pallina da colpire
            for ball in balls:
                if ball.get_id() == ball_id:
                    x_target, y_target = ball.get_x(), ball.get_y()
                    print("Pallina da colpire:", x_target, y_target)
                    break
            
            swipe_factor = 0.7  # Fattore di spostamento: 70% della distanza residua

            # Ciclo per spostare la ghost ball verso la posizione target finché non è sufficientemente vicina
            while True:
                dist = math.sqrt((x_target - g_x)**2 + (y_target - g_y)**2)
                print("Distanza ghost ball:", dist)
                if dist < 50:
                    break
                
                # Fattore dinamico: maggiore se la ghost ball è lontana, minore se è vicina
                if dist > 200:
                    swipe_factor = 0.95
                elif dist > 100:
                    swipe_factor = 0.85
                else:
                    swipe_factor = 0.75

                dx = x_target - g_x
                dy = y_target - g_y
                new_x = int(g_x + dx * swipe_factor)
                new_y = int(g_y + dy * swipe_factor)

                ## Esegue il comando swipe per muovere la ghost ball verso il nuovo punto intermedio
                os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {g_x} {g_y} {new_x} {new_y}'")
                time.sleep(0.0005)

                # Aggiorna la posizione della ghost ball acquisendo nuovamente l'immagine e ricavando le nuove coordinate
                feedback.take_screenshot()
                #matcher = MatchingBallPool(screenshot_path, debug=True, validation= vision_val!= None, iteration=iteration)
                
                vision = matcher.vision(iteration)
                abstraction, g_ball_detected = matcher.abstraction(vision)
                #1655, 260   1044, 260
                if abstraction is not None:
                    _, _, _, ghost_ball, _, _, _, _ = asp_input(abstraction)
                if not g_ball_detected:
                    print("Ghost ball non rilevata.")
                    g_x, g_y = 1044, 260
                else:
                    g_x, g_y = ghost_ball.get_coordinates()
            
                # Esegue lo swipe finale
                """plt.imshow( matcher.full_image)
                plt.title(f"VISION")
                plt.pause(0.1)

                plt.show()"""

            # Esegue lo swipe finale con lo stick per colpire la pallina verso la pocket
            print("TIRANDO")
            os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {s_x1} {s_y1} {s_x2} {int(s_y2//1.2)}'")
            time.sleep(7)
            iteration +=1