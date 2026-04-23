"""
Purpose of this script: get total length of the network
"""

from lxml import etree

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Koh/FirstNetwork_Koh.net.xml"


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


if __name__ == "__main__":
    get_total_length_network(NETWORK_PATH)
