import argparse
import csv
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import sys
import time
import cv2
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment
from collections import defaultdict
import numpy as np

from EdgeDetectionTechniques2 import retain_candy_region
from HSV_Horizontal_Vertical_merged_ImageMatching2 import get_grid, process_image_with_parameters
from autotuting import genetic_algorithm_tune_parameters
from extrusion_remover import process_image



def test_autotuning(path,mode):
    params = {}
    files = []
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
    for f in os.listdir(path):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            files.append(f)
    leaf_name = os.path.basename(dirpath)
    parent_name = os.path.basename(os.path.dirname(dirpath))
    outer_folder=os.path.join(path,"tuning_test_"+str(os.getpid()))
    os.makedirs(outer_folder,exist_ok=True)
    total = len(files)
    print(f"Found {total} files.",end="")
    out_counter=1
    for file1 in files:
        print(f"{out_counter}/{total} in {parent_name}/{leaf_name}")
        out_counter+=1
        counter = 1
        print()
        p = Path(file1)
        inner_folder = os.path.join(outer_folder,file1.strip(p.suffix))
        if os.path.isdir(inner_folder):
            continue
        os.makedirs(inner_folder)
        image = cv2.imread(os.path.join(path, file1))
        candy_region = retain_candy_region(image)
        filtered_candy_region = process_image(candy_region)
        start = time.time()
        parameter_dict,mean_width,mean_height=genetic_algorithm_tune_parameters(filtered_candy_region,params_lower_bound,params_upper_bound,process_image_with_parameters,show=False,mode=mode)
        end = time.time()
        parameter_dict["cell_w"]=str(round(mean_width,2))
        parameter_dict["cell_h"]=str(round(mean_height,2))
        params = parameter_dict
        with open(os.path.join(inner_folder,"cell_size.csv"),mode="w") as f:
            f.write(f"{parameter_dict['cell_w']},{parameter_dict['cell_h']},{end-start}")
        print(f"Autotuning done in {end-start}.")
        for file in files:
            if file == file1:
                continue
            fp = Path(file)
            image = cv2.imread(os.path.join(path, file))
            candy_region = retain_candy_region(image)
            filtered_candy_region = process_image(candy_region)
            grid = get_grid(filtered_candy_region,float(params["cell_w"]),float(params["cell_h"]))
            with open(os.path.join(inner_folder,file.strip(fp.suffix)+".txt"),mode="w") as f:
                for i,box in enumerate(grid["boxes"]):
                    f.write(f"{box['center'][0]} {box['center'][1]} {grid['assigned'][i]}\n")
            print(f"{counter}/{total}",end = '\r')
            counter+=1




def calculate_distance(coord1, coord2):
    return np.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def create_cost_matrix(detected_objects, ground_truth, label_penalty=1000, consider_label=True):
    cost_matrix = np.zeros((len(detected_objects), len(ground_truth)))
    for i, det in enumerate(detected_objects):
        for j, gt in enumerate(ground_truth):
            if consider_label and det[1] != gt[1]:
                cost_matrix[i, j] = label_penalty
            else:
                cost_matrix[i, j] = calculate_distance(det[0], gt[0])
    return cost_matrix

def count_false_positives_negatives(detected_objects, ground_truth, distance_threshold=50, consider_label=True):
    cost_matrix = create_cost_matrix(detected_objects, ground_truth,consider_label=consider_label)
    # Hungarian algorithm
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    #for i, j in zip(row_ind, col_ind):
        #   print(f"Oggetto rilevato {i} abbinato all'oggetto ground truth {j} con costo {cost_matrix[i, j]}")
        #  print(detected_objects[i],ground_truth[j])
    matched_detected = [False] * len(detected_objects)
    matched_ground_truth = [False] * len(ground_truth)
    results={}
    false_positive = 0
    false_negative = 0
    true_positive =0
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] > distance_threshold:
            false_positive+=1
            false_negative+=1
        else:
            true_positive +=1


        matched_detected[i] = True
        matched_ground_truth[j] = True

    for i, matched in enumerate(matched_detected):
        if not matched:
            false_positive+=1

    for j, matched in enumerate(matched_ground_truth):
        if not matched:
            false_negative+=1
    return len(ground_truth),true_positive,false_positive,false_negative

def validate_matches(matches_list,validation:list,threshold=50,consider_label=True):
    #print("validating vision")
    '''
    matches=[]
    for m in matches_list:
            matches.append(((m.x,m.y),m.label))
    #print(matches)
    '''
    return count_false_positives_negatives(matches_list,validation,threshold,consider_label)

