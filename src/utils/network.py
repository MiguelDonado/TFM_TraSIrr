import numpy as np
from lxml import etree


def get_edge_lengths(net) -> np.ndarray:
    tree = etree.parse(net)
    lengths = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    return np.array([float(l) for l in lengths])


def get_edges_lengths_program(net):
    return round(float(np.median(get_edge_lengths(net))), 2)
