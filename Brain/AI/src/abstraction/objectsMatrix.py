
from languages.predicate import Predicate

class ObjectMatrix():

    def __init__(self, matrix, offset, delta):
        self.matrix=matrix
        self.cells = self.to_cells(offset,delta)

    def set_cell(self,i,j,value):
        self.cells[i][j]=value
    
    def get_cells(self):
        return self.cells
    
    def get_cell(self,i,j=-1):
        if j!=-1:
            return self.cells[i][j]
        else:
            return self.cells[i//len(self.matrix)][i%len(self.matrix[0])]
    
    def to_cells(self,offset,delta):
        cells=[]
        n=len(self.matrix)
        m=len(self.matrix[0])
        for i in range(n):
            cells.append([])
            for j in range(m):
                cells[i].append(ObjectCell(i*n+j,i,j,self.matrix[i][j], j*delta[0]+offset[0],i*delta[1]+offset[1]))
        return cells
    
class ObjectCell(Predicate):
    predicate_name="cell"

    def __init__(self,id,i,j,value,x,y):
        Predicate.__init__(self, [("id",int),("i", int), ("j", int), ("value", str)])
        self.__i=i
        self.__j=j
        self.__id = id
        self.__value=value if value!= None else ""
        self.x=x
        self.y=y

    def get_id(self):
        return self.__id
    
    def get_i(self):
        return self.__i
    
    def get_j(self):
        return self.__j
    
    def get_value(self):
        return self.__value
    
    def set_id(self,id):
        self.__id = id

    def set_i(self,i):
        self.__i = i 

    def set_j(self,j):
        self.__j = j

    def set_value(self,value):
        self.__value = value

class TypeOf(Predicate):
    predicate_name = "type_of"
    def __init__(self,id,type):
        Predicate.__init__(self, [("id",int),("type", str)])
        self.__id = id
        self.__type=type

    def get_id(self):
        return self.__id
    
    def set_id(self,v):
        self.__id = v
    
    def get_type(self):
        return self.__type

    def set_type(self,v):
        self.__type=v