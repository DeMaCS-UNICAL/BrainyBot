from AI.src.candy_crush.helper import candy_crush,MatchingCandy,draw
import constants
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
SPRITE_PATH = os.path.join(RESOURCES_PATH, 'match3')
SCREENSHOTS_PATH= os.path.join(constants.SCREENSHOT_PATH,'match3')
GROUND_TRUTH = os.path.join(SRC_PATH, 'ground_truth')

def get_center_color(img):
    h, w, _ = img.shape
    return img[h // 2, w // 2].tolist()  # ritorna [R, G, B]

def load_recursive(current_path, base_path, sprites, distances):
    rel_path = os.path.relpath(current_path, base_path)
    #if rel_path == ".":
        #rel_path = ""

    for entry in os.listdir(current_path):
        full_path = os.path.join(current_path, entry)

        if os.path.isdir(full_path):
            load_recursive(full_path, base_path, sprites, distances)  # chiamata ricorsiva
        elif os.path.isfile(full_path):
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
    if current_path == base_path:
        for k in distances:
            print(k)
        for k in sprites:
            print(k)
    for entry in os.listdir(current_path):
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            # Chiamata ricorsiva per sottodirectory
            process_screenshots_recursively(full_path,base_path,sprites, distances)
        else:
            screenshot = os.path.relpath(full_path, constants.SCREENSHOT_PATH)
            print(f"{screenshot}")
            #with open(output_file, 'w') as f:
            #    with redirect_stdout(f):
            game_path=os.path.relpath(current_path, base_path)
            matchingCandy = MatchingCandy(screenshot,distances[game_path],defaultdict(lambda:0.75),True,True,sprites=sprites[game_path])
            template_matches_list,candyMatrix,to_plot = matchingCandy.search()
            candies=defaultdict(int)

            output_file = os.path.join(GROUND_TRUTH, screenshot.strip(".png") + '.txt')
            print(output_file)
            # Crea le directory di destinazione se non esistono
            generate_ground_truth(sprites, game_path, candyMatrix, to_plot, output_file)
            subprocess.run(["code", output_file])
            plt.imshow(to_plot)
            plt.title(f"ABSTRACTION")
            plt.show()

def generate_ground_truth(sprites, game_path, candyMatrix, to_plot, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    met_templates = {}
    met_templates[""]=""
    colors = {}
    id=0
    width,heigth = candyMatrix.delta[0], candyMatrix.delta[1]
    with open(output_file, 'w') as f:
        with redirect_stdout(f):
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
                    print (cell.x,cell.y,met_templates[value])                            
                    draw(to_plot,(cell.x,cell.y),met_templates[value],width,heigth, colors[value] )


msg = "Description"
    
parser = argparse.ArgumentParser(description=msg)
parser.add_argument("-p", "--path", type=str, help=f"Name of the folder in {SCREENSHOTS_PATH} on which you want to recurse to generate the ground truth",required=False)
args = parser.parse_args()
if not args.path:
    args.path=""
print(SPRITE_PATH)
SPRITES,DISTANCES = load_sprites_and_distances(os.path.join(SPRITE_PATH,args.path))
path = os.path.join(SCREENSHOTS_PATH,args.path)
process_screenshots_recursively(path,path, SPRITES,DISTANCES)