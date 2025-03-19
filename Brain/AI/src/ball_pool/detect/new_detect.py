import os

import re
from string import Template
import cv2
import numpy as np
import math
from matplotlib import pyplot as plt
import sys 
from AI.src.ball_pool.constants import SPRITE_PATH,SRC_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.input_game_object import Circle, Container, Rectangle, TemplateMatch
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.stack import Stack
from AI.src.abstraction.elementsStack import ElementsStacks
from AI.src.ball_pool.dlvsolution.helpers import AimLine, BPoolColor, Color, Ball, Pocket, MoveAndShoot, GameOver


class MatchingBallPool:

    # Parametri relativi al campo (se necessari per ulteriori controlli)
    #446 / 2400 = 0.185
    #2400 x  1080 

    """X_MIN = 446
    Y_MIN = 169
    X_MAX = 2067
    Y_MAX = 1073"""
    #STICK_COORDS = 221, 362, 221, 887


    PERC_X_MIN = 0.185
    PERC_Y_MIN = 0.156
    PERC_X_MAX = 0.861
    PERC_Y_MAX = 0.993

    PERC_X_MIN_PLAYER_AREA = 0.181
    PERC_X_MAX_PLAYER_AREA = 0.859
    PERC_Y_MAX_PLAYER_AREA = 0.159

    PERC_STICK_COORDS = 0.092, 0.335, 0.092, 0.820

    # Parametri per la rilevazione delle palline
    BALLS_MIN_DIST = 1
    BALLS_MIN_RADIUS = 20
    BALLS_MAX_RADIUS = 25
    
    # Parametri per la rilevazione dei pocket (buche) tramite rilevamento dei cerchi
    POCKETS_MIN_DIST = 400        # Distanza minima tra le buche
    POCKETS_MIN_RADIUS = 33       # Raggio minimo in pixel per i pocket
    POCKETS_MAX_RADIUS = 50

    player1_pic_pos = 1018
    player2_pic_pos = 1356

    #Calibrerò meglio le costanti 

    def __init__(self, screenshot_path, debug=False, validation=False, iteration=0):
        self.screenshot = screenshot_path
        self.debug = debug
        self.validation = validation
        self.iteration = iteration
        self.image = None
        self.__gray = None
        self.__output = None

        self.detection_result = None
        self.__balls: list = []
        self.__pockets: list = []  # Ora i pocket verranno rilevati via circle detection
        self.player1_turn = False

        #self.table_area = MatchingBallPool.X_MIN, MatchingBallPool.Y_MIN, MatchingBallPool.X_MAX, MatchingBallPool.Y_MAX 

        # Recupera la configurazione dal file config
        self.canny_threshold, self.proportion_tolerance, self.size_tolerance = self.retrieve_config()
        
        self.canny_threshold = self.adjust_threshold(iteration)
        

    def adjust_threshold(self, iteration):
        if iteration == 0:
            return self.canny_threshold
        return self.canny_threshold + iteration * 10

    def retrieve_config(self):
        with open(os.path.join(SRC_PATH, "config"), "r") as f:
            x = f.read()
        canny_threshold = int(re.search("CANNY_THRESHOLD=([^\n]+)", x, flags=re.M).group(1))
        # Anche se non usiamo template per i pocket, manteniamo la configurazione per eventuali usi futuri
        proportion_tolerance = (
            float(re.search("POCKET_PROPORTION_TOLERANCE=([^\n]+)", x, flags=re.M).group(1))
            if re.search("POCKET_PROPORTION_TOLERANCE=([^\n]+)", x, flags=re.M)
            else 0.1
        )
        size_tolerance = (
            float(re.search("POCKET_SIZE_TOLERANCE=([^\n]+)", x, flags=re.M).group(1))
            if re.search("POCKET_SIZE_TOLERANCE=([^\n]+)", x, flags=re.M)
            else 0.1
        )
        return canny_threshold, proportion_tolerance, size_tolerance


    def vision(self, iteration=0):
        self.iteration = iteration
        self.finder = ObjectsFinder(self.screenshot, debug=self.debug, threshold=0.8, validation=self.validation)

        self.image = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot))
        self.full_image = self.image.copy()  # conserva l'immagine completa per la visualizzazione
        
        if not self.debug and self.validation is None:
            plt.imshow(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
            plt.title("Screenshot")
            plt.show()
        
        # Carica la versione in scala di grigi e applica pre-elaborazione
        self.__gray = getImg(os.path.join(SCREENSHOT_PATH, self.screenshot), gray=True)
        self.__gray = cv2.GaussianBlur(self.__gray, (5, 5), 0)
        self.__gray = cv2.equalizeHist(self.__gray)
        
        img_height = self.image.shape[0]
        img_width = self.image.shape[1]

        self.table_area = int(self.PERC_X_MIN * img_width), int(self.PERC_Y_MIN * img_height), int (self.PERC_X_MAX * img_width), int(self.PERC_Y_MAX * img_height)
        self.pool_x_min, self.pool_y_min, self.pool_x_max, self.pool_y_max = self.table_area

        self.player_area = int(self.PERC_X_MIN_PLAYER_AREA * img_width), 0, int(self.PERC_X_MAX_PLAYER_AREA * img_width), int(self.PERC_Y_MAX_PLAYER_AREA * img_height)
        self.X_MIN_PLAYER_AREA, self.Y_MIN_PLAYER_AREA, self.X_MAX_PLAYER_AREA, self.Y_MAX_PLAYER_AREA = self.player_area

        self.STICK_COORDS = int(self.PERC_STICK_COORDS[0] * img_width), int(self.PERC_STICK_COORDS[1] * img_height), int(self.PERC_STICK_COORDS[2] * img_width), int(self.PERC_STICK_COORDS[3] * img_height)
    
        # Salviamo self.__output come immagine completa per la visualizzazione finale
        self.__output = self.image.copy()
        self.img_width = self.image.shape[1]

        player_squares = self.__detect_players_pic(area=( self.pool_x_min, self.pool_y_min, self.pool_x_max, self.pool_y_max))

        ghost_ball = self.finder.detect_ghost_ball(
            Circle(17, 100, 23,
                   (self.pool_x_min, self.pool_y_min, self.pool_x_max, self.pool_y_max),
                   )
        )
        if ghost_ball == None:
            print("Ghost ball not found")
            """ghost_ball = self.finder._template_matching(
               TemplateMatch(
                     {
                        "red_ghost_ball": getImg(os.path.join(SPRITE_PATH, "red_ghost_ball.png"), gray=True)
                     },
                     {
                        "red_ghost_ball": 0.4
                     },
                     find_all=True,
                     grayscale=True
               )

            )
            for gb in ghost_ball:
                print(f"x {gb.x} y {gb.y} labels {gb.label} confidance {gb.confidence}")"""
            
        
        aim_line = None
        if ghost_ball != None:
            self.gx, self.gy, self.gr, self.isWhite = ghost_ball 
       
            

        #pocket_circles = self.find_pocket_pool_houghCircles(area=(x,y,w,h))

        if iteration == 0:
            pocket_circles = self.finder._find_pockets_pool_contour(
                Circle(self.POCKETS_MIN_RADIUS, 40, self.POCKETS_MAX_RADIUS+2,
                    ( self.pool_x_min, self.pool_y_min, self.pool_x_max, self.pool_y_max),
                    )
            )

            self.__pockets = pocket_circles

        ball_circles = self.finder._find_balls_pool_contour(
            Circle(self.BALLS_MIN_RADIUS-1, 100, self.BALLS_MAX_RADIUS+2,
                   ( self.pool_x_min + 60, self.pool_y_min + 60,
                     self.pool_x_max - 60, self.pool_y_max - 60),

                   (self.gx, self.gy, self.gr) if ghost_ball != None else None,
                   )
        )

        players_balls = self.finder._find_balls_pool_contour(
            Circle(self.BALLS_MIN_RADIUS-1, 70, self.BALLS_MAX_RADIUS+2,
                   (self.X_MIN_PLAYER_AREA, 0, self.X_MAX_PLAYER_AREA, self.Y_MAX_PLAYER_AREA),
                   None,
                   ), area_threshold=10,circularity_threshold=0.5
        )

        # Assegniamo per riferimento interno
        self.__balls = ball_circles
        
        self.__ghost_balls = ghost_ball
        self.__player_squares = player_squares
        self.__player_balls = players_balls
        
        if self.player1_turn:
            print("Player 1 turn")
        else:
            print("Player 2 turn")

        print(f"{len(self.__pockets)} Pockets")
        print(f"{ghost_ball} Ghost ball")
        print(f"{len(ball_circles)} Balls")
        print(f"{len(players_balls)} Player balls")
        #print(f"{len(aim_line) if aim_line != None else None} Aim line")

        result =  {"balls": ball_circles, "ghost_ball": ghost_ball, 
                     "aim_line": aim_line, "player_ball_type": "solid"}
        
        # Se non vengono rilevate pocket, definisci alcune pocket di default (per test)
        return result
    
    
    def __detect_players_pic(self, area=None):
        squares = self.finder.detect_square_boxes()
        if area is not None:
            x_min, y_min, x_max, y_max = area 
            squares = [sq for sq in squares if x_min <= sq[0].x <= x_max and sq[0].y <= y_min]
            
        if squares is not None and len(squares) > 0:
            #print(f"len find squares {len(squares)}")
            # Ordina la lista in base al clear_count (indice 1 della tupla), decrescente
            squares= sorted(squares, key=lambda item: item[1], reverse=True)
            squares = squares[:2]
            brighter_square_x = squares[0][0].x
            if len(squares) > 1:
                second_square_x = squares[1][0].x
                self.player1_turn = brighter_square_x < second_square_x
            else:
                if squares[0][1] > 50:
                    if squares[0][0].x <= self.player1_pic_pos:
                        self.player1_turn = True
                    else:
                        self.player1_turn = False

        
        """for sq in squares:
            print(f"Square {sq[0].x} {sq[0].y} {sq[1]}")"""

        return squares
    

    
    def abstract_balls(self, circles):
        if circles is None:
            return []
        raw_balls = []
        # Per ogni cerchio rilevato, crea una Ball assegnandole il BPoolColor
        for c in circles:
            x = c.x
            y = c.y
            r = c.radius
            dominant_col = c.color  # patch dell'immagine della pallina
            white_ratio : float= c.white_ratio 

            #print(f"x: {x} y: {y} r: {r} color: {patch}")
            bpColor = BPoolColor.get_color(dominant_col)

            ball_obj = Ball()
            ball_obj.set_x(x)
            ball_obj.set_y(y)
            ball_obj.set_r(r)
            ball_obj.set_color(bpColor)
            ball_obj.set_white_ratio(white_ratio)
            raw_balls.append(ball_obj)
        
        # Raggruppa le palle per categoria di colore e assegna il tipo ("piena" -"mezza" - "otto" - "bianca")
        final_balls, red_ghost = BPoolColor.assign_ball_types(raw_balls)
        return final_balls,red_ghost

    def abstract_pockets(self, circles):
        """
        Converte i cerchi (x, y, r) in oggetti Pocket.
        Esegue eventuale NMS e filtraggio dei duplicati.
        """
        if circles is None:
            return []
        raw_pockets = []
        for c in circles:

            p = Pocket(c.x, c.y)
            p.set_r(c.radius)
            raw_pockets.append(p)

        return raw_pockets
    

    def abstraction(self, vision_output, reset=True) -> ElementsStacks:
        """if reset:
            Ball.reset()
            Pocket.reset()
            Color.reset()
            """
        
        result = {"balls": [], "pockets": [], "ghost_ball":Ball , "aim_line": [] ,"aimed_ball": Ball}

        ball_circles = vision_output["balls"]
        ghost_ball = vision_output["ghost_ball"]
        

        final_balls, red_ghost = self.abstract_balls(ball_circles)

        if self.__ghost_balls == None:

            if red_ghost != None:
                self.__ghost_balls = red_ghost
                self.gx, self.gy, self.gr, self.isWhite = red_ghost.get_x(), red_ghost.get_y(), red_ghost.get_r(), False

            ghost_ball = (400, 400, 0, False)
            self.gx, self.gy, self.gr, self.isWhite = ghost_ball

        if self.iteration == 0:
            self.__pockets = self.abstract_pockets(self.__pockets)

        result["pockets"] = self.__pockets

        ghost_ball = Ball()
        ghost_ball.set_x(self.gx)
        ghost_ball.set_y(self.gy)
        ghost_ball.set_r(self.gr)
        ghost_ball.set_ghost_type("GHOST" if self.isWhite else "RED GHOST")

        aim_line, aimed_ball = self.finder.compute_target_direction(
                                                    all_balls=final_balls,
                                                    ghost_ball=(self.gx, self.gy, self.gr),
                                                    area=(self.pool_x_min, self.pool_y_min, self.pool_x_max, self.pool_y_max)
                                                )
            
        
        result["balls"] = final_balls
        result["stick"] = AimLine(self.STICK_COORDS[0], self.STICK_COORDS[1], self.STICK_COORDS[2], self.STICK_COORDS[3])

        result["ghost_ball"] = ghost_ball
        result["aim_line"] = aim_line
        result["aimed_ball"] = aimed_ball
        self.__aim_line = result["aim_line"]

        # Salviamo il risultato in un attributo interno
        self.__result = result

        self.__balls = result["balls"]
        self.__ghost_balls = result["ghost_ball"]

        if not self.validation is None and self.debug:
            self.show_result()  # Nessun parametro"""

        # Se non vengono rilevate pocket, definisci alcune pocket di default (per test)
        piena = 0
        nera = 0
        mezza = 0
        bianca = 0

        for ball in final_balls:
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

        return result, self.gx != 400

    

    def show_result(self):
        scale_factor = 1.0
        width = int(self.image.shape[1] * scale_factor)
        height = int(self.image.shape[0] * scale_factor)
        dim = (width, height)

        img_copy = self.__output.copy()
        

        # Disegna il rettangolo dell'area (in rosso)
        cv2.rectangle(img_copy, ( self.pool_x_min, self.pool_y_min), (self.pool_x_max, self.pool_y_max), (255, 0, 0), 5)

        # Disegna le palline (in verde)
        for ball in self.__balls:
            x, y, r = ball.get_x(), ball.get_y(), ball.get_r()
            cv2.circle(img_copy, (x, y), r, (0, 255, 0), 3)
            cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
            # Testo con bordo nero e testo verde
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
        
        for ball in self.__player_balls:
            x, y, r = ball.x, ball.y, ball.radius
            cv2.circle(img_copy, (x, y), r, (255, 0, 0), 3)
            cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
            # Testo con bordo nero e testo verde
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(img_copy, f"({x}, {y}) {r}", (x + r, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Disegna i pocket (in giallo)
        for pocket in self.__pockets:
            x, y, r = pocket.get_x(), pocket.get_y(), pocket.get_r()
            cv2.circle(img_copy, (x, y), r, (0, 255, 255), 3)
            cv2.circle(img_copy, (x, y), 4, (0, 0, 0), 1)
            cv2.putText(img_copy, f"P({x}, {y}) {r}", (x + r, y + r),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(img_copy, f"P({x}, {y}) {r}", (x + r, y + r),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
        """if len(self.__stick) != 0:
            for rect in self.__stick:
                x = rect.x
                y = rect.y
                width = rect.width
                heigth = rect.heigth

                cv2.rectangle(img_copy, (x, y), (x+width, y+heigth), (255, 255, 255), 5)
        """

        # Supponiamo che self.__aim_line sia una lista di tuple, in cui ogni tupla è:
        # (ball_center_x, ball_center_y, direction_vector, len_line)
        # dove direction_vector è una tupla (dx, dy) già normalizzata.

        if self.__aim_line is not None:
        
            x1, y1, x2, y2 = self.__aim_line.get_x1(), self.__aim_line.get_y1(), self.__aim_line.get_x2(), self.__aim_line.get_y2()
            cv2.line(img_copy, (x1, y1), (x2, y2), (255, 0, 0), 3)
            cv2.putText(img_copy, f"Aim Line", (x1, y1),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)


        x, y, r, type = self.__ghost_balls.get_x(), self.__ghost_balls.get_y(), self.__ghost_balls.get_r(), self.__ghost_balls.get_ghost_type()
        
        cv2.circle(img_copy, (x, y), r, (60,20,220) if type == "GHOST"  else (255,255,255), 4)
        cv2.circle(img_copy, (x, y), 6, (0, 0, 0), 1)
        # Testo con bordo nero e testo verde
        cv2.putText(img_copy, f"({x}, {y}) {r}", (x - 200, y -50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
        cv2.putText(img_copy, f"({x}, {y}) {r}", (x - 200, y - 50 ),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (60,20,220) if type == "GHOST"  else (255,255,255), 2)
        
        #purple bgr 
        x_above, y_above, x_below, y_below = self.STICK_COORDS

        cv2.line(img_copy, (x_above, y_above), (x_below, y_below), (255, 0, 255), 3)
        cv2.putText(img_copy, f"Stick", (x_above, y_above),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        

        if self.__player_squares is not None and len(self.__player_squares) != 0:
            player_cont = 0
            for rect, clear_count in self.__player_squares:
                x = rect.x
                y = rect.y
                width = rect.width
                heigth = rect.heigth
                if player_cont == 0:
                    cv2.rectangle(img_copy, (x, y), (x+width, y+heigth), (0, 0, 255), 5)
                else:
                    cv2.rectangle(img_copy, (x, y), (x+width, y+heigth), (255,0,255), 5)
                player_cont+=1
            player_cont = 0

        # Ridimensionamento per la visualizzazione
        resized_input = cv2.cvtColor(cv2.resize(self.image, dim, interpolation=cv2.INTER_LINEAR), cv2.COLOR_BGR2RGB)
        resized_gray = cv2.cvtColor(cv2.resize(self.__gray, dim, interpolation=cv2.INTER_LINEAR), cv2.COLOR_GRAY2RGB)
        resized_output = cv2.cvtColor(cv2.resize(img_copy, dim, interpolation=cv2.INTER_LINEAR), cv2.COLOR_BGR2RGB)

        # Mostra i risultati
        fig, axes = plt.subplots(3, 1, figsize=(8, 18))

        axes[0].imshow(resized_input)
        axes[0].set_title("Input Image")
        axes[0].axis("off")

        axes[1].imshow(resized_gray)
        axes[1].set_title("Gray Image")
        axes[1].axis("off")

        axes[2].imshow(resized_output)
        axes[2].set_title("Detection Output")
        axes[2].axis("off")

        plt.tight_layout()
        plt.show()
        if not self.debug:
            plt.pause(0.1)
