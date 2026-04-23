import subprocess

NETCONVERT_NET_FOLDER = (
    "/home/miguel/6.Projects/Thesis/sumo/net/Manual/netconvert_network/"
)


def convert_map():
    MAP = input("Enter the absolute path of the OSM file: ")
    NET = input("Enter the filename you wanna give to the NETEDIT network: ")
    NET = NETCONVERT_NET_FOLDER + NET + ".net.xml"

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
