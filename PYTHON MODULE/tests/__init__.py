import cv2
from matplotlib import pyplot as plt

from src.model.CandyGraph import CandyGraph, PX, PY
from src.model.DLVClass import DLVSolution, Edge


def draw(matrixCopy, nodes, f=10):
    cv2.rectangle(matrixCopy, (nodes[PX], nodes[PY]), (nodes[PX] + width, nodes[PY] + height), (255, 0, 0), f)


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
