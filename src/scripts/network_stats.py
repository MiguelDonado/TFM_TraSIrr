"""
Purpose of this script: parse xml network file to get the characteristics
of the network (nodes, links, turns)
"""

from lxml import etree

# CONSTANTS
NETWORK_PATH = "/home/miguel/6.Projects/Thesis/sumo/net/Popular/Sioux_Falls.net.xml"


def get_network_characteristics(net=NETWORK_PATH):
    ###########
    # SCRIPT
    ###########
    # Nodes = junction
    nodes = 0
    # Edges = links
    edges = 0
    # Lanes
    lanes = 0
    # Connections = turns (possible turn between edges)
    connections = 0

    document = net
    tree = etree.parse(document)

    # Junction: Only type="priority" or "dead_end".
    # We do not take into account junctions with type='internal'
    junction_elements = tree.xpath("//junction[@type='priority' or @type='dead_end']")
    nodes = len(junction_elements)

    # Edges
    edges_elements = tree.xpath("//edge[@priority]")
    edges = len(edges_elements)

    # Lanes
    lanes_elements = tree.xpath("//edge[not(@function='internal')]/lane")
    lanes = len(lanes_elements)

    # Connections
    connection_elements = tree.xpath(
        "//connection[starts-with(@from,'E') or starts-with(@from,'-E')]"
    )
    connections = len(connection_elements)

    print("\n\n###############")
    print(f"The network '{net}' has the following characteristics:")
    print("###############")
    print(f"Nodes: {nodes}")
    print(f"Edges: {edges}")
    print(f"Lanes: {lanes}")
    print(f"Connections: {connections}")
    print("\n\n")
    return lanes


if __name__ == "__main__":
    get_network_characteristics()
