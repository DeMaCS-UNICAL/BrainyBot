import math
import os
import sys
import time
import re
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
# Importa le classi aggiornate per ball_pool
from AI.src.ball_pool.dlvsolution.dlvsolution import DLVSolution, Ball, Color, Pocket, MoveAndShoot
# Funzioni helper per ottenere colori e per estrarre palline e pocket
from AI.src.ball_pool.dlvsolution.helpers import  get_pockets_and_near_ball, get_aimed_ball_and_aim_line
from AI.src.ball_pool.detect.new_detect import MatchingBallPool
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.constants import SRC_PATH
from AI.src.vision.feedback import Feedback
from matplotlib import pyplot as plt





def asp_input(balls_chart):
    # Suppongo che balls_chart fornisca una lista di oggetti Ball con coordinate,
    # e che get_balls_and_pockets() restituisca due liste: una di Pocket e una di Ball.
    balls, pockets, ghost_ball, aim_line, stick, player1_type = balls_chart

    pocket_ord = get_pockets_and_near_ball(balls, pockets)
    #aim_situation = get_aimed_ball_and_aim_line( ghost_ball,stick, aimed_ball, aim_line)
    
    input = pocket_ord.copy()
    input.extend(balls)

    return input, pocket_ord, balls, ghost_ball, aim_line, stick, player1_type
 


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
    iteration = 1
    target_ball = None

    # Inizializza il matcher per il Ball Pool
    matcher = MatchingBallPool(
        screenshot_path,
        debug=True,
        validation=(vision_val is not None),
        iteration=iteration
    )

    # Helper per acquisire e processare la visione e l'astrazione
    def acquire_abstraction():
        vision = matcher.vision(iteration)
        return matcher.abstraction(vision)


    while True:
        feedback = Feedback()
        abstraction = acquire_abstraction()

        # Verifica il turno del giocatore
        player1_turn = matcher.player1_turn
        player1_turn = True  # Forzatura per debugging
        if not player1_turn:
            time.sleep(1.5)
            continue

        # Se non sono state rilevate palline, termina l'esecuzione
        if abstraction is None:
            print("No balls found.")
            return

        # Ottieni gli input necessari dall'astrazione
        inputs = asp_input(abstraction)
        # Aspettiamo di avere:
        # input, pockets, balls, ghost_ball, aim_line, stick, player1_type
        try:
            input_data, pockets, balls, ghost_ball, aim_line, stick, player1_type = inputs
        except Exception as e:
            print("Errore nell'elaborazione dell'astrazione:", e)
            return

        if debug:
            return matcher.canny_threshold

        # Soluzione ottenuta dal modulo DLVSolution (codice commentato di gestione errori)
        solution = DLVSolution()
        # Se necessario, qui si potrebbe invocare solution.call_asp(...)
        # e gestire eventuali eccezioni, come indicato nel blocco commentato

        # Cambio della directory di lavoro (assicurarsi che CLIENT_PATH sia definito)
        os.chdir(CLIENT_PATH)

        # Ottieni le coordinate dello stick
        s_x1, s_y1, s_x2, s_y2 = stick.get_coordinates()
        pool_power = s_y2

        # Itera sulle pocket per eseguire le mosse
        for pk in pockets:
            if len(pk.get_all_balls()) == 0:
                continue
            # Ottieni la pallina target
            target_ball = pk.get_ball(0)
            x_target, y_target = target_ball.get_x(), target_ball.get_y()

            # Recupera la posizione corrente della ghost ball
            g_x, g_y = ghost_ball.get_coordinates()

            # Imposta il fattore iniziale di swipe
            swipe_factor = 0.7

            # Ciclo per muovere la ghost ball verso il target
            while True:
                if iteration == 1:
                    pool_power = s_y2
                    break 
                dist = math.sqrt((x_target - g_x) ** 2 + (y_target - g_y) ** 2)
                if target_ball is not None:
                    print(f"Palla da colpire: {target_ball.get_x(), target_ball.get_y()} {target_ball.get_type()}")
                    print(f"Pocket di destinazione: {pk.get_x(), pk.get_y()}")
                else:
                    print("Target ball NONE")
                print("Distanza ghost ball:", dist)
                if dist < 50:
                    pool_power = pool_power
                    break

                # Aggiorna dinamicamente il fattore di swipe
                swipe_factor *= (dist * 0.3)

                # Calcola nuove coordinate intermedie
                dx = abs(x_target - g_x)
                dy = abs(y_target - g_y)
                new_x = int(g_x + dx * swipe_factor)
                new_y = int(g_y + dy * swipe_factor)

                #matcher.show_result()

                # Esegue il comando swipe per muovere la ghost ball verso il punto intermedio
                os.system(
                    f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {g_x} {g_y} {new_x} {new_y}'"
                )

                # Aggiorna la posizione della ghost ball acquisendo un nuovo screenshot
                feedback.take_screenshot()
                vision = matcher.vision(iteration)
                abstraction = matcher.abstraction(vision)
                if abstraction is not None:
                    inputs = asp_input(abstraction)
                    try:
                        input_data, pockets, balls, ghost_ball, aim_line, stick, player1_type = inputs
                    except Exception as e:
                        print("Errore nell'aggiornamento dell'astrazione:", e)
                        break

                g_x, g_y = ghost_ball.get_coordinates()

            # Swipe finale con lo stick per tirare la pallina verso la pocket
            print("TIRANDO")
            os.system(
                f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'swipe {s_x1} {s_y1} {s_x2} {int(s_y2 // 1.2)}'"
            )
            time.sleep(7)
            iteration += 1

        # Al termine del ciclo per ogni pocket, acquisisce un nuovo screenshot
        feedback.take_screenshot()
