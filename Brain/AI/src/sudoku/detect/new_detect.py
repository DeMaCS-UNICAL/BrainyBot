import cv2
from statistics import median

from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.vision.input_game_object import Rectangle, TextRectangle
from AI.src.vision.output_game_object import OutputRectangle


class MatchingSudoku:
    def __init__(self, screenshot_path, debug=False):
        self.__finder = ObjectsFinder(screenshot_path)
        self.__debug = debug
        self.__cell_boxes = None       # 81 (x,y,w,h), row-major
        self.__keypad_boxes = None     # 9 (x,y,w,h), digit 1..9 in order
        self.__calculate_metadata()

    def get_image_width(self):
        return self.__finder.get_image_width()

    def get_image_height(self):
        return self.__finder.get_image_height()

    def __calculate_metadata(self):
        boxes, hierarchy = self.__finder.find(Rectangle(True))
        self.__boxes = boxes
        self.__hierarchy = hierarchy
        grid_container = self.__find_grid_container()
        if grid_container is None:
            return
        self.__cell_boxes = self.__find_leaf_cells(grid_container)
        grid_bottom = self.__bbox(grid_container)[1] + self.__bbox(grid_container)[3]
        self.__keypad_boxes = self.__find_keypad_boxes(grid_bottom)

    def __bbox(self, idx):
        return cv2.boundingRect(self.__boxes[idx])

    def __children_count(self):
        counts = {}
        for h in self.__hierarchy:
            if h[3] != -1:
                counts[h[3]] = counts.get(h[3], 0) + 1
        return counts

    def __find_grid_container(self):
        # The 9x9 grid is drawn with thick borders, which OpenCV's contour
        # detection sees as several nested near-duplicate rectangles of
        # almost the same size (one contour per border edge/anti-aliasing
        # ring). Rather than assuming a fixed nesting depth (outer grid ->
        # 9 sub-boxes -> 9 cells, as a naive two-level walk would), we pick
        # the largest roughly-square box whose DIRECT children are most
        # numerous -- empirically this is the hierarchy level where the
        # individual cell rectangles (or cell-cluster blobs, see
        # __find_leaf_cells) actually live for the real NYT screenshot.
        img_w = self.get_image_width()
        img_h = self.get_image_height()
        children_count = self.__children_count()

        candidates = []
        for i in range(len(self.__boxes)):
            x, y, w, h = self.__bbox(i)
            if w < img_w * 0.5 or h < img_h * 0.2:
                continue
            if abs(w - h) > 0.05 * max(w, h):
                continue
            candidates.append((i, children_count.get(i, 0)))
        if not candidates:
            return None
        candidates.sort(key=lambda t: -t[1])
        return candidates[0][0]

    def __find_leaf_cells(self, grid_container):
        # Direct children of the grid container are usually the 81 single
        # cells, but on the real screenshot some adjacent cells (near the
        # thick 3x3 sub-box borders, and cells sharing a highlighted
        # background) get merged by contour detection into one bounding
        # box spanning 2-9 cells, AND one child is itself a near-duplicate
        # of the whole grid rectangle (an inner border ring) whose own
        # children are the "merged" blobs for the missing cells. We
        # collect all of that, then split any oversized box into an NxM
        # sub-grid based on the modal single-cell size.
        _, _, cw, ch = self.__bbox(grid_container)
        container_area = cw * ch
        direct_children = [i for i, h in enumerate(self.__hierarchy) if h[3] == grid_container]

        raw_boxes = []
        for child in direct_children:
            x, y, w, h = self.__bbox(child)
            if w * h > container_area * 0.5:
                # near-duplicate of the grid container -- descend one level
                grandchildren = [i for i, hh in enumerate(self.__hierarchy) if hh[3] == child]
                raw_boxes.extend(self.__bbox(gc) for gc in grandchildren)
            else:
                raw_boxes.append((x, y, w, h))

        # drop tiny noise slivers (border-intersection artifacts)
        sized = [(x, y, w, h) for x, y, w, h in raw_boxes if w * h >= 1000]
        small = [(w, h) for x, y, w, h in sized if w < cw / 6 and h < ch / 6]
        if not small:
            return sorted(sized, key=lambda box: (round(box[1] / 10), box[0]))
        cell_w = median(w for w, h in small)
        cell_h = median(h for w, h in small)

        cells = []
        for x, y, w, h in sized:
            ncols = max(1, round(w / cell_w))
            nrows = max(1, round(h / cell_h))
            if ncols == 1 and nrows == 1:
                cells.append((x, y, w, h))
                continue
            sw, sh = w / ncols, h / nrows
            for r in range(nrows):
                for c in range(ncols):
                    cells.append((round(x + c * sw), round(y + r * sh), round(sw), round(sh)))

        # sort row-major: primarily by row (y bucketed to half a cell height), then by x
        ordered = sorted(cells, key=lambda box: (round(box[1] / (cell_h / 2)), box[0]))
        return ordered

    def __find_keypad_boxes(self, grid_bottom):
        # Each keypad button (1-9 plus X, and the separate "Undo" button
        # above them) is its own top-level contour (no shared parent),
        # unlike the brief's original assumption of 9 siblings under one
        # parent. We instead cluster top-level, button-sized boxes below
        # the grid into rows by y-coordinate, keep only full rows of 5
        # (digits 1-5, then 6-9+X), and drop the trailing X from the last row.
        depth0 = [i for i, h in enumerate(self.__hierarchy) if h[3] == -1]
        below = []
        for i in depth0:
            x, y, w, h = self.__bbox(i)
            if y > grid_bottom and 3000 < w * h < 20000:
                below.append((x, y, w, h))

        below.sort(key=lambda b: b[1])
        rows = []
        for b in below:
            for row in rows:
                if abs(row[0][1] - b[1]) < 30:
                    row.append(b)
                    break
            else:
                rows.append([b])

        full_rows = [row for row in rows if len(row) == 5]
        full_rows.sort(key=lambda row: row[0][1])
        ordered = []
        for row in full_rows:
            ordered.extend(sorted(row, key=lambda b: b[0]))
        if len(ordered) < 9:
            return None
        return ordered[:9]

    def find_grid_numbers(self):
        if self.__cell_boxes is None:
            self.__calculate_metadata()
        values = []
        for box in self.__cell_boxes:
            x, y, w, h = box
            text = self.__finder.find(TextRectangle(OutputRectangle(x, y, w, h), numeric=True))
            values.append(int(text) if text is not None else 0)
        return values

    def get_cell_position(self, row, col):
        x, y, w, h = self.__cell_boxes[row * 9 + col]
        return x + w // 2, y + h // 2

    def get_keypad_position(self, digit):
        x, y, w, h = self.__keypad_boxes[digit - 1]
        return x + w // 2, y + h // 2
