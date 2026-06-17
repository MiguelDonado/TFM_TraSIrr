"""
Purpose of this script: parse xml network file to get the characteristics
of the network (nodes, links, turns)
"""

import numpy as np
from lxml import etree

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Koh/1st_koh_v2.net.xml"


def get_edges_lengths_script(net=NETWORK_PATH):
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
        "/home/miguel/6.Projects/Thesis/src/scripts/output/1st_koh_v2.net.csv",
        data,
        delimiter=",",
        fmt="%.2f",
    )
    mean_length = round(float(np.mean(data)), 2)
    print(mean_length)
    return mean_length


if __name__ == "__main__":
    get_edges_lengths_script()
