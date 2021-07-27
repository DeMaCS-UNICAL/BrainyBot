import cv2

from Application.candygraph.candygraph import CandyGraph
from Application.candygraph.constants import ID
from Application.dlv.dlv import Edge


def getImg(file):
    try:
        im = cv2.imread(file)
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    except:
        raise Exception(f"NO {file} FOUND. \n")


def getEdges(graph: CandyGraph) -> [Edge]:
    edges = []
    for n, nbrs in graph.getGraph():
        for nbr, eattr in nbrs.items():
            edges.append(Edge(n[ID], nbr[ID], graph.getPosition(n, nbr)))

    return edges
