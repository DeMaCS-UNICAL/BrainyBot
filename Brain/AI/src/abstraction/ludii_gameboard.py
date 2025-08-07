import re
import cv2

from AI.src.vision.objectsFinder import ObjectsFinder
from AI.src.abstraction.abstraction import Abstraction
from AI.src.abstraction.objectsMatrix import ObjectMatrix
from AI.src.vision.input_game_object import TemplateMatch, Rectangle


class LudiiGameBoard:
    """Utility class for extracting a board from a Ludii description.

    Given the path to a ``.lud`` file and a screenshot, this class parses the
    equipment section of the Ludii description and tries to detect a
    corresponding board on the screenshot.  Detection of pieces relies on the
    existing :class:`ObjectsFinder`'s ``find`` method while grids are
    represented through :class:`ObjectMatrix`.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug

    def _extract_equipment(self, lud_content: str) -> str:
        """Return the raw text of the equipment section from a lud file."""
        match = re.search(r"\(equipment\s*\{(.*?)\}\)", lud_content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _board_layout_from_equipment(self, equipment: str) -> str:
        """Very naive extraction of the board layout type from equipment."""
        if "square" in equipment:
            return "square"
        if "hex" in equipment:
            return "hex"
        if "triangle" in equipment:
            return "triangle"
        return "unknown"

    def detect_board(self, lud_path: str, screenshot: str):
        """Detect board and pieces according to the equipment section."""
        with open(lud_path, "r", encoding="utf-8") as lud_file:
            equipment = self._extract_equipment(lud_file.read())

        layout = self._board_layout_from_equipment(equipment)
        finder = ObjectsFinder(screenshot, color=cv2.COLOR_BGR2RGB, debug=self.debug)

        if layout == "square":
            # Find all rectangles composing the grid and convert them to a matrix
            rectangles = finder.find(Rectangle(True))
            abstraction = Abstraction()
            # TODO: determine distance between cells from equipment
            matrix_rep, offset, delta = abstraction.ToMatrix(rectangles, (0, 0))
            grid = ObjectMatrix(matrix_rep, offset, delta)

            # TODO: provide actual templates based on equipment pieces
            pieces = finder.find(TemplateMatch({}, {}))
            return grid, pieces

        if layout == "hex":
            # TODO: implement detection for hexagonal boards
            raise NotImplementedError("Hex boards are not supported yet")

        if layout == "triangle":
            # TODO: implement detection for triangular boards
            raise NotImplementedError("Triangle boards are not supported yet")

        raise NotImplementedError(f"Board layout '{layout}' is not implemented")
