"""
One-off tool to convert an OSM file into a SUMO network (.net.xml) via netconvert.

Flags applied during conversion
--------------------------------
Geometry   --geometry.remove, --geometry.min-dist, --geometry.avoid-overlap
               Simplify redundant shape points and fix overlapping geometry.
Junctions  --junctions.join, --junctions.join-dist 10
               Merge closely-spaced junctions (within 10 m) into one,
               which reduces unrealistic micro-junctions from OSM data.
Roads      --ramps.guess, --roundabouts.guess, --osm.turn-lanes
               Infer highway ramps, roundabout structure, and turn lanes
               from OSM tags where they are not explicitly defined.
Traffic lights  --tls.discard-simple, --tls.discard-loaded
               Remove all traffic lights — the experiment uses uncontrolled
               intersections (yield/priority rules only).

Post-conversion
---------------
Manual edits in netedit are still required after running this tool.
OSM data is noisy; automated conversion cannot resolve all artefacts
(disconnected edges, misclassified road types).
"""

import subprocess

# ARGUMENT PASSED TO THE FUNCTION
NETCONVERT_NET_FOLDER = (
    "/home/miguel/6.Projects/Thesis/sumo/net/Manual/netconvert_network/"
)


def convert_map(dir_path):
    MAP = input("Enter the absolute path of the OSM file: ")
    NET = input("Enter the filename you wanna give to the NETEDIT network: ")
    NET = dir_path + NET + ".net.xml"

    """
    Converts OSM to SUMO
    It uses netconvert tool with some options
    It outputs a .net.xml file

    It has some extra options, in order to try to make the conversion as good as possible
    """

    cmd = [
        "netconvert",
        "--osm",
        MAP,
        # Geometry cleanup
        "--geometry.remove",
        "--geometry.min-dist",
        "1.0",
        "--geometry.avoid-overlap",
        # Network structure
        "--junctions.join",
        "--junctions.join-dist",
        "10",
        # Road features
        "--ramps.guess",
        "--roundabouts.guess",
        "--osm.turn-lanes",
        # REMOVE traffic lights
        "--tls.discard-simple",
        "--tls.discard-loaded",
        # Simplify
        "--no-internal-links",
        "-o",
        NET,
    ]

    # Runs the command in the OS shell
    subprocess.run(cmd, check=True)

    return NET


convert_map()
