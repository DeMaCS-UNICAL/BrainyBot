import os

from languages.asp.asp_input_program import ASPInputProgram
from languages.predicate import Predicate

from Application.costants import RESOURCES_PATH
from Application.dlv.helpers import chooseDLVSystem


class Connect:
    def __init__(self, id1=None, id2=None):
        self.__id1 = id1
        self.__id2 = id2

    def get_id1(self):
        return self.__id1

    def get_id2(self):
        return self.__id2

    def set_id1(self, id1):
        self.__id1 = id1

    def set_id2(self, id2):
        self.__id2 = id2

    def __str__(self):
        return f"({self.__id1}, {self.__id2})\n"


class Edge(Predicate, Connect):
    predicate_name = "edge"

    def __init__(self, id1=None, id2=None, position=None):
        Predicate.__init__(self, [("id1", int), ("id2", int), ("position", int)])
        Connect.__init__(self, id1, id2)
        self.__position = position

    def get_position(self):
        return self.__position

    def set_position(self, position):
        self.__position = position


class Swap(Predicate, Connect):
    predicate_name = "swap"

    def __init__(self, id1=None, id2=None):
        Predicate.__init__(self, [("id1", int), ("id2", int)])
        Connect.__init__(self, id1, id2)


class InformationID:
    def __init__(self, nodeID=None):
        self.__id = nodeID

    def get_id(self):
        return self.__id

    def set_id(self, nodeID):
        self.__id = nodeID

    def __eq__(self, o: object) -> bool:
        return self.__id == o.__id

    def __str__(self) -> str:
        return f"Information({self.__id}) \n"


class Node(InformationID):

    def __init__(self, nodeID=None, candyType=None):
        super().__init__(nodeID)
        self.__type = candyType

    def get_type(self):
        return self.__type

    def set_type(self, candyType):
        self.__type = candyType

    def __str__(self) -> str:
        return f"node2({super().get_id()}, {self.__type}) \n"


class InputNode(Predicate, Node):
    predicate_name = "node"

    def __init__(self, nodeID=None, candyType=None):
        Predicate.__init__(self, [("id", int), ("type", int)])
        Node.__init__(self, nodeID, candyType)


class InputBomb(Predicate, InformationID):
    predicate_name = "bomb"

    def __init__(self, nodeID=None):
        Predicate.__init__(self, [("id", int)])
        InformationID.__init__(self, nodeID)

    def __str__(self) -> str:
        return f"bomb({super().get_id()}) \n"


class InputVertical(Predicate, InformationID):
    predicate_name = "vertical"

    def __init__(self, nodeID=None):
        Predicate.__init__(self, [("id", int)])
        InformationID.__init__(self, nodeID)

    def __str__(self) -> str:
        return f"vertical({super().get_id()}) \n"


class InputHorizontal(Predicate, InformationID):
    predicate_name = "horizontal"

    def __init__(self, nodeID=None):
        Predicate.__init__(self, [("id", int)])
        InformationID.__init__(self, nodeID)

    def __str__(self) -> str:
        return f"horizontal({super().get_id()}) \n"


class NewEdge(Predicate, Connect):
    predicate_name = "newEdge"

    def __init__(self, id1=None, id2=None, position=None):
        Predicate.__init__(self, [("id1", int), ("id2", int), ("position", int)])
        Connect.__init__(self, id1, id2)
        self.__position = position

    def get_position(self):
        return self.__position

    def set_position(self, position):
        self.__position = position


class AtLeast3Adjacent(Predicate, Connect):
    predicate_name = "AtLeast3Adjacent"

    def __init__(self, id1=None, id2=None, position=None):
        Predicate.__init__(self, [("id1", int), ("id2", int), ("position", int)])
        Connect.__init__(self, id1, id2)
        self.__position = position

    def get_position(self):
        return self.__position

    def set_position(self, position):
        self.__position = position


class DLVSolution:

    def __init__(self, nodes: [InputNode]):
        self.__nodes = nodes

        try:
            self.__handler = chooseDLVSystem()
            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()

            self.__initFixed()
        except Exception as e:
            print(str(e))

    def __initFixed(self):
        self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, "rules.dlv2"))
        for node in self.__nodes:
            self.__fixedInputProgram.add_object_input(node)
        self.__handler.add_program(self.__fixedInputProgram)

    def recallASP(self, edges: [Edge]) -> Swap:
        try:
            self.__variableInputProgram = ASPInputProgram()
            for edge in edges:  # add edges input to dlv program
                self.__variableInputProgram.add_object_input(edge)

            index = self.__handler.add_program(self.__variableInputProgram)
            answerSets = self.__handler.start_sync()

            swap = None
            for answerSet in answerSets.get_optimal_answer_sets():
                print(answerSet)
                for obj in answerSet.get_atoms():
                    if isinstance(obj, Swap):
                        swap = Swap(obj.get_id1(), obj.get_id2())

            self.__handler.remove_program_from_id(index)
            return swap

        except Exception as e:
            print(str(e))
