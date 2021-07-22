import os
from datetime import datetime
from time import sleep

import cv2
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper
from matplotlib import pyplot as plt
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService

from setup import RESOURCES_PATH, LOGS_PATH, DLV_PATH, MAP_PATH
from src.model.CandyGraph import CandyGraph, PX, PY
from src.model.DLVClass import Edge, Swap, AtLeast3Adjacent, Node
from src.model.Matching import MatchingCandy, getNodes, getImg

# mapping
ASPMapper.get_instance().register_class(Swap)
ASPMapper.get_instance().register_class(Edge)
ASPMapper.get_instance().register_class(Node)
ASPMapper.get_instance().register_class(AtLeast3Adjacent)


class DLVSolution:

    def __init__(self, nodes: [Node]):
        self.__countLogs = 0  # count for debug
        self.__dir = None  # log directory for debug
        self.__nodes = nodes

        try:
            if os.name == 'nt':
                self.__handler = DesktopHandler(
                    DLV2DesktopService(os.path.join(DLV_PATH, "DLV2.exe")))
            elif os.uname().sysname == 'Darwin':
                self.__handler = DesktopHandler(
                    DLV2DesktopService(os.path.join(DLV_PATH, "dlv2.mac_7")))
            else:
                self.__handler = DesktopHandler(
                    DLV2DesktopService(os.path.join(DLV_PATH, "dlv2-linux-64_6")))

            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()

            self.__initFixed()
        except Exception as e:
            print(str(e))

    def __initFixed(self):

        # show
        self.__fixedInputProgram.add_program("\n  #show swap/2. \n ")
        # self.__fixedInputProgram.add_program("#show edgeWithTheSameTypeAndPosition/3.")
        # self.__fixedInputProgram.add_program("#show AtLeast3Adjacent/3.")

        # only for testing
        # self.__fixedInputProgram.add_program("\n :- swap(ID,_), noConsider(ID). \n ")
        # self.__fixedInputProgram.add_program("\n :- swap(_,ID), noConsider(ID). \n ")
        # self.__fixedInputProgram.add_program("\n swap(62,70). \n")
        # end testing

        self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, "rules.dlv2"))

        for node in self.__nodes:
            self.__fixedInputProgram.add_object_input(node)
        self.__handler.add_program(self.__fixedInputProgram)

    # DEBUG

    def __log_program(self) -> None:
        if not os.path.exists(LOGS_PATH):
            os.mkdir(f"{LOGS_PATH}")
        if self.__countLogs == 0:
            timestamp = datetime.now()
            self.__dir = f"{timestamp.hour}-{timestamp.minute}-{timestamp.second}"
            os.mkdir(f"{LOGS_PATH}/{self.__dir}")
        with open(f"{LOGS_PATH}/{self.__dir}/TappingBOT-{self.__countLogs}.log", "w") as f:
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
                    elif isinstance(obj, AtLeast3Adjacent):
                        tmp = AtLeast3Adjacent(obj.get_id1(), obj.get_id2(), obj.get_position())
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


def draw(matrixCopy, nodes):
    width, height = 89, 94
    cv2.rectangle(matrixCopy, (nodes[PX], nodes[PY]), (nodes[PX] + width, nodes[PY] + height), (255, 0, 0), 10)


def drawNotOptimumAnswer(dlvSolution: DLVSolution, graph: CandyGraph, edges: [Edge], candyMatrix):
    ignore = []

    while True:
        swap, edgeNotOptimum = dlvSolution.recallASP(edges, ignore)
        if swap is None:
            break

        tmp = candyMatrix.copy()
        node1 = graph.getNode(swap.get_id1())
        node2 = graph.getNode(swap.get_id2())

        ignore.append((swap.get_id1(), swap.get_id2()))

        draw(tmp, node1)
        draw(tmp, node2)

        for elem in edgeNotOptimum:
            node3 = graph.getNode(elem.get_id1())
            node4 = graph.getNode(elem.get_id2())
            draw(tmp, node3)
            draw(tmp, node4)

        plt.imshow(tmp)
        plt.title(f"swap {node1} --> {node2}.")
        plt.show()


def drawOptimumSolution(dlvSolution: DLVSolution, graph: CandyGraph, edges: [Edge], candyMatrix):
    swap = dlvSolution.recallASP(edges, None)
    tmp = candyMatrix.copy()
    node1 = graph.getNode(swap.get_id1())
    node2 = graph.getNode(swap.get_id2())

    draw(tmp, node1)
    draw(tmp, node2)
    plt.imshow(tmp)
    plt.title(f"----------- OPTIMUM ---- swap {node1} --> {node2}.")
    plt.show()


matrix = getImg(os.path.join(MAP_PATH, "matrix1.jpeg"))
matching = MatchingCandy(matrix)
candyGraph: CandyGraph = matching.search()
for node in getNodes(candyGraph):
    print(f"NODE --> {node}")
    tmp = matrix.copy()
    nodeOnImg = candyGraph.getNode(node.get_id())
    print(nodeOnImg)
    draw(tmp, nodeOnImg)
    plt.imshow(tmp)
    plt.show()

    sleep(0.25)
