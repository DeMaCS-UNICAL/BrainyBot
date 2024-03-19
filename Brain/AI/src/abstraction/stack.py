

class Stack:
    def __init__(self,t=(0,0)):
        self.__x = t[0]
        self.__y = t[1]
        self.__elements = []

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_elements(self) -> list:
        return self.__elements

    def set_x_coordinates(self, x):
        self.__x = x

    def set_y_coordinate(self, y=None):
        if y is None:
            self.__y = int(sum([element[1] for element in self.__elements]) / len(self.__elements))
        else:
            self.__y = y

    def sort_elements(self):
        pass

    def add_element(self, element: list):
        self.__elements.append(element)
    
    def add_elements(self, elements: list):
        self.__elements.extend(elements)

    def to_string(self):
        result=""
        for elem in self.get_elements():
            result+=elem.to_string()+"\n"
        return result