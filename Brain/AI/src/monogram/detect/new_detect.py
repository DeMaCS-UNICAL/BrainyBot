import cv2
import os
from matplotlib import pyplot as plt
from AI.src.constants import SCREENSHOT_PATH
from AI.src.abstraction.helpers import getImg
from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.monogram.detect.constants import TEMPLATES, THRESHOLDS, DISTANCE
from AI.src.vision.input_game_object import TemplateMatch
from AI.src.abstraction.abstraction import MonogramAbstraction


class MatchingMonogram:
    """Monogram detection pipeline - template matching then abstraction"""
    
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
        
        # Store original image
        full_path = os.path.join(SCREENSHOT_PATH, screenshot)
        self.original_image = getImg(full_path, color_conversion=cv2.COLOR_BGR2RGB)
        
        # Cache results
        self._template_matches = None      # ← After template matching
        self._grid_matrix = None           # ← After abstraction
        self._detected_cells = None        # ← After abstraction
        self._offset = None                # ← After abstraction
        self._delta = None                 # ← After abstraction
        self._hints = None
    
    def get_template_matches(self) -> list:
        """
        STEP 1: Run template matching on the screenshot.
        
        Returns:
            List of OutputTemplateMatch objects from template matching
        """
        if self._template_matches is None:
            print("  [Template Matching] Running template matching...")
            
            # Create TemplateMatch search object
            search = TemplateMatch(
                templates=TEMPLATES,
                thresholds=THRESHOLDS,
                find_all=True,
                regmax=True,
                grayscale=False
            )
            
            # Execute template matching
            self._template_matches = self.finder.find(search)
            
            print(f"  [Template Matching] Found {len(self._template_matches)} matches")
            
            if self.debug:
                print(f"\n  Template matches:")
                for i, match in enumerate(self._template_matches[:10]):
                    print(f"    {i+1}. {match.label} at ({match.x}, {match.y}) - confidence: {match.confidence:.2f}")
                if len(self._template_matches) > 10:
                    print(f"    ... and {len(self._template_matches) - 10} more")
        
        return self._template_matches
    
    def get_grid_state(self) -> tuple:
        """
        STEP 2: Take template matches and run abstraction.
        
        This function now:
        1. First calls get_template_matches() to get raw matches
        2. Then processes them through abstraction
        
        Returns:
            Tuple of (grid_matrix, detected_cells, offset, delta)
        """
        if self._grid_matrix is None:
            print("  [Abstraction] Processing template matches...")
            
            # STEP 1: Get raw template matches first
            template_matches = self.get_template_matches()
            
            # STEP 2: Convert matches to MonogramCell objects
            detected_cells = self.abstractor._process_template_matches(template_matches)
            
            # STEP 3: Organize into matrix
            matrix, offset, delta = self.abstractor._organize_cells_to_matrix(detected_cells)
            
            # Cache results
            self._grid_matrix = matrix
            self._detected_cells = detected_cells
            self._offset = offset
            self._delta = delta
            
            print(f"  [Abstraction] Generated grid: {len(matrix)}×{len(matrix[0])}")
        
        return self._grid_matrix, self._detected_cells, self._offset, self._delta
    
    def get_hints(self) -> list:
        """Extract hints from rectangles"""
        if self._hints is None:
            self._hints = self.abstractor.process_hints(self.finder)
        return self._hints
    
    def search(self) -> dict:
        """Complete search - returns all detected elements"""
        # Get template matches first
        template_matches = self.get_template_matches()
        
        # Then get grid state (which uses template matches)
        grid_matrix, cells, offset, delta = self.get_grid_state()
        
        # Get hints
        hints = self.get_hints()
        
        return {
            'template_matches': template_matches,  # ← Raw matches
            'grid_matrix': grid_matrix,            # ← Abstract matrix
            'cells': cells,
            'offset': offset,
            'delta': delta,
            'hints': hints
        }