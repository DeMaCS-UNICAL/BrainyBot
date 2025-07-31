from AI.src.candy_crush.helper import candy_crush,MatchingCandy,draw, asp_input,retrieve_config
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
VISION_GROUND_TRUTH = os.path.join(SRC_PATH,'ground_truth', 'vision')

ABSTRACTION_GROUND_TRUTH = os.path.join(SRC_PATH,'ground_truth', 'abstraction')
VISION = False
GROUND_TRUTH = VISION_GROUND_TRUTH if VISION  else ABSTRACTION_GROUND_TRUTH

def get_center_color(img):
    h, w, _ = img.shape
    return img[h // 2, w // 2].tolist()  # ritorna [R, G, B]

def load_recursive(current_path, base_path, sprites, distances):
    rel_path = os.path.relpath(current_path, base_path)
    #if rel_path == ".":
        #rel_path = ""

    for entry in sorted(os.listdir(current_path)):
        full_path = os.path.join(current_path, entry)

        if os.path.isdir(full_path):
            load_recursive(full_path, base_path, sprites, distances)  # chiamata ricorsiva
        elif os.path.isfile(full_path) and not full_path.endswith(".ini"):
            img = getImg(full_path, color_conversion=cv2.COLOR_BGR2RGB)

            if rel_path not in sprites:
                sprites[rel_path] = {}
                distances[rel_path] = [float('inf'), float('inf')]

            sprites[rel_path][entry] = img

            height, width, _ = img.shape
            distances[rel_path][0] = min(distances[rel_path][0], width)
            distances[rel_path][1] = min(distances[rel_path][1], height)

def load_sprites_and_distances(base_path):
    sprites = {}
    distances = {}
    load_recursive(base_path, base_path, sprites, distances)
    return sprites, distances


def process_screenshots_recursively(current_path,base_path, sprites, distances):
    for entry in sorted(os.listdir(current_path)):
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            # Chiamata ricorsiva per sottodirectory
            process_screenshots_recursively(full_path,base_path,sprites, distances)
        elif not full_path.endswith(".ini"):
            screenshot = os.path.relpath(full_path, base_path)
            print(f"{screenshot}")
            #with open(output_file, 'w') as f:
            #    with redirect_stdout(f):
            game_path=os.path.relpath(current_path, base_path)
            matchingCandy = MatchingCandy(full_path,retrieve_config(),True,True,sprites=sprites[game_path],difference=distances[game_path])
            template_matches_list,candyMatrix,to_plot = matchingCandy.search()
            candies=defaultdict(int)

            output_file = os.path.join(GROUND_TRUTH, screenshot + '.txt')
            print(output_file)
            # Crea le directory di destinazione se non esistono
            generate_ground_truth(sprites, game_path, candyMatrix, to_plot, output_file,label=True)
            if VISION:
                subprocess.run(["code", output_file])
                plt.imshow(to_plot)
                plt.title(f"ABSTRACTION")
                mng = plt.get_current_fig_manager()
                mng.resize(1920, 900)
                plt.show()

def generate_ground_truth(sprites, game_path, candyMatrix, to_plot, output_file,label=False):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    met_templates = {}
    met_templates[""]=""
    colors = {}
    id=0
    width,heigth = candyMatrix.delta[0], candyMatrix.delta[1]
    with open(output_file, 'w') as f:
        with redirect_stdout(f):
            
            if VISION:
                for row in candyMatrix.get_cells():
                    for cell in row:
                        value=cell.get_value()
                        if value not in colors and value in sprites[game_path]:
                            img = sprites[game_path][value]
                            colors[value] = get_center_color(img)
                        elif value not in colors:
                                    # Se manca, fallback su colore random
                            colors[value] = [0,0,0]

                        if value not in met_templates:
                            id+=1
                            met_templates[value]=id

                        if not label:
                            print (cell.x,cell.y,met_templates[value])
                        else:                  
                            print (cell.x,cell.y,value)

                        draw(to_plot,(cell.x,cell.y),met_templates[value],width,heigth, colors[value] )
            else:
                asp = asp_input(candyMatrix)
                for cell in asp:
                    print(ASPMapper.get_instance().get_string(cell) + ".")


msg = "Description"
    
parser = argparse.ArgumentParser(description=msg)
parser.add_argument("-p", "--path", type=str, help=f"Path to the folder containing templates and screenshots subfolders for ground truth generation",required=True)
args = parser.parse_args()
if not args.path:
    args.path=""
SPRITE_PATH = os.path.join(args.path,"templates")
SCREENSHOTS_PATH = os.path.join(args.path,"screenshots")

print(SPRITE_PATH)
SPRITES,DISTANCES = load_sprites_and_distances(os.path.join(SPRITE_PATH))
process_screenshots_recursively(SCREENSHOTS_PATH,SCREENSHOTS_PATH, SPRITES,DISTANCES)