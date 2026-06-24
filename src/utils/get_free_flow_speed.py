"""
Compute the length-weighted average free-flow speed of the network.

Used by demand calibration as the denominator of the congestion proxy:
    congestion_ratio = avg_speed / free_flow_speed

Formula
-------
    free_flow_speed = Σ (speed_i × length_i) / Σ length_i

where the sum runs over all non-internal lanes (internal lanes are
SUMO-generated connector segments at junctions, not real road links).

Network note
------------
Both networks used in the project use a uniform speed limit of 13.89 m/s on all edges,
so the weighted average is trivially constant. The general formula is
kept so the function works on heterogeneous networks without changes.
Homogeneous speed is an intentional simplification — the experiment
focuses on route-choice behaviour.
"""

import numpy as np
from lxml import etree


def get_free_flow_speed(net):
    """
    We dont want to get info about internal junctions.
    """

    ###########
    # SCRIPT
    ###########

    document = net
    tree = etree.parse(document)

    # Helper variables
    total_length = 0
    speeds = []
    lengths = []

    # Lanes
    lanes_elements = tree.xpath("//edge[not(@function='internal')]/lane")
    for lane_element in lanes_elements:
        speed = float(lane_element.get("speed"))
        length = float(lane_element.get("length"))

        total_length += length
        speeds.append(speed)
        lengths.append(length)

    weights = [length / total_length for length in lengths]

    free_flow_speed = round(np.average(a=speeds, weights=weights), 2)
    return free_flow_speed
