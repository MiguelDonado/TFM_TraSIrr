import numpy as np
from lxml import etree


def get_edge_lengths(net) -> np.ndarray:
    tree = etree.parse(net)
    lengths = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    return np.array([float(l) for l in lengths])
