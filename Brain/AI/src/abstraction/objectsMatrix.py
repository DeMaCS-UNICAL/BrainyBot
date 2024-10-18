
from languages.predicate import Predicate

class ObjectMatrix():

    def __init__(self, matrix, offset, delta):
        self.matrix=matrix
        self.num_row = len(self.matrix)
        self.num_col=-1
        for i in self.matrix:
            if len(i)>self.num_col:
                self.num_col=len(i)
        self.cells = self.to_cells(offset,delta)

    def set_cell(self,i,j,value):
        self.cells[i][j]=value
    
    def get_cells(self):
        return self.cells
    
    def get_cell(self,i,j=-1):
        if j!=-1:
            return self.cells[i][j]
        else:
            return self.cells[i//self.num_col][i%self.num_col]
    
    def to_cells(self,offset,delta):
        cells=[]
        for i in range(self.num_row):
            cells.append([])
            for j in range(self.num_col):
                cells[i].append(ObjectCell(i*self.num_col+j,i,j,self.matrix[i][j], j*delta[0]+offset[0],i*delta[1]+offset[1]))
        return cells
    
    def __eq__(self, other):
        # Controllo se other è un'istanza di Persona
        if isinstance(other, ObjectMatrix):
            return self.cells == other.cells
        return False
        
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

    def __eq__(self, other):
        # Controllo se other è un'istanza
        if isinstance(other, ObjectCell):
            return self.__id==other.__id and self.__i == other.__i and self.__j==other.__j and self.__value == other.__value
        return False

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

    def __eq__(self, other):
        # Controllo se other è un'istanza di Persona
        if isinstance(other, TypeOf):
            return self.__id==other.__id and self.__type == other.__type
        return False