def validate(ground_truth, validate):
    to_validate = []
    with open(validate,'r') as file:
        for line in file:
            line=line.strip()
            split = tuple(line.split())
            if len(split)==1:
                continue
            if len(split)==2:
                split=(split[0],split[1],"")
            to_validate.append(((int(float(split[0])),int(float(split[1]))),split[2]))

    gt = []
    with open(ground_truth,'r') as file:
        for line in file:
            line=line.strip()
            split = tuple(line.split())
            if len(split)<=2:
                continue
            gt.append(((int(float(split[0])),int(float(split[1]))),split[2]))

    _,global_TP,global_FP,global_FN = validate_matches(to_validate,gt,consider_label=True)
    all,grid_TP,grid_FP,grid_FN = validate_matches(to_validate,gt,consider_label=False)

    '''
    print(f)
    print("FN",only_grid["grid_false_negatives"], "FP",only_grid["grid_false_positives"])
    print("FN",with_label["false_negatives_by_label"])
    print("FP",with_label["false_positives_by_label"])
    '''
    return  all,grid_TP, grid_FP, grid_FN, global_TP, global_FP, global_FN



def validate_all_games(g_root: str, v_root: str, mode=""):
    g_root = Path(g_root)
    v_root = Path(v_root)
    folder_name = "validation_result_"+str(mode)
    validation_result_folder = g_root/".."/".."/".."/folder_name
    validation_result_folder.mkdir(exist_ok=True)
    header = ["Zh","TOTAL_OBJ", "grid_TP", "grid_FP", "grid_FN", "global_TP", "global_FP", "global_FN"]

    for x_g in sorted(p for p in g_root.iterdir() if p.is_dir()):  # Xi
        x_v = v_root / x_g.name
        if not x_v.exists():
            print(f"[skip] Missing {x_v}")
            continue

        for y_g in sorted(p for p in x_g.iterdir() if p.is_dir()):  # Yj
            files_g = [p for p in y_g.iterdir() if p.is_file()]
            infolder_name = "tuning_test_"+str(mode)
            y_v_tuning = x_v / y_g.name / infolder_name
            if not y_v_tuning.exists():
                print(f"[skip] Missing {y_v_tuning}")
                continue
            result_folder = validation_result_folder/x_g.name
            result_folder.mkdir(exist_ok=True)
            result_folder = result_folder/y_g.name
            result_folder.mkdir(exist_ok=True)


            z_folders = sorted(p for p in y_v_tuning.iterdir() if p.is_dir())

            for fg in files_g:  # one CSV per F_g
                if fg.suffix.lower() == ".ini":
                    continue
                print("validating",fg)
                result_file = result_folder / f"{fg.stem}.csv"
                print("saving to",result_file)
                file_exists = result_file.exists()

                with open(result_file, "a", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)

                    # Write header only once
                    if not file_exists:
                        writer.writerow(header)

                    for z_v in z_folders:
                        fv = z_v / fg.name
                        if not fv.is_file():
                            continue

                        # f() returns six values in order
                        all,grid_TP, grid_FP, grid_FN, global_TP, global_FP, global_FN = validate(fg, fv)
                        writer.writerow([z_v.name, all,grid_TP, grid_FP, grid_FN,
                                         global_TP, global_FP, global_FN])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grid construction and candy clustering")
    parser.add_argument("-d", "--debug", action='store_true', help="Wether to show the image result.")
    parser.add_argument("-p", "--path", type=str, required=False, help="Path to the images.")
    parser.add_argument("-v", "--validate", type=str, required=False, help="Path to experiments to be validated.")
    parser.add_argument("-g", "--ground_truth", type=str, required=False, help="Path to ground truth.")

    parser.add_argument("-m", "--mode", type=int, required=False, help="Path to the image images.")



    args = parser.parse_args()
    if args.path:
        for dirpath, dirnames, filenames in os.walk(args.path):
        # A "leaf folder" has no subdirectories
            if "tuning_test" in dirnames:
                leaf_name = os.path.basename(dirpath)
                parent_name = os.path.basename(os.path.dirname(dirpath))
                if leaf_name != "Candy blast":
                    print(dirpath)
                    test_autotuning(dirpath, args.mode if args.mode else 0)
    else:
        try:
            print(validate_all_games(args.ground_truth, args.validate,mode=args.mode if args.mode else 0))
        except Exception as e:
            print(f"Error: {e}")
            print('\a', flush=True)
            print('\a', flush=True)
            print('\a', flush=True)