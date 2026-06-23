"""
Purpose of this script: parse xml network file to get the characteristics
of the network (nodes, links, turns)
"""

import numpy as np
from lxml import etree

from utils.network import get_edge_lengths

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Koh/1st_koh_v2.net.xml"


def get_edges_lengths_script(net=NETWORK_PATH):
    ###########
    # SCRIPT
    ###########
    data = get_edge_lengths(net)
    np.savetxt(
        "/home/miguel/6.Projects/Thesis/src/scripts/output/1st_koh_v2.net.csv",
        data,
        delimiter=",",
        fmt="%.2f",
    )
    return round(float(np.mean(data)), 2)


if __name__ == "__main__":
    get_edges_lengths_script()
