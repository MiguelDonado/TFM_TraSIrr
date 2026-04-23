import subprocess

from config.config import config
from paths import (
    NET,
    ROUTES_DEMAND_CALIBRATION,
    SUMMARY,
    SUMO_CONF_DEMAND_CALIBRATION,
    TRIPS_DEMAND_CALIBRATION,
)

n_agents = 50


class DemandCalibration:
    def __init__(self, map):
        self.ensure_network(map)
        self.generate_trips()
        self.conf = self.generate_conf()
        self.run_episode()

    def ensure_network(self, map):
        """
        Convert map if needed
        If you give an OpenStreetMap file .osm, it converts it to SUMO format using netconvert
        Otherwise, it assumes it's already a SUMO network
        """
        if map.suffix == ".osm":
            self.network = self.convert_map(map)
        else:
            self.network = map

    def convert_map(self, map):
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

    def generate_trips(self):
        cmd = [
            "randomTrips.py",
            "-n",
            self.network,
            "-b",
            str(config.start_time),
            "-e",
            str(config.end_time),
            "-p",
            str(((config.end_time - config.start_time) / n_agents)),
            "--fringe-factor",
            str(config.fringe_factor),
            "--min-distance",
            "100",
            "--seed",
            str(config.seed),
            "--validate",
            "-o",
            TRIPS_DEMAND_CALIBRATION,
            "--route-file",
            ROUTES_DEMAND_CALIBRATION,
        ]

        subprocess.run(cmd, check=True)

    def generate_conf(self):
        """
        Create SUMO Config file
        """
        with open(SUMO_CONF_DEMAND_CALIBRATION, "w+") as conf:
            conf.write('<?xml version="1.0"?>\n')
            conf.write("<configuration>\n")
            conf.write("\t<input>\n")
            conf.write(f'\t\t<net-file value="{self.network}"/>\n')
            conf.write(f'\t\t<route-files value="{ROUTES_DEMAND_CALIBRATION}"/>\n')
            conf.write("\t</input>\n")
            conf.write(f"\t<report>\n")
            conf.write(f'\t\t<summary-output value="{SUMMARY}"/>\n')
            conf.write(f"\t</report>\n")
            conf.write(f"\t<random>\n")
            conf.write(f"\t\t<seed value='42'/>\n")
            conf.write(f"\t</random>\n")
            conf.write("</configuration>\n")
        return SUMO_CONF_DEMAND_CALIBRATION

    def run_episode(self):
        cmd = ["sumo", "-c", self.conf]
        subprocess.run(cmd)
