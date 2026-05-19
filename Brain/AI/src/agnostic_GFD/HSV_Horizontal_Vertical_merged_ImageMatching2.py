
import sys
import cv2
import numpy as np
from matplotlib import pyplot as plt
import os
from AI.src.agnostic_GFD.Lines_Detector import search_lines
from AI.src.vision.output_game_object import OutputTemplateMatch
import traceback


def find_processed_folders(base_path):
    final_folders = []
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if dir_name.lower() == 'extrusion_processed':
                processed_path = os.path.join(root, dir_name)
                processed2_path = os.path.join(processed_path, 'processed2')
                
                # Check if 'processed2' exists inside 'extrusion_processed'
                if os.path.isdir(processed2_path):
                    final_folders.append(processed2_path)
                else:
                    final_folders.append(processed_path)
    return final_folders

def load_image(image_path):
    return cv2.imread(image_path)


def process_image_with_parameters(
    image,
    params,
    path_image=None,
    want_saving=False,
    save_templates=False
) -> dict[str, any]:
    '''
    Return a dictionary with keys:
    - "image" - np.ndarray : The processed combined image with detected lines.
    - "num_objects" - int : Number of detected objects (boxes).
    - "num_groups" - int : Number of groups identified through template matching.
    - "removed_lines" - int : Number of lines removed during processing.
    - "added_lines" - int : Number of lines added during processing.
    - "width_std" - float : Standard deviation of the widths of detected boxes.
    - "height_std" - float : Standard deviation of the heights of detected boxes.
    - "mean_width" - float : Mean width of detected boxes.
    - "mean_height" - float : Mean height of detected boxes.
    - "covered_area" - float : Proportion of the image area covered by detected boxes
    - "output_image" - np.ndarray : Image annotated with template matching results.
    '''
    try:
        if isinstance(image, str) :
            folder_containing_image = os.path.dirname(image)
            output_folder = os.path.join(folder_containing_image, 'processed3')
            os.makedirs(output_folder, exist_ok=True)

            image = cv2.imread(image)
        dilation_params = {}
        dilation_params["threshold"]=params["threshold"]
        dilation_params["maxval"]=params["maxval"]
        dilation_params["canny_thresh"]=params["canny_thresh"]
        clustering_threshold=20
        lines = search_lines(image,params,dilation_params,clustering_threshold,False)
        boxes = create_boxes(lines["horizontal_coords"], lines["vertical_coords"])
        # boxes = filter_boxes_by_black_pixels(image, boxes, black_threshold=50, max_black_ratio=0.40)
        tm = template_matching_fast(image, boxes, path_image, want_saving, save_templates)
        
        limits = non_black_limits(image)
        total_area = (limits["bottom"]-limits["top"])*(limits["right"]-limits["left"])
        covered_area = lines["covered_area"]/total_area
        
        return{
            "image": lines["combined_output"],
            "num_objects": len(boxes),
            "num_groups": tm['num_groups'],
            "removed_lines": lines["removed_lines"],
            "added_lines": lines["added_lines"],
            "width_std": tm["width_std"],
            "height_std": tm["height_std"],
            "mean_width": tm["mean_width"],
            "mean_height": tm["mean_height"],
            "covered_area": covered_area,
            "output_image": tm["output_image"],
            "output_matches": tm["output_matches"]
        }
    except Exception as e: 
        print(traceback.format_exc(),file=sys.stderr)
        #return image,0,0,np.inf,np.inf,np.inf,np.inf,0,0,0,image
        return {
            "image": image,
            "num_objects": 0,
            "num_groups": 0,
            "removed_lines": np.inf,
            "added_lines": np.inf,
            "width_std": np.inf,
            "height_std": np.inf,
            "mean_width": 0,
            "mean_height": 0,
            "covered_area": 0,
            "output_image": image,
            "output_matches": 0
        }

