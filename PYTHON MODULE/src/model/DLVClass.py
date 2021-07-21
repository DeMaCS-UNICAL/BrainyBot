import os
from datetime import datetime

from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper
from languages.predicate import Predicate
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService


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


class Node(Predicate):
    predicate_name = "node"

    def __init__(self, id=None, type=None):
        Predicate.__init__(self, [("id", int), ("type", int)])
        self.__id = id
        self.__type = type

    def get_id(self):
        return self.__id

    def get_type(self):
        return self.__type

    def set_id(self, id):
        self.__id = id

    def set_type(self, type):
        self.__type = type

    def __eq__(self, o: object) -> bool:
        return self.__id == o.__id


class temp(Predicate, Connect):
    predicate_name = "newEdge"

    def __init__(self, id1=None, id2=None, position=None):
        Predicate.__init__(self, [("id1", int), ("id2", int), ("position", int)])
        Connect.__init__(self, id1, id2)
        self.__position = position

    def get_position(self):
        return self.__position

    def set_position(self, position):
        self.__position = position


class DLVSolution:

    def __init__(self, nodes: [Node]):
        self.__countLogs = 0  # count for debug
        self.__dir = None  # log directory for debug
        self.__nodes = nodes

        # mapping
        ASPMapper.get_instance().register_class(Swap)
        ASPMapper.get_instance().register_class(Edge)
        ASPMapper.get_instance().register_class(Node)
        ASPMapper.get_instance().register_class(temp)

        try:
            if os.name == 'nt':
                self.__handler = DesktopHandler(
                    DLV2DesktopService(os.path.join(lib_path, "DLV2.exe")))
            elif os.uname().sysname == 'Darwin':
                self.__handler = DesktopHandler(
                    DLV2DesktopService(os.path.join(lib_path, "dlv2.mac_7")))
            else:
                self.__handler = DesktopHandler(
                    DLV2DesktopService(os.path.join(lib_path, "dlv2-linux-64_6")))

            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()

            self.__initFixed()
        except Exception as e:
            print(str(e))

    def __initFixed(self):

        # show
        self.__fixedInputProgram.add_program("\n  #show swap/2. \n ")
        # self.__fixedInputProgram.add_program("#show edgeWithTheSameTypeAndPosition/3.")
        # self.__fixedInputProgram.add_program("#show newEdge/3.")

        # only for testing
        # self.__fixedInputProgram.add_program("\n :- swap(ID,_), noConsider(ID). \n ")
        # self.__fixedInputProgram.add_program("\n :- swap(_,ID), noConsider(ID). \n ")
        # self.__fixedInputProgram.add_program("\n swap(62,70). \n")
        # end testing

        self.__fixedInputProgram.add_files_path(os.path.join(resource_path, "rules.dlv2"))

        for node in self.__nodes:
            self.__fixedInputProgram.add_object_input(node)
        self.__handler.add_program(self.__fixedInputProgram)

    # DEBUG

    def __log_program(self) -> None:
        if not os.path.exists(logs_path):
            os.mkdir(f"{logs_path}")
        if self.__countLogs == 0:
            timestamp = datetime.now()
            self.__dir = f"{timestamp.hour}-{timestamp.minute}-{timestamp.second}"
            os.mkdir(f"{logs_path}/{self.__dir}")
        with open(f"{logs_path}/{self.__dir}/TappingBOT-{self.__countLogs}.log", "w") as f:
            f.write(f"Variable: \n"
                    f"{self.__variableInputProgram.get_programs()} \n\n\n"
                    f"Fixed:\n"
                    f"{self.__fixedInputProgram.get_programs()}")
        self.__countLogs += 1

    # END DEBUG

    def recallASP(self, edges: [Edge], ignore):
        try:
            print("RECALL ASP")
            self.__variableInputProgram = ASPInputProgram()

            isNone = ignore is None  # only for testing
            # input edges

            for edge in edges:
                self.__variableInputProgram.add_object_input(edge)

            if not isNone:
                for no in ignore:  # only for testing
                    self.__variableInputProgram.add_program(f":-swap({no[0]},{no[1]}).")

            index = self.__handler.add_program(self.__variableInputProgram)
            answerSets = self.__handler.start_sync()

            # create log file for debug
            self.__log_program()  # only for testing

            swap = None
            notOptimum = None  # only for testing
            edgeNotOptimum = []  # only for testing
            print("#######################################")
            print(answerSets.get_answer_sets_string())

            for answerSet in answerSets.get_answer_sets():  # only for testing
                print(answerSet)
                for obj in answerSet.get_atoms():
                    if isinstance(obj, Swap):
                        notOptimum = Swap(obj.get_id1(), obj.get_id2())
                    elif isinstance(obj, temp):
                        tmp = temp(obj.get_id1(), obj.get_id2(), obj.get_position())
                        edgeNotOptimum.append(tmp)

            for answerSet in answerSets.get_optimal_answer_sets():
                print(answerSet)
                for obj in answerSet.get_atoms():
                    if isinstance(obj, Swap):
                        print(f"SWAP: {obj}")
                        swap = Swap(obj.get_id1(), obj.get_id2())
            print("#######################################")

            self.__handler.remove_program_from_id(index)

            if not isNone:  # only for testing
                return notOptimum, edgeNotOptimum
            else:
                return swap

        except Exception as e:
            print(str(e))
