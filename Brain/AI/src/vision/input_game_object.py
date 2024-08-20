from AI.src.vision.output_game_object import OutputRectangle
class Circle:
    def __init__(self,min_radius,canny_threshold):
        self.min_radius=min_radius
        self.canny_threshold=canny_threshold

class TemplateMatch:
    def __init__(self,templates:dict,find_all=True,regmax=True,grayscale=False):
        self.templates=templates
        self.find_all=find_all
        self.regmax = regmax
        self.grayscale=grayscale

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