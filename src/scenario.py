"""
Class that creates the required files for SUMO simulator in order to run simulation in this experiment.
"""

import os
import random
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np
import pandas as pd
from lxml import etree

from config.config import RunMode, config
from paths import (
    AGENTS_OD,
    FCD,
    MAP,
    NET,
    OD_MATRIX,
    OD_ROUTES,
    STATISTICS,
    SUMMARY,
    SUMO_CONF,
    TRIPS_INFO,
    UNDESIRED_ROUTE_FILE,
    VEHROUTE,
)


class Scenario:
    def __init__(self, map, n_agents_warmup, n_agents_post_warmup, seeds, rng):
        """
        Parameters:
        map: network file or .osm file
        n_agents: number of agents
        """
        self.n_agents_warmup = n_agents_warmup
        self.n_agents_post_warmup = n_agents_post_warmup
        self.n_agents = n_agents_warmup + n_agents_post_warmup
        self.network = map

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
        self.network = map
        self.generate_agents(rng)
        self.ensure_routes(seeds)
        self.save_scenario_data()
        self.conf = self.generate_conf()

    def generate_agents(self, rng):
        # Generate the random edge OD-matrix (origin,destination for the agents)
        od_s = self.generate_od_for_agents()
        departure_times = self.generate_departure_times(rng)
        self.write_od_matrix(
            od_s, departure_times, interval_size=config.interval_od_matrix
        )
        for i in range(self.n_agents):
            origin, dest = od_s[i]
            departure_time = departure_times[i]
            self.agents.append(
                {
                    "id": f"agent_{i+1}",
                    "origin": origin,
                    "destination": dest,
                    "departure_time": departure_time,
                }
            )

    def ensure_routes(self, seeds):
        if config.have_precomputed_routes:
            self.reconstruct_od_routes()
        else:
            self.generate_routes(seeds)

    def generate_routes(self, seeds):
        # 1. Compute routes per OD
        for od in self.unique_ods:
            # Store in the dictionary od_routes the set of routes for this od pair.
            self.od_routes[od] = self.compute_k_routes(od, seeds)

        UNDESIRED_ROUTE_FILE.unlink()

    def reconstruct_od_routes(self):
        df = pd.read_parquet(OD_ROUTES)

        df = df.sort_values(["origin", "dest", "route_id", "step"])

        od_routes = {}

        grouped = df.groupby(["origin", "dest", "route_id"])

        for (origin, dest, route_id), group in grouped:
            route = group["edge"].tolist()

            key = (origin, dest)
            if key not in od_routes:
                od_routes[key] = []
            od_routes[key].append(route)

        self.od_routes = od_routes

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
            conf.write(f'\t\t<summary-output value="{SUMMARY}"/>\n')
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

        # Check RunMode
        if config.mode == RunMode.COMPUTE_ROUTES:
            print(f"\nThe OD pairs and its k routes have been saved in {OD_ROUTES}")
            sys.exit()

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

    def generate_od_for_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trips_file = os.path.join(tmpdir, "trips.xml")
            # Generate random ods for agents
            self.generate_random_trips_agents(trips_file)
            # OD space
            od_space = self.parse_od_agents(trips_file)
            # Restricted/bounded OD space
            restricted_od_space_counter = self.restrict_od_space(
                od_space, config.max_size_od_space
            )
            # Sample ods for all the agents from the restricted OD space
            od_s = self.sample_od_space(
                restricted_od_space_counter, self.n_agents, config.max_size_od_space
            )
        return od_s

    def generate_random_trips_agents(self, output_file):
        cmd = [
            "randomTrips.py",
            "-n",
            MAP,
            "-b",
            str(0),
            "-e",
            str(config.end_time),
            "-p",
            str(((config.end_time - 0) / (self.n_agents_post_warmup))),
            "--fringe-factor",
            str(config.fringe_factor),
            "--min-distance",
            str(config.min_distance),
            "--seed",
            str(config.seed),
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

    def restrict_od_space(self, od_list, k):
        """
        Make sure to restrict/bound the OD pool to <= k unique ODs
        """
        counter = Counter(od_list)

        # Limit pool to k ODs (e.g., most frequent)
        # .most_common() returns [(('A','B'), 3), (('C','D'), 2)]
        most_common = counter.most_common(k)
        return most_common

    def sample_od_space(self, od_space_counter, n_agents, k):
        """
        Sample from a OD space counter object. That is [((A,B),3),((A,C),2)]
        It will receive the reduced OD space counter object
        """

        unique_ods = [od for od, _ in od_space_counter]
        self.unique_ods = unique_ods
        counts = [count for _, count in od_space_counter]

        # Step 2: Probabilities within reduced pool
        total = sum(counts)
        probs = [c / total for c in counts]

        # Step 3: sample MANY agents from FEW ODs
        ods = random.choices(
            unique_ods,
            weights=probs,
            k=n_agents,
        )
        return ods

    def generate_departure_times(self, rng):
        departure_times = rng.integers(
            0,
            config.end_time,
            size=self.n_agents,
        )

        departure_times = [int(departure_time) for departure_time in departure_times]
        # Sort departure times, to avoid problems in SUMO simulation and for clarity. The agent_1 should be the first to departure, the agent_2 the second...
        departure_times.sort()
        return departure_times

    def write_od_matrix(self, od_list, departure_times_list, interval_size):

        # Build df
        df = pd.DataFrame(
            [(o, d, t) for (o, d), t in zip(od_list, departure_times_list)],
            columns=["origin", "destination", "departure_time"],
        )

        # Assign interval index
        df["interval"] = (df["departure_time"] // interval_size).astype(int)

        # Group and count
        """
        interval	origin	destination	    count
        0	          A	          B	          5
        """
        grouped = (
            df.groupby(["interval", "origin", "destination"])
            .size()  # Counts how many rows on each group
            .reset_index(name="count")  # Resets index and creates column count
        )

        # Generate one OD matrix per interval
        for interval, subdf in grouped.groupby("interval"):
            matrix = (
                # Transforms into contingency table format
                subdf.pivot(index="origin", columns="destination", values="count")
                .fillna(0)
                .astype(int)
            )
            start = interval * interval_size
            end = (interval + 1) * interval_size
            matrix.to_csv(f"{OD_MATRIX}_{start}_{end}.csv")

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
            "--routing-threads",
            str(config.n_threads),
            "--routing-algorithm",
            config.routing_algorithm,
            # Just in case, even though it seems that this option --max-alternatives does not work (does not compute more than one route)
            "--max-alternatives",
            "1",
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
            f.write(f"""<routes>
    <trip id="t0" from="{origin}" to="{destination}" depart="0"/>
</routes>
                    """)

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
