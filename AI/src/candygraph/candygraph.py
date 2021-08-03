import networkx as nx

from src.candygraph.constants import *
from src.candygraph.helpers import *


class CandyGraph(nx.Graph):

    def __init__(self, difference: (), **attr):
        super().__init__(**attr)
        self.__idNumber = 0
        self.__difference = difference
        # 20% approximation
        self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2
        # print(f"APPROXIMATION: {self.__approximation}")

        self.__approximationTooClose = ((difference[PX] + difference[PY]) // 2) * 0.05

    def getDifference(self):
        return self.__difference

    def getNodes(self) -> []:
        return list(super().nodes)

    def getEdges(self, node: ()):
        return super().adj[node]

    def getGraph(self):
        return super().adj.items()

    def getNode(self, id: int) -> ():
        for node in self.getNodes():
            if node[ID] == id:
                return node

    def getPosition(self, nodeS: (), nodeD: ()):
        return self[nodeS][nodeD]['position']

    def setDifference(self, difference: ()) -> None:
        self.__difference = difference
        self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2

    def addNode(self, px, py, t) -> None:
        node = (px, py, t, self.__idNumber)
        self.__idNumber += 1

        if self.__existNeighboursTooClose(node) is False:  # check if there are some false matching
            super().add_node(node)
            self.__insertEdge(node)

    def swap(self, idNode1: int, idNode2: int) -> None:
        node1 = self.getNode(idNode1)
        node2 = self.getNode(idNode2)
        edges1 = self.getEdges(node1)
        edges2 = self.getEdges(node2)

        self.__singleSwap(node1, idNode2, edges1)
        self.__singleSwap(node2, idNode1, edges2)

    def __existNeighboursTooClose(self, node: ()) -> bool:
        for node2 in list(super().nodes):
            if self.__tooClose(node, node2):
                return True

        return False

    def __tooClose(self, node1: (), node2: ()) -> bool:
        return checkInRange(node1, node2, PX,
                            self.__approximationTooClose) and checkInRange(node1,
                                                                           node2, PY,
                                                                           self.__approximationTooClose)

    def __singleSwap(self, source: (), destination: int, edges):
        for nbr, eattr in edges.items():
            idNbr = nbr[ID]
            super().add_edge(destination, idNbr, position=eattr)
            super().remove_edge(source, nbr)

    def __insertEdge(self, node: ()) -> None:
        for n in list(super().nodes):
            if node == n:
                continue

            p = self.__checkConditions(node, n)
            if p == HORIZONTAL or p == VERTICAL:
                super().add_edge(node, n, position=p)
                # print(f"ADDING EDGE:  ( {node}, {n} )")

    def __checkConditions(self, node, n):
        # if a nodes is linked on X or on Y with another nodes.
        if checkInRange(node, n, PX, self.__approximation) and self.__checkOnTheAxis(node, n,
                                                                                     PY):
            return VERTICAL
        elif checkInRange(node, n, PY, self.__approximation) and self.__checkOnTheAxis(node,
                                                                                       n,
                                                                                       PX):
            return HORIZONTAL

    def __checkOnTheAxis(self, node, n, p) -> bool:
        return n[p] - self.__difference[p] - self.__approximation <= node[p] <= n[p] + self.__difference[
            p] + self.__approximation

    def __str__(self):
        return f"================= GRAPH ================= \n {super().adj.items()}"
