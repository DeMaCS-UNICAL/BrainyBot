class OutputGameObject:
    def __init__(self, x,y):
        self.x=x
        self.y=y

class OutputCircle(OutputGameObject):
    def __init__(self,x,y,radius,color):
        super().__init__(x,y)
        self.radius=radius
        self.color=color

class OutputTemplateMatch(OutputGameObject):
    def __init__(self,x,y,width,heigth,label,confidence):
        super().__init__(x,y)
        self.label=label
        self.confidence=confidence
        self.template_width=width
        self.template_heigth=heigth

    def __str__(self) -> str:
        return self.label

class OutputRectangle(OutputGameObject):
    def __init__(self,x,y,width,heigth):
        super().__init__(x,y)
        self.width=width
        self.heigth=heigth

class OutputRectangleWithHierarchy:
    def __init__(self,rectangle,hierarchy):
        self.rectangle = rectangle
        self.hierarchy=hierarchy

class OutputText:
    def __init__(self,text):
        self.text=text

class OutputContainer(OutputGameObject):
    def __init__(self, x,y,contour):
        super().__init__(x,y)
        self.contour=contour
        self.id=None
    
    def set_id(self,id):
        self.id=id


class MonogramCell(OutputGameObject):
    """
    Represents a single cell in the Monogram grid.
    
    We only track whether a cell HAS an "X" marked in it or not.
    No color tracking - just the presence/absence of the cross.
    """
    def __init__(self, x: float, y: float, has_cross: bool, 
                 confidence: float, cell_id: str = None):
        """
        Args:
            x, y: Center coordinates of the cell
            has_cross: True if cell contains X, False if empty
            confidence: Detection confidence (0-1) for the cross detection
            cell_id: Position identifier (e.g., "x0y1" for row 0, col 1)
        """
        super().__init__(x, y)
        self.has_cross = has_cross    # True or False - that's it!
        self.confidence = confidence
        self.cell_id = cell_id
        self.cell_width = None
        self.cell_height = None
    
    def __str__(self) -> str:
        """Returns grid representation: X for marked, . for empty"""
        return "X" if self.has_cross else "."
    
    def __repr__(self) -> str:
        return f"MonogramCell({self.cell_id}, has_cross={self.has_cross}, conf={self.confidence:.2f})"


class MonogramHint(OutputGameObject):
    """
    Represents a hint rectangle with clue text.
    Located outside the main grid.
    Example: "4B" means 4 consecutive marked cells
    """
    def __init__(self, x: float, y: float, width: float, height: float, 
                 hint_text: str, hint_type: str = "clue"):
        """
        Args:
            x, y: Top-left corner of hint rectangle
            width, height: Dimensions of hint rectangle
            hint_text: Extracted text from the hint (e.g., "4B", "W1")
            hint_type: Type of hint ("horizontal", "vertical", "clue")
        """
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.hint_text = hint_text
        self.hint_type = hint_type
    
    def __repr__(self) -> str:
        return f"MonogramHint({self.hint_type}, '{self.hint_text}')"


class MonogramGrid(OutputGameObject):
    """Represents the entire Monogram grid"""
    def __init__(self, x: float, y: float, grid_width: int, grid_height: int):
        super().__init__(x, y)
        self.grid_width = grid_width
        self.grid_height = grid_height
