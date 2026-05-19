import os
import random
import sys
import cv2
import argparse
import json
import matplotlib.pyplot as plt
from AI.src.agnostic_GFD.EdgeDetectionTechniques2 import retain_candy_region
from AI.src.agnostic_GFD.extrusion_remover import process_image
from AI.src.agnostic_GFD.autotuning import  genetic_algorithm_tune_parameters
from AI.src.agnostic_GFD.HSV_Horizontal_Vertical_merged_ImageMatching2 import process_image_with_parameters,get_grid
import time


def run_controller(image_path, population, generations, tolerance, gamename=None, tune=None, save_ids=False, debug=False):
    start = time.perf_counter()


    
    # args = parser.parse_args()
    if not debug:
        game_name = gamename.strip().lower() if gamename else tune.strip().lower()
        want_saving = save_ids
        config_path = os.path.join(os.path.dirname(__file__), "grid_config.json")

        with open(config_path, "r") as f:
            config = json.load(f)
        if gamename:
            matched_game = next((k for k in config if k.lower() == game_name), None)
            if not matched_game:
                raise ValueError(f"Game name '{game_name}' not found in config.")
            params = config[matched_game]
        else:
            params = {}
    files = [os.path.basename(image_path)]
    is_tune = tune is not None
    resolution=""
    for file in files:
        print(file)
        path_image = image_path
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        candy_region = retain_candy_region(image)
        filtered_candy_region = process_image(candy_region)
        if debug:
            f, axarr = plt.subplots(1,2)
            axarr[0].imshow(image)
            axarr[1].imshow(candy_region)
            # axarr[2].imshow(filtered_candy_region)
            plt.show()
            continue

        current_res = f"{str(image.shape[0])}x{str(image.shape[1])}"
        if resolution == "":
            resolution=current_res
        if current_res !=resolution:
            print(f"\033[91m Error: the current screenshot {file} has a different resolution from the previous ones. \033[0m",file=sys.stderr)
            exit()
        if current_res not in params and not is_tune:
            print(f"\033[91m Error: the resolution ({current_res}) of the current screenshot ({file}) is not in the config file. Available {params.keys()}. \033[0m",file=sys.stderr)
            exit()
        if is_tune:
            is_tune=False
            params_lower_bound={}
            params_lower_bound["vertical_threshold"] = 50
            params_lower_bound["vertical_minLineLength"] = 20
            params_lower_bound["vertical_maxLineGap"] = 2
            params_lower_bound["threshold"]=50
            params_lower_bound["maxval"]=50
            params_lower_bound["canny_thresh"]=20
            params_upper_bound={}
            params_upper_bound["vertical_threshold"] = 300
            params_upper_bound["vertical_minLineLength"] = 200
            params_upper_bound["vertical_maxLineGap"] = 20
            params_upper_bound["threshold"]=300
            params_upper_bound["maxval"]=300
            params_upper_bound["canny_thresh"]=200
                
            parameter_dict,mean_width,mean_height, to_return=genetic_algorithm_tune_parameters(filtered_candy_region,params_lower_bound,params_upper_bound,process_image_with_parameters,population_size=population, generation_no_improvements=generations,fitness_tolerance=tolerance, path_image=image_path, show=True)



            parameter_dict["cell_w"]=str(round(mean_width,2))
            parameter_dict["cell_h"]=str(round(mean_height,2))
            if not tune in config:
                config[tune]={}
            config[tune][resolution]=parameter_dict
            params = config[tune]
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4) 
        else:
            grid = get_grid(filtered_candy_region,float(params[current_res]["cell_w"]),float(params[current_res]["cell_h"]), path_image, want_saving)
            f, axarr = plt.subplots(1,3)
            axarr[0].imshow(image)
            axarr[1].imshow(filtered_candy_region)
            axarr[2].imshow(grid["output_image"])
            plt.show()
    elapsed = time.perf_counter() - start
    print(f"Elapsed: {elapsed:.6f} s")
    return to_return



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grid construction and candy clustering")
    parser.add_argument("-p", "--path", type=str, required=True)
    parser.add_argument("--population", type=int, required=True)
    parser.add_argument("--generations", type=int, required=True)
    parser.add_argument("--tolerance", type=float, required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", "--gamename", type=str)
    group.add_argument("-t", "--tune", type=str)
    group.add_argument("-d", "--debug", action="store_true")

    parser.add_argument("-s", "--save_ids", action="store_true")

    args = parser.parse_args()

    run_controller(
        image_path=args.path,
        population=args.population,
        generations=args.generations,
        tolerance=args.tolerance,
        gamename=args.gamename,
        tune=args.tune,
        save_ids=args.save_ids,
        debug=args.debug
    )