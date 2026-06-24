"""
Edge length utilities for the road network.

The median edge length is used to set the min_distance parameter in
randomTrips.py, which controls the minimum OD distance for generated agents:
    min_distance = 2 × median_edge_length

The factor of 2 ensures agents traverse at least two typical edges,
filtering out trivially short trips that would not reflect realistic
route-choice behaviour.

Internal SUMO junction connector edges are excluded from all calculations.
"""

import numpy as np
from lxml import etree


def get_edge_lengths(net) -> np.ndarray:
    tree = etree.parse(net)
    lengths = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    return np.array([float(l) for l in lengths])


def get_median_edge_lengths(net):
    return round(float(np.median(get_edge_lengths(net))), 2)
