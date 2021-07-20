import networkx as nx

PX = 0
PY = 1
T = 2
ID = 3

ON_THE_SAME_COLUMN = 0
ON_THE_SAME_ROW = 1


class CandyGraph:
    def __init__(self, difference: ()):
        self.__idNumber = 0
        self.__graph = nx.Graph()
        self.__difference = difference

        # 20% approximation
        self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2
        print(f"APPROXIMATION: {self.__approximation}")

    def getDifference(self):
        return self.__difference

    def getNodes(self) -> []:
        return list(self.__graph.nodes)

    def getAdjacent(self, node: ()):
        return self.__graph.adj[node]

    def getGraph(self):
        return self.__graph.adj.items()

    def getNode(self, id: int) -> ():
        for node in self.getNodes():
            if node[ID] == id:
                return node

    def getPosition(self, nodeS: (), nodeD: ()):
        return self.__graph[nodeS][nodeD]['position']

    def setDifference(self, difference: ()) -> None:
        self.__difference = difference
        self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2

    def addNode(self, px, py, t) -> None:
        node = (px, py, t, self.__idNumber)
        self.__idNumber += 1
        self.__graph.add_node(node)
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
            self.__graph.add_edge(destination, idNbr, position=eattr)
            self.__graph.remove_edge(source, nbr)

    def __insertEdge(self, node: ()) -> None:
        for n in list(self.__graph.nodes):
            if node == n:
                continue

            p = self.__checkConditions(node, n)
            if p == ON_THE_SAME_ROW or p == ON_THE_SAME_COLUMN:
                # print(f"LINKING: {nodes} ---> {nodes}\nodes")
                self.__graph.add_edge(node, n, position=p)

    def __checkConditions(self, node, n) -> int:

        # if a nodes is linked on X or on Y with another nodes.
        if self.__secondConditionDifference(node, n, PX) and self.__firstConditionDifference(node, n, PY):
            return ON_THE_SAME_COLUMN
        elif self.__secondConditionDifference(node, n, PY) and self.__firstConditionDifference(node, n, PX):
            return ON_THE_SAME_ROW

    def __secondConditionDifference(self, node, n, p) -> bool:
        difference = self.__difference[p] // 2
        return n[p] - difference <= node[p] <= n[p] + difference

    def __firstConditionDifference(self, node, n, p) -> bool:
        return n[p] - self.__difference[p] - self.__approximation <= node[p] <= n[p] + self.__difference[
            p] + self.__approximation

    def __str__(self):
        return f"================= GRAPH ================= \n{self.__graph.adj.items()}"