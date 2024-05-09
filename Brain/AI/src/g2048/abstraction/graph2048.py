from AI.src.g2048.dlvsolution.helpers import *

class Graph2048:
    def __init__(self, n):
        self.n = n
        self.nodes = []
        self.superior = []
        self.left = []
        self.__start()

    def __start(self):
        for i in range(self.n**2):
            self.nodes.append(Node(i))
            if i%self.n != self.n-1:
                self.left.append(Left(i, i+1))
            if i+ self.n < self.n**2:
                self.superior.append(Superior(i, i+self.n))

    def get_nodes(self):
        return self.nodes
    
    def get_superior(self):
        return self.superior
    
    def get_left(self):
        return self.left
    
    def get_value(self, l):
        value = []
        for i in range(len(l)):
            if l[i] != 0:
                value.append(Value(i, l[i]))
        return value