def get_grid(image,cell_width,cell_height, path_image=None, want_saving=False) -> dict[str, any]:
    '''
    Returns a dictionary with keys:
    - "image" - np.ndarray : The original image.
    - "assigned" - list[int] : List of assigned group IDs for each box.
    - "boxes" - list : List of detected boxes with their properties.
    - "output_image" - np.ndarray : Image annotated with template matching results.
    '''
    if isinstance(image, str) :
        folder_containing_image = os.path.dirname(image)
        output_folder = os.path.join(folder_containing_image, 'processed3')
        os.makedirs(output_folder, exist_ok=True)

        image = cv2.imread(image)

    limits = non_black_limits(image)
    num_rows = round((limits["bottom"]-limits["top"])/cell_height)
    num_col = round((limits["right"]-limits["left"])/cell_width)

    center_horiz = limits["top"]+((limits["bottom"]-limits["top"])/2)
    center_vert = limits["left"]+((limits["right"]-limits["left"])/2)
    next_horiz_top = center_horiz-cell_height/2 if num_rows%2==1 else center_horiz
    next_horiz_bottom = center_horiz+cell_height/2 if num_rows%2==1 else center_horiz + cell_height
    next_vert_left = center_vert-cell_width/2 if num_col%2==1 else center_vert
    next_vert_right = center_vert +cell_width/2 if num_col%2==1 else center_vert + cell_width
    vertical_coords =[]
    horizontal_coords=[]
    while next_horiz_top>=limits["top"]:
        horizontal_coords.insert(0,next_horiz_top)
        next_horiz_top -= cell_height
    while next_horiz_bottom<=limits["bottom"]:
        horizontal_coords.append(next_horiz_bottom)
        next_horiz_bottom += cell_height
    while next_vert_left>=limits["left"]:
        vertical_coords.insert(0,next_vert_left)
        next_vert_left -= cell_width
    while next_vert_right<=limits["right"]:
        vertical_coords.append(next_vert_right)
        next_vert_right += cell_width
        
    boxes = create_boxes(horizontal_coords, vertical_coords)
    boxes = filter_boxes_by_black_pixels(image, boxes, black_threshold=50, max_black_ratio=0.40)
    tm = template_matching_fast(image, boxes, path_image, want_saving)
    return {
        "image": image,
        "assigned": tm["assigned"],
        "boxes": boxes,
        "output_image": tm["output_image"]
    }

def non_black_limits(img) -> dict[str, int]:
    '''
        Returns a dictionary with keys:
        - "top" : int : Topmost non-black row index.
        - "bottom" : int : Bottommost non-black row index.
        - "left" : int : Leftmost non-black column index.
        - "right" : int : Rightmost non-black column index.
    '''
    
    H, W = img.shape[:2]
    s = img if img.ndim == 2 else img.max(axis=2)

    row_max = s.max(axis=1)              # (H,)
    col_max = s.max(axis=0)              # (W,)

    if row_max.max() == 0:               # all black
        return {
            "top": -1,
            "bottom": -1,
            "left": -1,
            "right": -1
        }

    rows_has = row_max > 0               # (H,) small boolean
    cols_has = col_max > 0               # (W,) small boolean

    top    = int(np.argmax(rows_has))
    bottom = int(H - 1 - np.argmax(rows_has[::-1]))
    left   = int(np.argmax(cols_has))
    right  = int(W - 1 - np.argmax(cols_has[::-1]))
    
    return {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right
    }

def create_boxes(horizontal_lines, vertical_lines):
    boxes = []
    for i in range(len(horizontal_lines) - 1):
        for j in range(len(vertical_lines) - 1):
            top = horizontal_lines[i]
            bottom = horizontal_lines[i + 1]
            left = vertical_lines[j]
            right = vertical_lines[j + 1]
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            width = right - left
            height = bottom - top
            box = {
                "center": (center_x, center_y),
                "width": width,
                "height": height
            }
            boxes.append(box)
    return boxes


