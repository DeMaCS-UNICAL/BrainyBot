import networkx as nx

from AI.src.candy_crush.candygraph.constants import *
from AI.src.candy_crush.candygraph.helpers import check_in_range


class CandyGraph(nx.Graph):

    def __init__(self, difference: (), **attr):
        super().__init__(**attr)
        self.__idNumber = 0
        self.__difference = difference
        # 20% approximation
        self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2
        # print(f"APPROXIMATION: {self.__approximation}")

        self.__approximationTooClose = ((difference[PX] + difference[PY]) // 2) * 0.05

    def get_difference(self):
        return self.__difference

    def get_nodes(self) -> []:
        return list(super().nodes)

    def get_edges(self, node: ()):
        return super().adj[node]

    def get_graph(self):
        return super().adj.items()

    def get_node(self, idx: int) -> ():
        for node in self.get_nodes():
            if node[ID] == idx:
                return node

    def get_position(self, nodeS: (), nodeD: ()):
        return self[nodeS][nodeD]['position']

    def set_difference(self, difference: ()) -> None:
        self.__difference = difference
        self.__approximation = ((difference[PX] + difference[PY]) // 2) * 0.2

    def add_another_node(self, px, py, t) -> None:  # TODO: we can override this
        node = (px, py, t, self.__idNumber)
        self.__idNumber += 1

        if self.__exist_neighbours_too_close(node) is False:  # check if there are some false matching
            super().add_node(node)
            self.__insert_edge(node)

    def swap(self, idNode1: int, idNode2: int) -> None:
        node1 = self.get_node(idNode1)
        node2 = self.get_node(idNode2)
        edges1 = self.get_edges(node1)
        edges2 = self.get_edges(node2)

        self.__single_swap(node1, idNode2, edges1)
        self.__single_swap(node2, idNode1, edges2)

    def __exist_neighbours_too_close(self, node: ()) -> bool:
        for node2 in list(super().nodes):
            if self.__too_close(node, node2):
                return True

        return False

    def __too_close(self, node1: (), node2: ()) -> bool:
        return check_in_range(node1, node2, PX,
                              self.__approximationTooClose) and check_in_range(node1,
                                                                               node2, PY,
                                                                               self.__approximationTooClose)

    def __single_swap(self, source: (), destination: int, edges):
        for nbr, eattr in edges.items():
            idNbr = nbr[ID]
            super().add_edge(destination, idNbr, position=eattr)
            super().remove_edge(source, nbr)

    def __insert_edge(self, node: ()) -> None:
        for n in list(super().nodes):
            if node == n:
                continue

            p = self.__check_conditions(node, n)
            if p == HORIZONTAL or p == VERTICAL:
                super().add_edge(node, n, position=p)
                # print(f"ADDING EDGE:  ( {node}, {n} )")

    def __check_conditions(self, node, n):
        # if a nodes is linked on X or on Y with another nodes.
        if check_in_range(node, n, PX, self.__approximation) and self.__check_on_the_axis(node, n,
                                                                                          PY):
            return VERTICAL
        elif check_in_range(node, n, PY, self.__approximation) and self.__check_on_the_axis(node,
                                                                                            n,
                                                                                            PX):
            return HORIZONTAL

    def __check_on_the_axis(self, node, n, p) -> bool:
        return n[p] - self.__difference[p] - self.__approximation <= node[p] <= n[p] + self.__difference[
            p] + self.__approximation

    def __str__(self):
        return f"================= GRAPH ================= \n {super().adj.items()}"
