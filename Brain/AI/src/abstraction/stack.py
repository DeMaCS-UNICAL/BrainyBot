

class Stack:
    def __init__(self):
        self.__x = 0
        self.__y = 0
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
