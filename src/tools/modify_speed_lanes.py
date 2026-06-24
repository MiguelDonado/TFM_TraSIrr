"""
One-off tool to randomise lane speeds in a SUMO network file.

Each lane is assigned a speed drawn from a weighted distribution
reflecting typical urban road types:

    Speed (m/s) | km/h | Weight | Road type
    ------------|------|--------|----------
       5.56     |  20  |  0.10  | residential
       8.33     |  30  |  0.40  | local
      13.89     |  50  |  0.40  | arterial
      16.67     |  60  |  0.10  | main road

Used to introduce speed heterogeneity into networks that originally
have a uniform speed limit (e.g. Sioux Falls at 13.89 m/s), so that
free-flow travel times vary across edges.

Run once, then commit the modified .net.xml file.
Internal SUMO junction edges are left unchanged.
"""

import numpy as np
from lxml import etree

rng = np.random.default_rng(42)

# City speed bounds
POSSIBLE_SPEEDS = [5.56, 8.33, 13.89, 16.67]  # 20, 30, 50, 60
WEIGHTS = [0.1, 0.4, 0.4, 0.1]

# ARGUMENT PASSED TO THE FUNCTION
NETWORK_PATH = None


def change_lanes_speed(net):
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
    if net == None:
        print("You must pass a network as an argument to the function")

    document = net
    tree = etree.parse(document)

    # Lanes
    lanes_elements = tree.xpath("//edge[not(@function='internal')]/lane")
    for lane_element in lanes_elements:
        speed = float(rng.choice(POSSIBLE_SPEEDS, p=WEIGHTS))
        lane_element.attrib["speed"] = str(speed)

    tree.write(NETWORK_PATH, pretty_print=True, encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    change_lanes_speed(NETWORK_PATH)
