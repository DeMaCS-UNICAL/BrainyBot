import os
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from validation import Validation  # ✅ Make sure this import works

# Define DetectedObject for use with validator
class DetectedObject:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label

def read_txt_data(txt_path):
    """Reads a txt file with format: x y id"""
    data = []
    with open(txt_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                x, y, obj_id = map(int, parts)
                data.append(((x, y), obj_id))
    return data

def read_excel_data(excel_path):
    """Reads an Excel file with 'Center' and 'ID' columns."""
    data = []
    try:
        df = pd.read_excel(excel_path)
        for _, row in df.iterrows():
            center = str(row['Center']).strip().replace('(', '').replace(')', '')
            id_val = int(row['ID'])

            if ',' in center:
                parts = center.split(',')
                if len(parts) == 2:
                    x, y = int(float(parts[0].strip())), int(float(parts[1].strip()))
                    data.append(DetectedObject(x, y, id_val))
    except Exception as e:
        print(f"❌ Error reading {excel_path}: {e}")
    return data

def find_matching_txt(txt_filename, search_root):
    for dirpath, _, filenames in os.walk(search_root):
        if txt_filename in filenames:
            return os.path.join(dirpath, txt_filename)
    return None


def validate_all(gt_root, pred_root, threshold=50):
    validator = Validation()
    full_results = []

    match3_root = os.path.join(gt_root, "match3")
    for resolution_folder in os.listdir(match3_root):
        res_path = os.path.join(match3_root, resolution_folder)
        if not os.path.isdir(res_path):
            continue

        print(f"\n📏 Resolution: {resolution_folder}")
        for game_folder in os.listdir(res_path):
            game_path = os.path.join(res_path, game_folder)
            if not os.path.isdir(game_path):
                continue

            print(f"🎮 Game: {game_folder}")
            tp_total = fp_total = fn_total = file_count = zero_errors = 0
            unmatched_files = []
            error_files = []

            for dirpath, _, filenames in os.walk(game_path):
                for file in filenames:
                    if file.endswith('.txt'):
                        file_count += 1
                        gt_path = os.path.join(dirpath, file)
                        rel_game_folder = os.path.relpath(dirpath, res_path)
                        pred_match = find_matching_txt(file, pred_root)

                        if not pred_match:
                            unmatched_files.append(file)
                            continue

                        gt_data = read_txt_data(gt_path)
                        pred_data = [DetectedObject(x, y, label) for (x, y), label in read_txt_data(pred_match)]


                        if not gt_data or not pred_data:
                            continue

                        fn, fp, tp, er_log = validator.validate_matches(pred_data, gt_data, threshold)
                        # Count reasons
                        fp_id_mismatch = sum(1 for e in er_log if e["type"] == "mismatch" and e["reason"] == "wrong_label")
                        fn_distance = sum(1 for e in er_log if e["type"] == "mismatch" and e["reason"] == "too_far")
                        both_fp_fn = sum(1 for e in er_log if e["type"] == "mismatch" and e["reason"] in ("too_far", "wrong_label"))

                        fn_sum = sum(fn.values())
                        fp_sum = sum(fp.values())
                        tp_sum = sum(tp.values())
                        if fn_sum > 0 or fp_sum > 0:
                            error_files.append(file)

                        

                        if fn_sum == 0 and fp_sum == 0:
                            zero_errors += 1

                        tp_total += tp_sum
                        fp_total += fp_sum
                        fn_total += fn_sum
                        # print(f"   File: {file}")
                        # print(f"     ✅ TP: {tp_sum}")
                        # print(f"     ❌ FP: {fp_sum} | FN: {fn_sum}")
                        # print(f"     ⚠️  FP due to label mismatch: {fp_id_mismatch}")
                        # print(f"     ⚠️  FN due to distance mismatch: {fn_distance}")
                        # print(f"     ⚠️  Combined FP+FN due to ID/distance mismatch: {both_fp_fn}")

            print(f"   Files validated: {file_count}")
            print(f"   TP: {tp_total}, FP: {fp_total}, FN: {fn_total}, Zero-error files: {zero_errors}")
            if unmatched_files:
                print(f"   ⚠️ Unmatched: {len(unmatched_files)} files")
                print("     ➤", ", ".join(unmatched_files))
            if error_files:
                print(f"   ❌ Files with errors: {len(error_files)}")
                print("     ➤", ", ".join(error_files))



# 8. Sweets match       Sweets_Match
# 12. Candy charming    Candy_Charming
# 1. Candy crush saga   Candy_Crush
# === Example usage ===
if __name__ == "__main__":
    gt_path = "/mnt/c/Users/Utente/Desktop/Ground truth acording to template matching - lines removed"
    pred_path = "/mnt/c/Users/Utente/Desktop/Data set - 3 games SAMM GFS/1080x2400"


    validation_results = validate_all(gt_path, pred_path, threshold=50)

