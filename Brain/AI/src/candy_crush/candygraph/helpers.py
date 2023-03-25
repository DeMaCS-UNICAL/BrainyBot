def check_in_range(node1: (), node2: (), p: int, approximation) -> bool:
    return node1[p] - approximation <= node2[p] <= node1[p] + approximation
