import os
import time
from matplotlib import pyplot as plt
import cv2
 
from AI.src.monogram.detect.new_detect import MatchingMonogram
from AI.src.vision.output_game_object import MonogramHint
from AI.src.vision.input_game_object import Rectangle, TextRectangle
from AI.src.monogram.dlvsolution.dlvsolution import DLVSolution
from AI.src.constants import CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP
from AI.src.vision.feedback import Feedback
 
 
def draw(matrixCopy, center,id,width,height, color):
    top_left = (center[0] - width // 2, center[1] - height // 2)
    bottom_right = (center[0] + width // 2, center[1] + height // 2)
 
    cv2.rectangle(matrixCopy, top_left,bottom_right, color, 10)
    cv2.putText(matrixCopy,f"{id}",center,cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def prepare_asp_input(grid_matrix, hint_lines):

    facts = []

    cell_id = 0

    for row_idx, row in enumerate(grid_matrix):

        for col_idx, symbol in enumerate(row):

            state = 'cross' if symbol in ('X', 'cross') else 'empty'

            facts.append(f"cell({cell_id},{row_idx},{col_idx},{state}).")

            cell_id += 1
 
    for hint_type, line_index, hint_text in hint_lines:

        digits = [c for c in hint_text if c.isdigit()]

        lengths = []

        i = 0

        while i < len(digits):

            if digits[i] == '1' and i + 1 < len(digits) and digits[i + 1] == '0':

                lengths.append(10)

                i += 2

            else:

                lengths.append(int(digits[i]))

                i += 1

        for idx, length in enumerate(lengths, start=1):

            facts.append(f"block({line_index},{length},{idx},{hint_type}).")
 
    return facts
 
 
def is_inside_grid(rect, grid_left, grid_top, grid_right, grid_bottom):
    """A candidate rectangle counts as 'inside the grid' if its center falls
    within the grid's bounding box, so it can be excluded from hint detection."""
    cx = rect.x + rect.width / 2
    cy = rect.y + rect.heigth / 2
    return grid_left <= cx <= grid_right and grid_top <= cy <= grid_bottom
 
def monogram(screenshot, debug=False, vision_validation=None,
             abstraction_validation=None, iteration=0, benchmark=False):
    """
    Main Monogram solver.
    """
    print("START MONOGRAM")
    # ============ VISION DETECTION ============
    print("\n[VISION] Detecting grid cells and hints...")
    matcher = MatchingMonogram(
        screenshot,
        debug=debug,
        validation=vision_validation is not None,
        iteration=iteration,
        grid_size=(11, 11),
    )
    # ===== STEP 1: Template Matching =====
    print("\n[STEP 1] Running template matching...")
    template_matches = matcher.get_template_matches()
    print(f"  ✓ Template matches: {len(template_matches)}")
    # Visualization after template matching
    if debug:
        img_copy = matcher.original_image.copy()
        for tm in template_matches:
            draw(img_copy, (tm.x, tm.y), f"{1}", tm.template_width, tm.template_heigth, (0, 255, 0))
        plt.figure(figsize=(12, 8))
        plt.imshow(img_copy)
        plt.title(f"Template Matching Results: {len(template_matches)} matches found")
        plt.show()
 
    # ===== STEP 2: Abstraction (grid geometry) =====
    # Run this before hint detection so we know the grid's bounding box and
    # can tell hint boxes (outside the grid) apart from grid cells (inside it).
    print("\n[STEP 2] Running abstraction...")
    grid_matrix, detected_cells, offset, delta = matcher.get_grid_state()
    rows, cols = len(grid_matrix), len(grid_matrix[0])
 
    print(f"  ✓ Grid: {rows}×{cols}")
    print(f"  ✓ Cells detected: {len(detected_cells)}")
 
    grid_left   = offset[0] - delta[0] / 2
    grid_top    = offset[1] - delta[1] / 2
    grid_right  = offset[0] + (cols - 1) * delta[0] + delta[0] / 2
    grid_bottom = offset[1] + (rows - 1) * delta[1] + delta[1] / 2
 
    # ===== STEP 3: Detect Hints =====
    print("\n[STEP 3] Detecting hint rectangles...")
    # Find all rectangles in the image, then keep only the ones outside the grid
    all_rectangles = matcher.finder.find(Rectangle(hierarchy=False))
    rectangles = [
        r for r in all_rectangles
        if not is_inside_grid(r, grid_left, grid_top, grid_right, grid_bottom)
        # detectable rectanglues must have y coordinate less or equal to the grid's bottom edge 
        and r.y <= grid_bottom
    ]
    print(f"  ✓ Found {len(all_rectangles)} rectangles, {len(rectangles)} outside the grid")
    hints = []
    hint_lines = []
    # Extract text from each rectangle to create hints
    for i, rect in enumerate(rectangles):
        print(f"  [{i+1}/{len(rectangles)}] Processing rectangle at ({rect.x}, {rect.y}), size: {rect.width}x{rect.heigth}")
        try:
            # Create TextRectangle search object
            text_search = TextRectangle(rectangle=rect, numeric=False)
            # Call finder.find() with TextRectangle
            hint_text = matcher.finder.find(text_search)
            print(f"    - Result type: {type(hint_text)}")
            print(f"    - Result value: {hint_text}")
            # Handle different return types
            if hint_text is not None:
                hint_text_str = str(hint_text).strip()
                if hint_text_str and len(hint_text_str) > 0:
                    cx = rect.x + rect.width / 2
                    cy = rect.y + rect.heigth / 2
                    if cx < grid_left:
                        hint_type = "row"
                        line_index = round((cy - offset[1]) / delta[1])
                    else:
                        hint_type = "col"
                        line_index = round((cx - offset[0]) / delta[0])
                
                    hint = MonogramHint(
                        x=float(rect.x),
                        y=float(rect.y),
                        width=float(rect.width),
                        height=float(rect.heigth),
                        hint_text=hint_text_str,
                        hint_type=hint_type
                    )
                    hints.append(hint)
                    hint_lines.append((hint_type, line_index, hint_text_str))
                    print(f"    ✓ Hint extracted: '{hint_text_str}' -> {hint_type} {line_index}")
                else:
                    print(f"    ✗ Empty text")
            else:
                print(f"    ✗ No text found (None returned)")
        except Exception as e:
            print(f"    ✗ Error extracting text: {e}")
            import traceback
            traceback.print_exc()
    print(f"  ✓ Total hints extracted: {len(hints)}")
    # Visualization of hints
    if debug and len(hints) > 0:
        hints_img = matcher.original_image.copy()
        for hint in hints:
            x1, y1 = int(hint.x), int(hint.y)
            x2 = x1 + int(hint.width)
            y2 = y1 + int(hint.height)
            # Draw rectangle around hint
            cv2.rectangle(hints_img, (x1, y1), (x2, y2), (255, 165, 0), 2)
            # Add text label
            cv2.putText(hints_img, f"{hint.hint_type}: {hint.hint_text}",
                      (x1, y1 - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
        plt.figure(figsize=(12, 8))
        plt.imshow(hints_img)
        plt.title(f"Detected Hints: {len(hints)} hints found")
        plt.show()
 
    if debug:
        print("\n  Grid state:")
        for i, row in enumerate(grid_matrix):
            print(f"    Row {i}: {' '.join(row)}")
        print("\n  Hints:")
        for hint in hints:
            print(f"    - {hint.hint_type}: {hint.hint_text}")
        # Visualization
        plt.figure(figsize=(10, 8))
        plt.imshow(matcher.original_image)
        plt.title("Grid Abstraction Results")
        plt.show()
    # ============ GAME LOOP ============
    input_facts = prepare_asp_input(grid_matrix, hint_lines)
    if not debug:
        plt.ion()
    while True:
        solver = DLVSolution()
        action, answer_set = solver.recall_asp(input_facts)
        if action is None:
            print("No moves found.")
            break
        else:
            row, col = action.get_row(), action.get_col()
            print(f"Action: toggle cell ({row}, {col})")
            if not vision_validation:
                plt.imshow(matcher.original_image)
                plt.title(f"About to toggle cell ({row}, {col})")
                plt.show()
                if not debug:
                    plt.pause(0.1)
            cell_x = int(offset[0] + col * delta[0] + delta[0] // 2)
            cell_y = int(offset[1] + row * delta[1] + delta[1] // 2)
            print(f"Tapping at screen coordinates ({cell_x}, {cell_y})")
            os.chdir(CLIENT_PATH)
            os.system(f"python3 client3.py --url http://{TAPPY_ORIGINAL_SERVER_IP}:8000 --light 'tap {cell_x} {cell_y}'")
            time.sleep(1)
            feedback = Feedback()
            # Feedback.main() calls abstraction_to_asp_callback(abstraction_result)
            # with a single argument (the fresh grid_matrix from matcher.abstraction()),
            # so block facts (static, from hints) are re-attached via this closure.
            success, abstraction, input_facts = feedback.request_feedback(
                matcher.vision,
                matcher.abstraction,
                lambda updated_grid_matrix: prepare_asp_input(updated_grid_matrix, hint_lines),
                answer_set
            )
            if not success:
                print("Feedback failed")
                break
    print("END MONOGRAM")
    return True
