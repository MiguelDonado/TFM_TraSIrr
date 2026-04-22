import subprocess

NET = "/home/miguel/6.Projects/Thesis/src/scripts/net.net.xml"
MAP = "/home/miguel/6.Projects/Thesis/src/scripts/map.osm"


def convert_map(map):
    """
    Converts OSM to SUMO
    It uses netconvert tool with some options
    It outputs a .net.xml file

    It has some extra options, in order to try to make the conversion as good as possible
    """

    cmd = [
        "netconvert",
        "--osm",
        map,
        "--geometry.remove",
        "--geometry.min-dist",
        "1.0",
        "--geometry.avoid-overlap",
        "--ramps.guess",
        "--roundabouts.guess",
        "--junctions.join",
        "--junctions.join-dist",
        "15",
        "--junctions.corner-detail",
        "10",
        "--junctions.internal-link-detail",
        "10",
        "--osm.turn-lanes",
        "--tls.guess",
        "--tls.guess-signals",
        "--tls.join",
        "-o",
        NET,
    ]

    # Runs the command in the OS shell
    subprocess.run(cmd, check=True)

    return NET


convert_map(MAP)
