import cv2
import os
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH
from AI.src.vision.objectsFinder import ObjectsFinder
from monogram.abstraction.abstraction import MonogramAbstraction


class MatchingMonogram:
    """Monogram detection pipeline - only detects X marks in grid"""
    
    def __init__(self, screenshot: str, debug: bool = False, 
                 validation: bool = False, iteration: int = 0,
                 grid_size: tuple = (5, 5), cell_size: tuple = (50, 50)):
        
        self.screenshot = screenshot
        self.debug = debug
        self.validation = validation
        self.grid_size = grid_size
        self.cell_size = cell_size
        
        # Initialize components
        self.abstractor = MonogramAbstraction(grid_size, cell_size)
        self.finder = ObjectsFinder(screenshot, debug=debug, validation=validation)
        
        # Cache results
        self._grid_matrix = None
        self._detected_cells = None
        self._offset = None
        self._delta = None
        self._hints = None
    
    def get_grid_state(self) -> tuple:
        """Returns (grid_matrix, detected_cells, offset, delta)"""
        if self._grid_matrix is None:
            self._process_grid()
        return self._grid_matrix, self._detected_cells, self._offset, self._delta
    
    def get_hints(self) -> list:
        """Returns list of MonogramHint objects"""
        if self._hints is None:
            self._process_hints()
        return self._hints
    
    def _process_grid(self):
        """Detect grid cells with X marks"""
        full_path = os.path.join(SCREENSHOT_PATH, self.screenshot)
        img = getImg(full_path, color_conversion=cv2.COLOR_BGR2RGB)
        
        # Detect cells with X marks
        detected_cells = self.abstractor._detect_all_cells(img)
        
        # Organize into matrix
        matrix, offset, delta = self.abstractor._organize_cells_to_matrix(detected_cells)
        
        # Cache
        self._grid_matrix = matrix
        self._detected_cells = detected_cells
        self._offset = offset
        self._delta = delta
        
        if self.debug:
            print(f"Grid: {len(matrix)}x{len(matrix[0])}, "
                  f"Found {len(detected_cells)} cells, offset={offset}, delta={delta}")
    
    def _process_hints(self):
        """Extract hint text from rectangles"""
        self._hints = self.abstractor.process_hints(self.finder)
        
        if self.debug:
            print(f"Found {len(self._hints)} hints:")
            for hint in self._hints:
                print(f"  - {hint}")
    
    def search(self) -> dict:
        """Complete search returning all game elements"""
        grid_matrix, cells, offset, delta = self.get_grid_state()
        hints = self.get_hints()
        
        return {
            'grid_matrix': grid_matrix,
            'cells': cells,
            'offset': offset,
            'delta': delta,
            'hints': hints
        }

    