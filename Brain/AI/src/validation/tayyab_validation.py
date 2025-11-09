
import os
import sys
import pandas as pd
import numpy as np
from collections import Counter
from scipy.optimize import linear_sum_assignment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from validation import Validation 
import argparse 

class DetectedObject:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label


def read_gt_txt(txt_path):
    """
    GT TXT can contain:
      - 'x y id'  -> use
      - 'x y'     -> ignore (no label)
      - '-----'   -> ignore (row separators)
      - blank     -> ignore
    Returns: list of ((x, y), id)
    """
    data = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('-'):
                continue
            parts = line.split()
            if len(parts) == 3:
                try:
                    x, y, obj_id = map(int, parts)
                    data.append(((x, y), obj_id))
                except ValueError:
                    # skip malformed
                    continue
    return data

def read_pred_txt(txt_path):
    data = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('-'):
                continue
            parts = line.split()
            if len(parts) != 3:
                continue
            try:
                x, y, obj_id = map(int, parts)
                data.append(DetectedObject(x, y, obj_id))
            except ValueError:
                continue
    return data

def index_pred_txt_files(pred_root):
    idx = {}
    for dirpath, _, filenames in os.walk(pred_root):
        for fn in filenames:
            if fn.lower().endswith('.txt'):
                idx.setdefault(fn, []).append(os.path.join(dirpath, fn))
    return idx

def find_pred_for_gt(gt_filename, pred_index):
    candidates = pred_index.get(gt_filename, [])
    if not candidates:
        return None, False
    if len(candidates) > 1:
        # Ambiguous; choose first but signal there are multiple
        return candidates[0], True
    return candidates[0], False

def validate_all(gt_root, pred_root, threshold=50):
    validator = Validation()
    match3_root = os.path.join(gt_root, "match3")
    # Build prediction index once
    pred_index = index_pred_txt_files(pred_root)
    game_stats = []

    for resolution_folder in os.listdir(match3_root):
        res_path = os.path.join(match3_root, resolution_folder)
        if not os.path.isdir(res_path):
            continue

        print(f"Resolution: {resolution_folder}")
        for game_folder in os.listdir(res_path):
            game_path = os.path.join(res_path, game_folder)
            if not os.path.isdir(game_path):
                continue

            print(f"Game: {game_folder}")
            tp_total = fp_total = fn_total = file_count = zero_errors = 0
            unmatched_files = []
            multiple_match_files = []
            error_files = []
            # zero_error_files = []  

            for dirpath, _, filenames in os.walk(game_path):
                for file in filenames:
                    if not file.lower().endswith('.txt'):
                        continue

                    file_count += 1
                    gt_path = os.path.join(dirpath, file)

                    pred_path, has_multiple = find_pred_for_gt(file, pred_index)
                    if pred_path is None:
                        unmatched_files.append(file)
                        continue
                    if has_multiple:
                        multiple_match_files.append(file)

                    gt_data = read_gt_txt(gt_path)
                    pred_data = read_pred_txt(pred_path)

                    if not gt_data or not pred_data:
                        continue

                    fn_by, fp_by, tp_by = validator.validate_matches(pred_data, gt_data, threshold)

                    # per-label GT counts
                    gt_counts = Counter([label for (_, label) in gt_data])
                    fn_sum = sum(fn_by.values())
                    fp_sum = sum(fp_by.values())
                    tp_sum = sum(tp_by.values())

                    if fn_sum == 0 and fp_sum == 0:
                        zero_errors += 1
                        # zero_error_files.append(file)
                    else:
                        error_files.append(file)

                    tp_total += tp_sum
                    fp_total += fp_sum
                    fn_total += fn_sum

            # Summary per game
            print(f"   Files validated: {file_count}")
            print(f"   TP: {tp_total}, FP: {fp_total}, FN: {fn_total}, Zero-error files: {zero_errors}")

            if unmatched_files:
                print(f"  Unmatched files in predictions ({len(unmatched_files)}):")
                for fname in unmatched_files:
                    print(f"     - {fname}")

            if multiple_match_files:
                print(f"  Multiple prediction candidates found ({len(multiple_match_files)}); first used:")
                for fname in multiple_match_files:
                    print(f"     - {fname}")

            if error_files:
                print(f" Files with errors ({len(error_files)}):")
                for fname in error_files:
                    print(f"     - {fname}")
            
            # Per-game metrics at the end
            precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) else 0.0
            recall    = tp_total / (tp_total + fn_total) if (tp_total + fn_total) else 0.0
            f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

            game_stats.append((resolution_folder, game_folder, precision, recall, f1, tp_total, fp_total, fn_total))

    print("\nPer-game metrics (all resolutions):")
    for res, game, p, r, f1, tp, fp, fn in game_stats:
        print(f" - {res}/{game}: Precision={p:.3f}, Recall={r:.3f}, F1={f1:.3f}  (TP={tp}, FP={fp}, FN={fn})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate predictions against ground truth.")
    parser.add_argument("gt_root", help="Path to the ground truth root directory")
    parser.add_argument("pred_root", help="Path to the predictions root directory")
    args = parser.parse_args()
    print("Validation starts now")

    validate_all(args.gt_root, args.pred_root, 50)

    # pred_root = r"/mnt/d/HP 840 G6 Data/PD/Calabria/Research/Phd thesis/Object and Grid detection papers/Images/Working_Dataset_5_game_GT_CW/Screenshots/"
    # gt_root = r"/mnt/d/HP 840 G6 Data/PD/Calabria/Research/Phd thesis/Object and Grid detection papers/Images/Working_Dataset_5_game_GT_CW/Ground_truth/Ground truth/"


