"""
Purpose of this script: parse xml network file to get the characteristics
of the network (nodes, links, turns)
"""

import numpy as np
from lxml import etree

rng = np.random.default_rng(42)

# City speed bounds
POSSIBLE_SPEEDS = [5.56, 8.33, 13.89, 16.67]  # 20, 30, 50, 60
WEIGHTS = [0.1, 0.4, 0.4, 0.1]

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Koh/FirstNetwork_Koh.net.xml"


def change_lanes_speed(net=NETWORK_PATH):
    """
    It should not modify the internal edges.
    Those are:
        junction connectors
        turning movements
        inside intersections

    If you change their speed:

    you distort intersection behavior
    turning speeds become unrealistic
    traffic lights / yielding logic breaks
    """

    ###########
    # SCRIPT
    ###########

    # Lanes
    lanes = 0

    document = net
    tree = etree.parse(document)

    # Lanes
    lanes_elements = tree.xpath("//edge[not(@function='internal')]/lane")
    for lane_element in lanes_elements:
        speed = float(rng.choice(POSSIBLE_SPEEDS, p=WEIGHTS))
        lane_element.attrib["speed"] = str(speed)

    tree.write(NETWORK_PATH, pretty_print=True, encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    change_lanes_speed()