def filter_boxes_by_black_pixels(image, boxes, black_threshold=50, max_black_ratio=0.40):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape[:2]
    kept_boxes = []
    removed = 0

    for b in boxes:
        cx, cy = b["center"]
        w, h = int(b["width"]), int(b["height"])

        # Reconstruct box coordinates and clip to image bounds
        left   = max(0, int(cx - w // 2))
        right  = min(W, int(left + w))
        top    = max(0, int(cy - h // 2))
        bottom = min(H, int(top + h))
        roi = gray[top:bottom, left:right]
        total = roi.size
        black_pixels = np.count_nonzero(roi < black_threshold)
        black_ratio = black_pixels / total

        if black_ratio <= max_black_ratio:
            kept_boxes.append(b)
        else:
            removed += 1
    return kept_boxes

def is_flat_patch(patch, var_thresh=130, range_thresh=15):

    if (int(patch.max()) - int(patch.min())) <= range_thresh:
        return True
    m = patch.mean(dtype=np.float32)
    v = (patch.astype(np.float32)**2).mean() - m*m
    return v <= var_thresh

def _save_box_clusters_txt(centers, wh, assigned, scores, path_image, coord_mode="center"):
    print(path_image)

    base_dir = os.path.dirname(path_image)
    base_name = os.path.splitext(os.path.basename(path_image))[0]
    out_txt_path = os.path.join(base_dir, f"{base_name}.txt")

    rows = []
    for i, cid in enumerate(assigned):
        cx, cy = int(centers[i, 0]), int(centers[i, 1])
        w, h   = int(wh[i, 0]), int(wh[i, 1])

        if coord_mode == "center":
            x, y = cx, cy
        elif coord_mode == "topleft":
            x, y = cx - w // 2, cy - h // 2
        elif coord_mode == "bottomright":
            x, y = cx + (w - 1) // 2, cy + (h - 1) // 2
        else:
            x, y = cx, cy  # fallback

        rows.append((y, x, w, h, int(cid), float(scores[i])))

    rows.sort(key=lambda t: (t[0], t[1]))

    with open(out_txt_path, "w", encoding="utf-8") as f:
        for y, x, w, h, cid, score in rows:
            f.write(f"{x} {y} {w} {h} {cid} {score:.4f}\n")

    print(f"[INFO] Clusters saved to: {out_txt_path}")


def draw_boxes_ids(x1, y1, x2, y2, to_draw_rects, to_draw_labels, out):
    for rx1, ry1, rx2, ry2 in to_draw_rects:
        cv2.rectangle(out, (rx1, ry1), (rx2, ry2), (0, 255, 255), 2)
    for idx, cid, score in to_draw_labels:
        cx = (x1[idx] + x2[idx]) // 2
        cy = (y1[idx] + y2[idx]) // 2
        cv2.putText(out, f"{cid}", (x1[idx]+50, cy + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 5)

def group_patches(match_threshold, template_percentage, img, wh, x1, y1, x2, y2, areas, N, assigned, scores, is_flat, cur_id, to_draw_rects, to_draw_labels, templates):
    for i in range(N):
        if assigned[i] != -1 or is_flat[i]:
            continue
        tpl = templates[i]
        th, tw = tpl.shape[:2]
        tpl_area = th * tw

        assigned[i] = cur_id
        scores[i] = 1.0
        to_draw_rects.append((int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])))
        to_draw_labels.append((i, cur_id, 0))

        area_factor = (1/(template_percentage**2))
        area_factor += area_factor*0.2
        ok_size = (wh[:,0] >= tw) & (wh[:,1] >= th) & (areas <= area_factor * tpl_area)
        cand_mask = (assigned == -1) & (~is_flat) & ok_size
        cand_mask[i] = False
        cand_idx = np.flatnonzero(cand_mask)
        def score(j):
            sr = img[y1[j]:y2[j], x1[j]:x2[j]]
            res = cv2.matchTemplate(sr, tpl, cv2.TM_CCOEFF_NORMED)
            
            return j, float(res.max())

        if cand_idx.size:
            for j in cand_idx:
                _, m = score(j)
                if m >= match_threshold:
                    assigned[j] = cur_id
                    scores[j] = m
                    to_draw_rects.append((int(x1[j]), int(y1[j]), int(x2[j]), int(y2[j])))
                    to_draw_labels.append((j, cur_id, m))

        cur_id += 1

def retain_valid_patches(template_percentage, img, H, W, centers, wh, x1, y1, x2, y2, N, is_flat, to_draw_rects, to_draw_labels, templates):
    for i in range(N):
        cx, cy = centers[i]
        w, h   = int(wh[i,0]), int(wh[i,1])

        # build template = 0.75 window around the same center
        tpl_w, tpl_h = int(w *template_percentage), int(h *template_percentage)
        tx1 = max(cx - tpl_w // 2, 0); ty1 = max(cy - tpl_h // 2, 0)
        tx2 = min(tx1 + tpl_w, W);     ty2 = min(ty1 + tpl_h, H)
        tpl = img[ty1:ty2, tx1:tx2]
        th, tw = tpl.shape[:2]
        if th == 0 or tw == 0:
            templates.append(None)
            is_flat[i]=True
            to_draw_rects.append((int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])))
            to_draw_labels.append((i, "ERR!",0))
            continue

        tpl_gray = cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY)
        if not is_flat_patch(tpl_gray):
            templates.append(tpl)
        else:
            to_draw_rects.append((int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])))
            to_draw_labels.append((i, -1,0))
            templates.append(None)
            is_flat[i]=True


