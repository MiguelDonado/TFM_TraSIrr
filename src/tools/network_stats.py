"""
One-off tool to print structural statistics of a SUMO network.

Metrics extracted
-----------------
Nodes       — junctions of type 'priority' or 'dead_end' only
              (internal junction connectors are excluded)
Edges       — real road links (edges with a @priority attribute)
Lanes       — total lane count across all non-internal edges
Connections — possible turning movements between edges
              (filtered to edges whose id starts with 'E' or '-E',
               which is the Sioux Falls naming convention)

Used in the thesis document to present the experimental network topology.
"""

from lxml import etree

# ARGUMENT PASSED TO THE FUNCTION
NETWORK_PATH = None


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
