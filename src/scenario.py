"""
Class that creates the required files for SUMO simulator in order to run simulation in this experiment.
"""

import os
import random
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import numpy as np

from config.constants import config_constants
from config.simulation import config_simulation
from paths import (
    MAP_FILE,
    NET_FILE,
    ROUTE_FILE,
    SUMO_CONF,
    TRIP_FILE,
    TRIPSINFO_OUTPUT_FILE,
    UNDESIRED_ROUTE_FILE,
    VTYPE_FILE,
)


class scenario:
    def __init__(self, map, n_agents):
        """
        Parameters:
        map: network file or .osm file
        n_agents: number of agents
        """
        self.n_agents = n_agents
        # List that store agents (each agent a dictionary with keys id, origin, destination)
        self.agents = []
        # Dictionary that stores set of routes for each OD-pair
        self.od_routes = {}  # (origin, dest) → routes

        """
        Convert map if needed
        If you give an OpenStreetMap file .osm, it converts it to SUMO format using netconvert
        Otherwise, it assumes it's already a SUMO network
        """
        if map.suffix == ".osm":
            self.network = self.convert_map(map)
        else:
            self.network = map

        """
        Automatically
        1. Creates agents  
        2. Generate routes sets per OD
        3. Creates a config file
        """
        self.generate_agents()
        self.generate_routes()
        self.conf = self.gen_conf()

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
            NET_FILE,
        ]

        # Runs the command in the OS shell
        subprocess.run(cmd, check=True)

        return NET_FILE

    def generate_agents(self):
        for i in range(self.n_agents):
            origin, dest = self.sample_od()
            self.agents.append(
                {"id": f"agent_{i+1}", "origin": origin, "destination": dest}
            )

    def generate_routes(self):

        unique_ods = self.get_unique_ods()

        # 1. Compute routes per OD
        for od in unique_ods:
            # Store in the dictionary od_routes the set of routes for this od pair.
            self.od_routes[od] = self.compute_k_routes(od)

    def get_unique_ods(self):
        # Extract unique OD pairs
        # (agent["origin"], agent["destination"]) for agent in self.agents: List comprenhensions, returns a list
        # set(): Constructs a set from a list
        return set((agent["origin"], agent["destination"]) for agent in self.agents)

    def sample_od(self):
        """
        In the future I will implement more than one OD-pair.
        For simplicity, and to start, all the agents start from the same OD-pair
        """
        fixed_od = (config_simulation.start_edge, config_simulation.end_edge)
        return fixed_od

    def compute_k_routes(self, od, k=3, n_samples=10, random_factor=10):
        # Weights of edges by default are free-flow travel times
        # --weights.random-factor: Edge weights for routing are dynamically disturbed by a random factor drawn uniformly from

        routes = []

        with tempfile.TemporaryDirectory() as tmpdir:
            trips_file = os.path.join(tmpdir, "trips.xml")
            routes_file = os.path.join(tmpdir, "routes.xml")

            # 1. Create trips.xml
            self.__write_trip(trips_file, od)

            # 2. Compute best route according shortest-path
            best_route = self._run_duarouter(
                trips_file, routes_file, random_factor=1.0, seed=42
            )

            if best_route:
                routes.append(best_route)

            # 3. Sample alternative routes (applying random factor to edge costs)
            for _ in range(n_samples):

                route = self._run_duarouter(
                    trips_file,
                    routes_file,
                    random_factor=random_factor,
                    # So each time we call duarouter, assigns different random factor to each edge
                    seed=random.randint(0, 100000),
                )

                if route and route not in routes:
                    routes.append(route)

                # Early stop
                if len(routes) == k:
                    break

        if not routes:
            return []

        # 3. Return k routes
        return routes

    def _run_duarouter(self, trips_file, routes_file, random_factor, seed):
        cmd = [
            "duarouter",
            "-n",
            MAP_FILE,
            "--route-files",
            trips_file,
            "-o",
            routes_file,
            "--routing-algorithm",
            "astar",
            "--weights.random-factor",
            str(random_factor),
            "--seed",
            str(seed),
        ]

        subprocess.run(cmd, check=True)

        return self.__parse_route(routes_file)

    def __write_trip(self, file_path, od):
        origin, destination = od
        with open(file_path, "w") as f:
            f.write(
                f"""<routes>
    <trip id="t0" from="{origin}" to="{destination}" depart="0"/>
</routes>
                    """
            )

    def __parse_route(self, routes_file):
        try:
            tree = ET.parse(routes_file)
            root = tree.getroot()

            vehicle = root.find("vehicle")
            route = vehicle.find("route")
            if route is not None:
                edges = route.attrib["edges"].split()
                return edges

        except Exception:
            return None

        return None

    def gen_conf(self):
        """
        Create SUMO Config file
        """
        with open(SUMO_CONF, "w+") as conf:
            conf.write('<?xml version="1.0"?>\n')
            conf.write("<configuration>\n")
            conf.write("\t<input>\n")
            conf.write(f'\t\t<net-file value="{self.network}"/>\n')
            conf.write("\t</input>\n")
            conf.write(f"\t<report>\n")
            conf.write(f'\t\t<tripinfo-output value="{TRIPSINFO_OUTPUT_FILE}"/>\n')
            conf.write(f"\t</report>\n")
            conf.write("</configuration>\n")

        return SUMO_CONF
