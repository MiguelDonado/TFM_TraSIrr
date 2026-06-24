"""
One-off tool to export edge lengths from a SUMO network to CSV.

Output is used to generate the edge-length histogram included in the
thesis document when describing the experimental networks.
"""

import numpy as np
from lxml import etree

from utils.network import get_edge_lengths

# ARGUMENTS PASSED TO THE FUNCTION
NETWORK_PATH = None
OUTPUT_PATH = None


def get_edges_lengths_script(net, output_path):
    ###########
    # SCRIPT
    ###########
    data = get_edge_lengths(net)
    np.savetxt(
        output_path,
        data,
        delimiter=",",
        fmt="%.2f",
    )
    return round(float(np.mean(data)), 2)


if __name__ == "__main__":
    get_edges_lengths_script()
