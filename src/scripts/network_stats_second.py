"""
Purpose of this script: parse xml network file to get the characteristics
of the network (nodes, links, turns)
"""

import numpy as np
from lxml import etree

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Popular/Sioux_Falls.net.xml"


def get_network_characteristics(net=NETWORK_PATH):
    ###########
    # SCRIPT
    ###########

    document = net
    tree = etree.parse(document)

    # Edges
    edges_length = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    edges_length = [float(edge_length) for edge_length in edges_length]

    data = np.array(edges_length)
    np.savetxt(
        "/home/miguel/6.Projects/Thesis/src/scripts/output/Sioux_Falls.net.csv",
        data,
        delimiter=",",
        fmt="%.2f",
    )


if __name__ == "__main__":
    get_network_characteristics()
