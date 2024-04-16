import os

from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from AI.src.constants import DLV_PATH

from languages.predicate import Predicate


    
class Node(Predicate):
    predicate_name = "node"

    def __init__(self, id=None):
        self.__id = id
        Predicate.__init__(self, [("id", int)])

    def get_id(self):
        return self.__id
    
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
    
class Superior(Predicate, Connect):
    predicate_name = "superior"

    def __init__(self, node1, node2):
        Predicate.__init__(self, [("id1", int), ("id2", int)])
        Connect.__init__(self, node1, node2)

class Left(Predicate, Connect):
    predicate_name = "left"

    def __init__(self, node1, node2):
        Predicate.__init__(self, [("id1", int), ("id2", int)])
        Connect.__init__(self, node1, node2)

class Value(Predicate):
    predicate_name = "value"

    def __init__(self, node, value):
        Predicate.__init__(self, [("id", int), ("value", int)])
        self.node = node
        self.value = value

    def get_id(self):
        return self.node
    
    def get_value(self):
        return self.value

class Direction(Predicate):
    predicate_name = "direction"

    def __init__ (self, d):
        self.direction = d
        Predicate.__init__(self, [("d", int)])

    def get_dir(self):
        return self.direction
    
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
