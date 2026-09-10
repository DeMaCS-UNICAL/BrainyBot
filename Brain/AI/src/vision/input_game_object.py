from AI.src.vision.output_game_object import OutputRectangle
class Circle:
    def __init__(self,min_radius,canny_threshold):
        self.min_radius=min_radius
        self.canny_threshold=canny_threshold

class TemplateMatch:
    def __init__(self,templates:dict,thresholds:dict, find_all=True,regmax=True,grayscale=False):
        self.templates=templates  # <nome file o cross, img>
        self.threshold_dictionary = thresholds
        self.find_all=find_all
        self.regmax = regmax
        self.grayscale=grayscale

class SimplifiedTemplateMatch:
    def __init__(self,templates:dict,size:tuple, grayscale=False):
        self.templates=templates
        self.grayscale=grayscale
        self.width = size[0]
        self.heigth = size[1]
        
class Rectangle:
    def __init__(self,hierarchy=False):
        self.hierarchy=hierarchy

class TextRectangle:
    def __init__(self,rectangle:OutputRectangle,dictionary=None,regex=None,numeric = False):
        self.rectangle=rectangle
        if numeric and (dictionary!=None or regex!=None):
            raise Exception("Dictionary and regex parameters are incompatible with numeric being True.")
        if regex!=None and dictionary!=None:
            raise Exception("Only one among 'dictionary' and 'regex' parameters can be valorized.")
        self.numeric=numeric
        self.dictionary=dictionary
        self.regex=regex

class Container:
    def __init__(self,template,proportion_tolerance=0,size_tolerance=0,rotate=False):
        self.template=template
        self.proportion_tolerance=proportion_tolerance
        self.size_tolerance=size_tolerance
        self.rotate=rotate

from AI.src.vision.input_game_object import TemplateMatch, SimplifiedTemplateMatch, TextRectangle


class MonogramCellDetection(TemplateMatch):
    """
    Detection specification for Monogram grid cells using TemplateMatch.
    
    We use template matching to detect cells with an "X" mark by:
    - Uploading a template image of a cell with an X
    - Using opencv's matchTemplate to find matches
    """
    def __init__(self, templates: dict, thresholds: dict, find_all=True, regmax=True, grayscale=False):
        """
        Args:
            templates: Dict mapping cell_type -> template_image
                      Example: {'cross': cross_template_img, 'empty': empty_template_img}
            thresholds: Dict mapping cell_type -> confidence_threshold (0-1)
                       Example: {'cross': 0.7, 'empty': 0.6}
            find_all: Find all matches (True) or just first one (False)
            regmax: Use regional max suppression to filter overlapping matches
            grayscale: Process images in grayscale
        """
        super().__init__(templates, thresholds, find_all=find_all, regmax=regmax, grayscale=grayscale)


class MonogramHintDetection(TextRectangle):
    """
    Detection specification for hint rectangles.
    Inherits from TextRectangle to extract text from rectangles.
    """
    def __init__(self, rectangle, dictionary=None, regex=None, numeric=False):
        """
        Args:
            rectangle: OutputRectangle specifying the region
            dictionary: Optional path to dictionary file for text validation
            regex: Optional regex pattern for text matching
            numeric: Set to True to extract only numbers
        """
        super().__init__(rectangle, dictionary=dictionary, regex=regex, numeric=numeric)
