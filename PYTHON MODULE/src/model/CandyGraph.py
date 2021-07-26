import networkx as nx

PX = 0
PY = 1
TYPE = 2
ID = 3

ON_THE_SAME_COLUMN = "column"
ON_THE_SAME_ROW = "row"


class CandyGraph(nx.Graph):

    def __init__(self, difference=None, **attr):
        super().__init__(**attr)
        self.__idNumber = 0
        self.__difference = None
        if difference is not None:
            self.__difference = difference
            # 20% approximation
            self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2
            # print(f"APPROXIMATION: {self.__approximation}")

    def getDifference(self):
        return self.__difference

    def getNodes(self) -> []:
        return list(super().nodes)

    def getAdjacent(self, node: ()):
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
        super().add_node(node)
        self.__insertEdge(node)

    def swap(self, idNode1: int, idNode2: int) -> None:
        node1 = self.getNode(idNode1)
        node2 = self.getNode(idNode2)
        edges1 = self.getAdjacent(node1)
        edges2 = self.getAdjacent(node2)

        self.__singleSwap(node1, idNode2, edges1)
        self.__singleSwap(node2, idNode1, edges2)

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
            if p == ON_THE_SAME_ROW or p == ON_THE_SAME_COLUMN:
                # print(f"LINKING: {nodes} ---> {nodes}\nodes")
                super().add_edge(node, n, position=p)

    def __checkConditions(self, node, n):

        # if a nodes is linked on X or on Y with another nodes.
        if self.__secondConditionDifference(node, n, PX) and self.__firstConditionDifference(node, n, PY):
            return ON_THE_SAME_COLUMN
        elif self.__secondConditionDifference(node, n, PY) and self.__firstConditionDifference(node, n, PX):
            return ON_THE_SAME_ROW

    def __secondConditionDifference(self, node, n, p) -> bool:
        return n[p] - self.__approximation <= node[p] <= n[p] + self.__approximation

    def __firstConditionDifference(self, node, n, p) -> bool:
        return n[p] - self.__difference[p] - self.__approximation <= node[p] <= n[p] + self.__difference[
            p] + self.__approximation

    def __str__(self):
        return f"================= GRAPH ================= \n {super().adj.items()}"
