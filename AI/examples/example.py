import cv2
from matplotlib import pyplot as plt

from src.candygraph.candygraph import CandyGraph
from src.candygraph.constants import PX, PY
from src.detect.detect import MatchingCandy
from src.dlvsolution.dlvsolution import DLVSolution
from src.dlvsolution.helpers import getInputDLVNodes, getEdges, Swap
from src.webservices.helpers import makeJson, requireImageFromURL


def draw(matrixCopy, nodes, color):
    width, height = 70, 70
    cv2.rectangle(matrixCopy, (nodes[PX] + 35, nodes[PY] + 35), (nodes[PX] + width, nodes[PY] + height),
                  color,
                  10)


def main():
    # require image from server
    # TODO: change ip!
    serverIp, port = "192.168.1.58", 5432
    requireImageFromURL(serverIp, port)
    print("requireImageFromURL check")

    # execute template matching
    spriteSize = (110, 110)
    matchingCandy = MatchingCandy(spriteSize)
    tmp = matchingCandy.getMatrix().copy()
    plt.imshow(tmp)
    plt.title(f"Screenshot acquired")
    plt.show()

    # take graph
    candyGraph: CandyGraph = matchingCandy.search()

    # get nodes and edges of graph for DLV
    nodesAndInformation = getInputDLVNodes(candyGraph)
    edges = getEdges(candyGraph)

    print(f"EDGES --> {edges}")
    print(f"NODES --> {nodesAndInformation}")

    # recall ASP program
    solution = DLVSolution()
    swap: Swap = solution.recallASP(edges, nodesAndInformation)

    # draw
    tmp = matchingCandy.getMatrix().copy()
    node1 = candyGraph.getNode(swap.get_id1())
    node2 = candyGraph.getNode(swap.get_id2())

    draw(tmp, node1, (255, 255, 255))
    draw(tmp, node2, (255, 255, 255))
    plt.imshow(tmp)
    plt.title(f"OPTIMUM {node1} --> {node2}.")
    plt.show()

    # make json file
    makeJson(node1[PX], node1[PY], node2[PX], node2[PY])


if __name__ == '__main__':
    main()
