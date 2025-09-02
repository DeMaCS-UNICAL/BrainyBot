from AI.src.ball_sort.helper import MatchingBalls,asp_input,ElementsStacks,Color,get_colors
from languages.asp.asp_mapper import ASPMapper
import os
import subprocess
from contextlib import redirect_stdout
from collections import defaultdict
import  cv2
from AI.src.abstraction.helpers import getImg
from matplotlib import pyplot as plt
import argparse
import random 




SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
VISION_GROUND_TRUTH = os.path.join(SRC_PATH,'ground_truth', 'vision','ball_sort')

ABSTRACTION_GROUND_TRUTH = os.path.join(SRC_PATH,'ground_truth', 'abstraction','ball_sort')
VISION = True

def get_center_color(img):
    h, w, _ = img.shape
    return img[h // 2, w // 2].tolist()  # ritorna [R, G, B]


def process_screenshots_recursively(current_path,base_path):
    for entry in sorted(os.listdir(current_path)):
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            # Chiamata ricorsiva per sottodirectory
            process_screenshots_recursively(full_path,base_path)
        elif not full_path.endswith(".ini"):
            screenshot = os.path.relpath(full_path, base_path)
            print(f"{screenshot}")
            #with open(output_file, 'w') as f:
            #    with redirect_stdout(f):
            game_path=os.path.relpath(current_path, base_path)
            matching_balls= MatchingBalls(screenshot_path=full_path,debug=False,validation=True)
            chart:ElementsStacks = matching_balls.get_balls_chart()
            to_plot = matching_balls.get_image()
            all_balls = matching_balls.get_vision_balls()
            vision_output_file = os.path.join(VISION_GROUND_TRUTH, screenshot + '.txt')
            abstraction_output_file = os.path.join(ABSTRACTION_GROUND_TRUTH, screenshot + '.txt')
            # Crea le directory di destinazione se non esistono
            generate_ground_truth(chart,to_plot,vision_output_file,abstraction_output_file,all_balls)
            subprocess.run(["code", vision_output_file])
            #subprocess.run(["code", abstraction_output_file])
            plt.imshow(to_plot)
            plt.title(f"ABSTRACTION")
            mng = plt.get_current_fig_manager()
            mng.resize(1920, 900)
            plt.show()

def generate_ground_truth(chart:ElementsStacks, to_plot, vision_output_file,abstraction_output_file,all_balls,label=False):
    os.makedirs(os.path.dirname(vision_output_file), exist_ok=True)
    os.makedirs(os.path.dirname(abstraction_output_file), exist_ok=True)

    met_balls=[]
    colors = {}
    get_colors(chart.get_stacks())
    for empty_tube in chart.get_empty_stack():
        cv2.rectangle(to_plot, (int(empty_tube.get_x() - 20), int(empty_tube.get_y() - 50)), 
                    (int(empty_tube.get_x() + 20), int(empty_tube.get_y() + 50)), (0, 0, 255), 3)
    for tube in chart.get_stacks():
            last_y=int(tube.get_y())
            last_r=0
            if len(tube.get_elements())>0:
                for ball in tube.get_elements():
                    met_balls.append(ball)
                    x=ball.x
                    y=ball.y
                    r=ball.radius
                    c=ball.color
                    # draw the circle
                    cv2.circle(to_plot, (x, y), r, (c[0],c[1],c[2]), 10)
                    cv2.circle(to_plot, (x, y), 6, (0, 0, 0), 1)
                    #cv2.putText(to_plot, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(to_plot, f"({Color.get_color(c).get_id()})", (x , y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255-c[0], 255-c[1], 255-c[2]), 2)
                    last_y=y
                    last_r=r
            cv2.putText(to_plot, f"({tube.get_id()})", (int(tube.get_x()), last_y-last_r-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    additional_balls = []
    for ball in all_balls:
        skip=False
        for met in met_balls:
            if ball.y>2000 or (ball.x - met.x)**2 + (ball.y - met.y)**2 <= r**2:
                skip=True
                break
        if not skip:
            additional_balls.append(ball)
            met_balls.append(ball)
            x=ball.x
            y=ball.y
            r=ball.radius
            c=ball.color
            # draw the circle
            cv2.circle(to_plot, (x, y), r, (c[0],c[1],c[2]), 10)
            cv2.circle(to_plot, (x, y), 6, (0, 0, 0), 1)
            #cv2.putText(to_plot, f"({x}, {y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(to_plot, f"(Vision!)", (x , y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255-c[0], 255-c[1], 255-c[2]), 4)
            

    with open(vision_output_file, 'w') as f:
        with redirect_stdout(f):
                
                for ball in additional_balls:
                    print(ball.x,ball.y,ball.color)
                            
                for tube in sorted(chart.get_stacks(),key=lambda x:x.get_x()):
                    print(int(tube.get_x()),int(tube.get_y()),"tube")
                    if len(tube.get_elements())>0:
                        for ball in sorted(tube.get_elements(),key=lambda x:x.y):
                            x=ball.x
                            y=ball.y
                            c=ball.color
                            #bgr can be slightly different for balls of the same color, so this is the trick
                            color_to_print= Color.get_bgr_by_id(Color.get_color(c).get_id())
                            print(x,y,color_to_print)

                if VISION:
                    return
    with open(abstraction_output_file, 'w') as f:
        with redirect_stdout(f):            
            _,colors,tubes,balls,ons,_ = asp_input(chart)
            for tube in tubes:
                print(ASPMapper.get_instance().get_string(tube) + ".")
            for on in ons:
                print(ASPMapper.get_instance().get_string(on) + ".")
            for ball in balls:
                print(ASPMapper.get_instance().get_string(ball) + ".")
            for color in colors:
                print(ASPMapper.get_instance().get_string(color) + ".")
    



msg = "Description"
    
parser = argparse.ArgumentParser(description=msg)
parser.add_argument("-p", "--path", type=str, help=f"Path to the folder containing screenshots for ground truth generation",required=True)
parser.add_argument("-a", "--all", action="store_true", help="Both Vision and Abstraction ground truth")
args = parser.parse_args()
if not args.path:
    args.path=""
SCREENSHOTS_PATH = os.path.join(args.path)
VISION = not args.all
GROUND_TRUTH = VISION_GROUND_TRUTH if VISION  else ABSTRACTION_GROUND_TRUTH

process_screenshots_recursively(SCREENSHOTS_PATH,SCREENSHOTS_PATH)