def _build_output_matches(centers, wh, assigned, scores):
    matches = []

    for i, cid in enumerate(assigned):
        if cid == -1:
            continue

        cx, cy = int(centers[i, 0]), int(centers[i, 1])
        w, h = int(wh[i, 0]), int(wh[i, 1])
        score = float(scores[i])

        matches.append(
            OutputTemplateMatch(
                x=cx,
                y=cy,
                width=w,
                heigth=h,
                label=str(cid),   # numeric assigned id as label
                confidence=score
            )
        )

    return matches

def template_matching_fast(image, boxes, path_image=None, want_saving=False, black_threshold=50, match_threshold=0.80, parallel=True, template_percentage=0.75, save_templates=False) -> dict[str, any]:
    '''
        Returns a dict with:
        - num_groups: int: number of unique groups found
        - width_std: float: standard deviation of widths
        - height_std: float: standard deviation of heights
        - mean_width: float: mean width
        - mean_height: float: mean height
        - assigned: list[int]: list of assigned group IDs
        - output_image: np.ndarray: image with annotations
    '''
    img=image
    H, W,_ = img.shape
    if len(boxes)==0:
        #return 0, np.inf, np.inf,0,0,[],img
        return {
            "num_groups": 0,
            "width_std": np.inf,
            "height_std": np.inf,
            "mean_width": 0,
            "mean_height": 0,
            "assigned": [],
            "output_image": img,
             "output_matches": []
        }
    # 2) pack boxes to arrays
    centers = np.array([b["center"] for b in boxes], dtype=np.int32)   # (N,2): [cx, cy]
    wh      = np.array([[b["width"], b["height"]] for b in boxes], dtype=np.int32)  # (N,2): [w, h]

    # corners (clipped)
    x1 = np.clip(centers[:,0] - wh[:,0]//2, 0, W)
    y1 = np.clip(centers[:,1] - wh[:,1]//2, 0, H)
    x2 = np.clip(x1 + wh[:,0], 0, W)
    y2 = np.clip(y1 + wh[:,1], 0, H)
    areas = (x2 - x1) * (y2 - y1)
    # 5) arrays instead of dicts
    N = len(boxes)
    assigned = np.full(N, -1, dtype=np.int32)
    scores = np.zeros(N, dtype=np.float32)
    is_flat=np.full(N, False, dtype=bool)
    cur_id = 1

    # accumulate drawings; do once at end
    to_draw_rects = []
    to_draw_labels = []

    # stats (just compute once with numpy)
    widths  = wh[:,0].astype(np.float32)
    heights = wh[:,1].astype(np.float32)
    templates=[]
    retain_valid_patches(template_percentage, img, H, W, centers, wh, x1, y1, x2, y2, N, is_flat, to_draw_rects, to_draw_labels, templates)

    group_patches(match_threshold, template_percentage, img, wh, x1, y1, x2, y2, areas, N, assigned, scores, is_flat, cur_id, to_draw_rects, to_draw_labels, templates)

    
    out = image.copy()
    draw_boxes_ids(x1, y1, x2, y2, to_draw_rects, to_draw_labels, out)
    mean_width = widths.mean()
    mean_height = heights.mean()
    w_cv = float(widths.std() / max(mean_width, 1e-9)) if widths.size else float("inf")
    h_cv = float(heights.std() / max(mean_height, 1e-9)) if heights.size else float("inf")
    num_groups = int(np.unique(assigned[assigned != -1]).size)
    output_matches = _build_output_matches(centers, wh, assigned, scores)
    print(want_saving)
    if(want_saving):  # to store centre(x,y) and id in txt file
        _save_box_clusters_txt(centers, wh, assigned, scores, path_image)
        # for obj in output_matches:
        #     print(obj.__dict__)
        
    return {
        "num_groups": num_groups,
        "width_std": w_cv,
        "height_std": h_cv,
        "mean_width": mean_width,
        "mean_height": mean_height,
        "assigned": assigned,
        "output_image": out,
        "output_matches": output_matches
    }
