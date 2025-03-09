from AI.src.vision.output_game_object import OutputRectangle
class Circle:
    def __init__(self,min_radius,canny_threshold, max_radius = None,area = None, not_this_coordinates = None):
        self.min_radius=min_radius
        self.canny_threshold=canny_threshold
        self.max_radius=max_radius
        self.area = area
        self.not_this_coordinates = not_this_coordinates

class TemplateMatch:
    def __init__(self,templates:dict,thresholds:dict, find_all=True,regmax=True,grayscale=False):
        self.templates=templates
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