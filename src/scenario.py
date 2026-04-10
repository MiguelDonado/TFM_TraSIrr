"""
Class that creates the required files for SUMO simulator in order to run simulation in this experiment.
"""

import os
import random
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter

import pandas as pd
from lxml import etree

from config.config import config
from paths import (
    AGENTS_OD,
    FCD,
    MAP,
    NET,
    OD_MATRIX,
    OD_ROUTES,
    STATISTICS,
    SUMO_CONF,
    TRIPS_INFO,
    UNDESIRED_ROUTE_FILE,
    VEHROUTE,
)


class Scenario:
    def __init__(self, map, n_agents, seeds):
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
        Automatically
        1. Creates agents  
        2. Generate routes sets per OD
        3. Creates a config file
        """
        self.ensure_network(map)
        self.generate_agents()
        self.generate_routes(seeds)
        self.save_scenario_data()
        self.conf = self.generate_conf()

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

    def generate_agents(self):
        # Generate the random edge OD-matrix (origin,destination for the agents)
        od_s = self.generate_od_for_agents()
        for i in range(self.n_agents):
            origin, dest = od_s[i]
            self.agents.append(
                {"id": f"agent_{i+1}", "origin": origin, "destination": dest}
            )

    def generate_routes(self, seeds):

        unique_ods = self.get_unique_ods()

        # 1. Compute routes per OD
        for od in unique_ods:
            # Store in the dictionary od_routes the set of routes for this od pair.
            self.od_routes[od] = self.compute_k_routes(od, seeds)

        UNDESIRED_ROUTE_FILE.unlink()

    def generate_conf(self):
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
            conf.write(f'\t\t<tripinfo-output value="{TRIPS_INFO}"/>\n')
            conf.write(f'\t\t<statistic-output value="{STATISTICS}"/>\n')
            conf.write(f'\t\t<vehroute-output value="{VEHROUTE}"/>\n')
            conf.write(f'\t\t<vehroute-output.exit-times value="true"/>\n')
            conf.write(f'\t\t<fcd-output value="{FCD}"/>\n')
            conf.write(f'\t\t<fcd-output.attributes value="x,y"/>\n')
            conf.write(f"\t</report>\n")
            conf.write(f"\t<random>\n")
            conf.write(f"\t\t<seed value='42'/>\n")
            conf.write(f"\t</random>\n")
            conf.write(f"\t<device>\n")
            conf.write(f"\t\t<device.fcd.probability value='0.2'/>\n")
            conf.write(f"\t</device>\n")
            conf.write("</configuration>\n")
        return SUMO_CONF

    def save_scenario_data(self):
        processed_od_routes = self.process_od_routes()
        mapping = {
            "agents_od": (self.agents, AGENTS_OD),
            "od_routes": (processed_od_routes, OD_ROUTES),
        }
        for _, (data, path) in mapping.items():
            df = pd.DataFrame(data)
            df.to_parquet(path, engine="pyarrow")

    def process_od_routes(self):
        """
        I want this format
        origin | dest | route_id | step | edge
        A         B      1          1       e1
        A         B      1          2       e5 ...
        """
        rows = []
        for (origin, dest), routes in self.od_routes.items():
            for route_id, route in enumerate(routes):
                for step, edge in enumerate(route):
                    rows.append(
                        {
                            "origin": origin,
                            "dest": dest,
                            "route_id": route_id,
                            "step": step,
                            "edge": edge,
                        }
                    )
        return rows

    ########################
    ### HELPER FUNCTIONS ###
    ########################

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

    def generate_od_for_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trips_file = os.path.join(tmpdir, "trips.xml")
            # Generate random ods for the agents
            self.generate_random_trips(trips_file)
            od_s = self.parse_od_agents(trips_file)
        self.write_od_matrix(od_s)
        return od_s

    def generate_random_trips(self, output_file):
        cmd = [
            "randomTrips.py",
            "-n",
            MAP,
            "-b",
            "0",
            "-e",
            str(self.n_agents),
            "-p",
            "1",
            "--fringe-factor",
            "10",
            "--min-distance",
            "100",
            "--seed",
            "42",
            "--validate",
            "-o",
            output_file,
        ]

        subprocess.run(cmd, check=True)

    def parse_od_agents(self, trips_file):
        tree = etree.parse(trips_file)
        origins = tree.xpath("//trip/@from")
        destinies = tree.xpath("//trip/@to")
        od_s = list(zip(origins, destinies))
        return od_s

    def write_od_matrix(self, od_list):
        counts = Counter(od_list)
        df = pd.DataFrame(
            [(o, d, c) for (o, d), c in counts.items()],
            columns=["origin", "destination", "count"],
        )
        matrix = (
            df.pivot(index="origin", columns="destination", values="count")
            .fillna(0)
            .astype(int)
        )
        matrix.to_csv(OD_MATRIX)

    def get_unique_ods(self):
        # Extract unique OD pairs
        # (agent["origin"], agent["destination"]) for agent in self.agents: List comprenhensions, returns a list
        # set(): Constructs a set from a list
        return set((agent["origin"], agent["destination"]) for agent in self.agents)

    def compute_k_routes(
        self,
        od,
        seeds,
        k=3,
        max_attempts=config.max_attempts,
        random_factor=config.random_factor,
    ):
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
                trips_file, routes_file, random_factor=1.0, seed=config.seed
            )

            if best_route:
                routes.append(best_route)

            # 3. Try seeds until k routes (applying random factor to edge costs)
            for seed in seeds:
                # Early stop
                if len(routes) == k:
                    break

                route = self._run_duarouter(
                    trips_file,
                    routes_file,
                    random_factor=random_factor,
                    seed=seed,  # So each time we call duarouter, assigns different random factor to each edge
                )

                if route and route not in routes:
                    routes.append(route)

        # 4. Return k routes
        return routes

    def _run_duarouter(self, trips_file, routes_file, random_factor, seed):
        cmd = [
            "duarouter",
            "-n",
            MAP,
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
