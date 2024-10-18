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
    def __init__(self,x,y,label,confidence):
        super().__init__(x,y)
        self.label=label
        self.confidence=confidence

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