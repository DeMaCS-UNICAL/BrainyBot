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
    
    def set_id(self, id):
        self.__id = id
    
class Connect:
    def __init__(self, node1=None, node2=None):
        self.__node1 = node1
        self.__node2 = node2

    def get_node1(self):
        return self.__node1

    def get_node2(self):
        return self.__node2

    def set_node1(self, node1):
        self.__node1 = node1

    def set_node2(self, node2):
        self.__node2 = node2
    
class Superior(Predicate, Connect):
    predicate_name = "superior"

    def __init__(self, node1=None, node2=None):
        Predicate.__init__(self, [("node1", int), ("node2", int)])
        Connect.__init__(self, node1, node2)

class Left(Predicate, Connect):
    predicate_name = "left"

    def __init__(self, node1=None, node2=None):
        Predicate.__init__(self, [("node1", int), ("node2", int)])
        Connect.__init__(self, node1, node2)

class Value(Predicate):
    predicate_name = "value"

    def __init__(self, node = None, value = None):
        Predicate.__init__(self, [("node", int), ("value", int)])
        self.__node = node
        self.__value = value

    def get_node(self):
        return self.__node
    
    def get_value(self):
        return self.__value
    
    def set_node(self, node):
        self.__node = node

    def set_value(self, value):
        self.__value = value


class Direction(Predicate):
    predicate_name = "direction"

    def __init__(self, dir=None):
        self.__dir = dir
        Predicate.__init__(self, [("dir", int)])

    def get_dir(self):
        return self.__dir
    
    def set_dir(self, dir):
        self.__dir = dir

    
def chooseDLVSystem() -> DesktopHandler:
    try:
        if os.name == 'nt':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
        elif os.uname().sysname == 'Darwin':
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
        else:
            return DesktopHandler(
                DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux")))
    except Exception as e:
        print(e)
