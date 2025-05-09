import os
import re

from languages.predicate import Predicate
from AI.src.abstraction.object_graph import ObjectGraph
from AI.src.abstraction.objectsMatrix import ObjectMatrix, TypeOf
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from specializations.clingo.desktop.clingo_desktop_service import ClingoDesktopService
from AI.src.candy_crush.object_graph.constants import TYPE, ID
from AI.src.constants import DLV_PATH
from AI.src.abstraction import mappers


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


def chooseDLVSystem() -> DesktopHandler:
    try:
        if os.name == 'nt':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
        elif os.uname().sysname == 'Darwin':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
        else:
            print(f"I will use this ASP Solver: {os.path.join(DLV_PATH, 'dlv2-linux')}")
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux")))
    except Exception as e:
        print(e)

def chooseClingo()->DesktopHandler:
    try:
        return DesktopHandler(
                ClingoDesktopService("/usr/bin/clingo"))
    except Exception as e:
        print(e)

def get_input_dlv_cells(matrix: ObjectMatrix) -> list:
    cells = []
    for row in matrix.get_cells():
        cells.extend(row)
    for row in matrix.get_cells():
        for cell in row:
            if cell.get_value()!="":
                result = re.search(r"^(\w+)\.(?:png|jpeg|jpg)$", cell.get_value())
                candyType = result.groups()[0]
                special = None
                # checks if the node2 is not swappable
                if "notTouch" in candyType:
                    continue

                if "Bomb" in candyType:
                    special="bomb"            

                if "Horizontal" in candyType:
                    special="horizontal"

                if "Vertical" in candyType:
                    special="vertical"

                if special!=None:
                    cells.append(TypeOf(cell.get_id(),special))
                result = re.search(r"^([a-z]+)[A-Z]?.*$",candyType)
                cell.set_value(result.groups()[0])
    return cells

def get_input_dlv_nodes(graph: ObjectGraph) -> []:
    nodesAndInformation = []
    for node in graph.get_nodes():

        result = re.search(r"^(\w+)\.(?:png|jpeg|jpg)$", node[TYPE])
        candyType = result.groups()[0]

        # checks if the node2 is not swappable
        if "notTouch" in candyType:
            continue

        if "Bomb" in candyType:
            result = re.search(r"^(\w+)(?:Bomb)$", candyType)
            candyType = result.groups()[0]
            nodesAndInformation.append(InputBomb(node[ID]))

        if "Horizontal" in candyType:
            result = re.search(r"^(\w+)(?:Horizontal)$", candyType)
            candyType = result.groups()[0]
            nodesAndInformation.append(InputHorizontal(node[ID]))

        if "Vertical" in candyType:
            result = re.search(r"^(\w+)(?:Vertical)$", candyType)
            candyType = result.groups()[0]
            nodesAndInformation.append(InputVertical(node[ID]))

        nodesAndInformation.append(InputNode(node[ID], candyType))

    return nodesAndInformation


def get_edges(graph: ObjectGraph) -> [Edge]:
    edges = []
    for n, nbrs in graph.get_graph():
        for nbr, eattr in nbrs.items():
            edges.append(Edge(n[ID], nbr[ID], graph.get_position(n, nbr)))

    return edges


def assert_true(expr, msg=None):
    """Check that the expression is true."""
    if not expr:
        msg = f"{msg}: {(expr)} is not true"
        raise ValueError(msg)
