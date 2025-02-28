from languages.predicate import Predicate
from AI.src.constants import DLV_PATH

class Element(Predicate):
    predicate_name = "candy"
    def __init__(self, i, j, type):
        Predicate.__init__(self, [("i", int), ("j", int), ("type", str)])
        self.__i = i
        self.__j = j
        self.__type = type
        self.predicate_name = Element.predicate_name

    def get_i(self):
        return self.__i

    def set_i(self, i):
        self.__i = i
        
    def get_j(self):
        return self.__j

    def set_j(self, j):
        self.__j = j
        
    def get_type(self):
        return self.__type

    def set_type(self, type):
        self.__type = type
    
    def __str__(self) -> str:
        return f"{self.predicate_name}({self.__i},{self.__j},{self.__type}) \n"
        
class InputBomb(Element):
    predicate_name = "bomb"
    def __init__(self,i,j,type):
        super().__init__(i,j,type)
        self.predicate_name=InputBomb.predicate_name


class InputVertical(Element):
    predicate_name = "vertical"
    def __init__(self,i,j,type):
        super().__init__(i,j,type)
        self.predicate_name=InputVertical.predicate_name

class InputHorizontal(Element):
    predicate_name = "horizontal"
    def __init__(self,i,j,type):
        super().__init__(i,j,type)
        self.predicate_name=InputHorizontal.predicate_name
