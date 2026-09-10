import os
from languages.predicate import Predicate
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from specializations.clingo.desktop.clingo_desktop_service import ClingoDesktopService
from AI.src.constants import DLV_PATH


# ============ PREDICATE CLASSES ============

class Cell(Predicate):
    """
    Represents a grid cell with its state.
    
    Predicate: cell(row, col, state, confidence)
    Example: cell(0, 0, cross, 95)
    """
    predicate_name = "cell"
    
    def __init__(self, row=None, col=None, state=None, confidence=None):
        Predicate.__init__(self, [("row", int), ("col", int), ("state", str), ("confidence", int)])
        self.__row = row
        self.__col = col
        self.__state = state
        self.__confidence = confidence
    
    def get_row(self):
        return self.__row
    
    def get_col(self):
        return self.__col
    
    def get_state(self):
        return self.__state
    
    def get_confidence(self):
        return self.__confidence
    
    def set_row(self, row):
        self.__row = row
    
    def set_col(self, col):
        self.__col = col
    
    def set_state(self, state):
        self.__state = state
    
    def set_confidence(self, confidence):
        self.__confidence = confidence
    
    def __str__(self):
        return f"cell({self.__row}, {self.__col}, {self.__state}, {self.__confidence})"


class Hint(Predicate):
    """
    Represents a clue/hint in the puzzle.
    
    Predicate: hint(type, text)
    Example: hint(horizontal, "4B")  # Row hint: 4 consecutive black marks
    """
    predicate_name = "hint"
    
    def __init__(self, hint_type=None, text=None):
        Predicate.__init__(self, [("hint_type", str), ("text", str)])
        self.__hint_type = hint_type
        self.__text = text
    
    def get_hint_type(self):
        return self.__hint_type
    
    def get_text(self):
        return self.__text
    
    def set_hint_type(self, hint_type):
        self.__hint_type = hint_type
    
    def set_text(self, text):
        self.__text = text
    
    def __str__(self):
        return f'hint({self.__hint_type}, "{self.__text}")'


class GridSize(Predicate):
    """
    Metadata: grid dimensions.
    
    Predicate: grid_size(rows, cols)
    Example: grid_size(5, 5)
    """
    predicate_name = "grid_size"
    
    def __init__(self, rows=None, cols=None):
        Predicate.__init__(self, [("rows", int), ("cols", int)])
        self.__rows = rows
        self.__cols = cols
    
    def get_rows(self):
        return self.__rows
    
    def get_cols(self):
        return self.__cols
    
    def __str__(self):
        return f"grid_size({self.__rows}, {self.__cols})"


class Action(Predicate):
    """
    Output action: which cell to toggle/mark.
    
    Predicate: action(row, col)
    Example: action(1, 2)  # Toggle cell at row 1, col 2
    """
    predicate_name = "action"
    
    def __init__(self, row=None, col=None):
        Predicate.__init__(self, [("row", int), ("col", int)])
        self.__row = row
        self.__col = col
    
    def get_row(self):
        return self.__row
    
    def get_col(self):
        return self.__col
    
    def set_row(self, row):
        self.__row = row
    
    def set_col(self, col):
        self.__col = col
    
    def __str__(self):
        return f"action({self.__row}, {self.__col})"


# ============ ASP SOLVER SELECTION ============

def chooseDLVSystem() -> DesktopHandler:
    """
    Choose the appropriate ASP solver based on OS.
    Falls back to clingo if DLV2 is not available.
    """
    try:
        if os.name == 'nt':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
        elif os.uname().sysname == 'Darwin':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
        else:
            print(f"Using DLV2 ASP Solver: {os.path.join(DLV_PATH, 'dlv2-linux')}")
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux")))
    except Exception as e:
        print(f"DLV2 not available, trying Clingo: {e}")
        return chooseClingo()


def chooseClingo() -> DesktopHandler:
    """
    Use Clingo as ASP solver (more portable alternative to DLV2).
    """
    try:
        print("Using Clingo ASP Solver")
        return DesktopHandler(ClingoDesktopService("/usr/bin/clingo"))
    except Exception as e:
        print(f"Error initializing Clingo: {e}")
        raise
    