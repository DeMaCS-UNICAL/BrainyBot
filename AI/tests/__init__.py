import os
import re
from datetime import datetime

import cv2
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper
from matplotlib import pyplot as plt
from platforms.desktop.desktop_handler import DesktopHandler
from specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService

from Application.candygraph.candygraph import CandyGraph, PX, PY, TYPE
# mapping
from Application.costants import DLV_PATH, RESOURCES_PATH
from Application.detect import getImg
from Application.detect.detect import MatchingCandy, getInputDLVNodes
from Application.detect.helpers import getEdges
from Application.dlv.dlv import Edge, Swap, AtLeast3Adjacent, InputNode, InputBomb, InputHorizontal, InputVertical

TESTS_PATH = os.path.dirname(__file__)
LOGS_PATH = os.path.join(TESTS_PATH, 'logs')
MAP_PATH = os.path.join(TESTS_PATH, 'map')

ASPMapper.get_instance().register_class(Swap)
ASPMapper.get_instance().register_class(Edge)
ASPMapper.get_instance().register_class(InputNode)
ASPMapper.get_instance().register_class(InputBomb)
ASPMapper.get_instance().register_class(InputHorizontal)
ASPMapper.get_instance().register_class(InputVertical)
ASPMapper.get_instance().register_class(AtLeast3Adjacent)

STRING = {
    # (127, 127, 127) - Gray
    # (136, 0, 21) - Bordeaux
    (255, 0, 0): "red",
    (255, 127, 0): "orange",
    (255, 255, 0): "yellow",
    (0, 255, 0): "green",
    (0, 0, 255): "blue",
    (128, 0, 128): "purple"
    # (0, 162, 232) - dark blue
    # (255, 255, 255) - white
    # (195, 195, 195) - light gray
    # (185, 122, 87) - light brown
    # (255, 174, 201) - light pink
    # (255, 201, 14) - dark yellow
    # (239, 228, 176) - light yellow
    # (181, 230, 29) - light green
    # (153, 217, 234) - light blue
    # (112, 146, 190) - dark blue
    # (200, 191, 231) - light purple
}
COLOR = {v: k for k, v in STRING.items()}
difference = (110, 110)


class DLVSolution:

    def __init__(self, nodes: []):
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
        self.__fixedInputProgram.add_program("\n #show adjacentHorizontalNodes/2. \n ")
        # self.__fixedInputProgram.add_program("#show AtLeast3Adjacent/3.")

        # only for testing
        # self.__fixedInputProgram.add_program("\node1 :- swap(ID,_), noConsider(ID). \node1 ")
        # self.__fixedInputProgram.add_program("\node1 :- swap(_,ID), noConsider(ID). \node1 ")
        # self.__fixedInputProgram.add_program("\node1 swap(62,70). \node1")
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
                # print(f"EDGE --> {edge}")
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


def draw(matrixCopy, nodes, color=None):
    width, height = 70, 70

    if color is None:
        result = re.search(r"^(\w+)\.(?:png|jpeg|jpg)$", nodes[TYPE])
        candyType = result.groups()[0]

        if "Horizontal" in candyType or "Vertical" in candyType:
            result = re.search(r"^(\w+)(?:Horizontal|Vertical)$", candyType)
            candyType = result.groups()[0]

        if "Bomb" in candyType:
            result = re.search(r"^(\w+)(?:Bomb)$", candyType)
            candyType = result.groups()[0]

        if "notTouch" in candyType or "jolly" in candyType or "2" in candyType:
            return

        color = COLOR[candyType]

    cv2.rectangle(matrixCopy, (nodes[PX] + 35, nodes[PY] + 35), (nodes[PX] + width, nodes[PY] + height),
                  color,
                  10)


def drawNotOptimumAnswer(dlvSolution: DLVSolution, candyGraph: CandyGraph, edges: [Edge], candyMatrix):
    ignore = []

    while True:
        swap, edgeNotOptimum = dlvSolution.recallASP(edges, ignore)
        if swap is None:
            break

        tmp = candyMatrix.copy()
        node1 = candyGraph.getNode(swap.get_id1())
        node2 = candyGraph.getNode(swap.get_id2())

        ignore.append((swap.get_id1(), swap.get_id2()))

        draw(tmp, node1)
        draw(tmp, node2)

        for elem in edgeNotOptimum:
            node3 = candyGraph.getNode(elem.get_id1())
            node4 = candyGraph.getNode(elem.get_id2())
            draw(tmp, node3)
            draw(tmp, node4)

        plt.imshow(tmp)
        plt.title(f"swap {node1} --> {node2}.")
        plt.show()


def drawOptimumSolution(dlvSolution: DLVSolution, candyGraph: CandyGraph, edges: [Edge], candyMatrix):
    swap = dlvSolution.recallASP(edges, None)
    # print(f"SWAP ---> {swap}")
    tmp = candyMatrix.copy()
    node1 = candyGraph.getNode(swap.get_id1())
    node2 = candyGraph.getNode(swap.get_id2())

    draw(tmp, node1, (255, 255, 255))
    draw(tmp, node2, (255, 255, 255))
    plt.imshow(tmp)
    plt.title(f"----------- OPTIMUM ---- swap {node1} --> {node2}.")
    plt.show()


def drawDetection(candyGraph: CandyGraph, candyMatrix):
    for node in candyGraph.getNodes():
        draw(candyMatrix, node)

    plt.imshow(candyMatrix)
    plt.show()


def drawSingleNodeWithID(id, candyGraph, matrix):
    if candyGraph.getNode(id) is None:
        return
    draw(matrix, candyGraph.getNode(id), (255, 255, 0))
    plt.imshow(matrix)
    plt.title(id)
    plt.show()


def drawEdgeOfNodes(node, candyGraph: CandyGraph, matrix):
    draw(matrix, node, (255, 255, 0))
    for edge in candyGraph.getEdges(node):
        draw(matrix, edge, (255, 255, 255))

    plt.imshow(matrix)
    plt.title(node)
    plt.show()


def drawAllNodesAndEdges(candyGraph: CandyGraph, candyMatrix):
    for node in candyGraph.getNodes():
        drawEdgeOfNodes(node, candyGraph, candyMatrix.copy())


########################## remove comment for testing matching
# def submission(file):
#     print(f"Analysis {file}")
#     candyMatrix = getImg(os.path.join(MAP_PATH, file))
#     matching = MatchingCandy(candyMatrix, difference)
#     candyGraph: candygraph = matching.search()
#     drawDetection(candyGraph, candyMatrix)
#
#
# with ThreadPoolExecutor(max_workers=3) as exe:
#     for file in os.listdir(MAP_PATH):
#         exe.submit(submission, file)
##########################


########################## remove comment for testing ASP optimum solution

def submission(file):
    candyMatrix = getImg(os.path.join(MAP_PATH, file))
    matching = MatchingCandy(candyMatrix, difference)
    candyGraph: CandyGraph = matching.search()
    dlvSolution = DLVSolution(getInputDLVNodes(candyGraph))
    drawOptimumSolution(dlvSolution, candyGraph, getEdges(candyGraph), candyMatrix)


# with ThreadPoolExecutor(max_workers=2) as exe:
for file in os.listdir(MAP_PATH):
    # exe.submit(submission, file)
    submission(file)

##########################
