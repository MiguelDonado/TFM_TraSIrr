"""
Compute the total road length of the network in kilometres.

Used in demand calibration to seed the initial demand guess:
    demand = heuristic_veh_km_hour × total_length_km × hours

Internal SUMO junction connector edges are excluded — they are
not real road links and would inflate the length.
"""

from lxml import etree


def get_total_length_network(net):
    ###########
    # SCRIPT
    ###########

    # Lanes
    lanes = 0

    document = net
    tree = etree.parse(document)

    # Lanes
    lanes_lengths = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    lanes_lengths = [float(lane_length) for lane_length in lanes_lengths]

    total_length_network_m = sum(lanes_lengths)
    total_length_network_km = total_length_network_m / 1000

    return total_length_network_km
