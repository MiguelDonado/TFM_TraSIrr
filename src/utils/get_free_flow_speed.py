"""
Purpose of this script is to get the avg free flow speed of the network
A weighted average of the max speed on each lane. The weights are the length of the lanes
"""

import numpy as np
from lxml import etree

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Koh/FirstNetwork_Koh.net.xml"


def get_free_flow_speed(net=NETWORK_PATH):
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


if __name__ == "__main__":
    get_free_flow_speed()
