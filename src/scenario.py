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
    EDGEDATA_XML,
    FCD_XML,
    FREE_FLOW_TRAVEL_TIMES,
    MAP,
    MEANDATA,
    NET,
    OD_MATRIX_INTERVALS,
    OD_MATRIX_TOTAL,
    OD_ROUTES,
    STATISTICS_XML,
    SUMMARY_XML,
    SUMO_CONF,
    TRIPS_INFO_XML,
    UNDESIRED_ROUTE_FILE,
    VEHROUTE_XML,
)
from utils.od_routes import od_routes_to_rows
from utils.sumo_xml import write_meandata_file, write_sumo_conf


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
        self._generate_agents(rng)
        self._load_or_compute_routes(seeds)
        self._save_scenario_data()
        self.conf = self._generate_conf()

    def _generate_agents(self, rng):
        # Generate the random edge OD-matrix (origin,destination for the agents)
        self.od_pairs = self._generate_od_for_agents()
        self.departure_times = self._generate_departure_times(rng)
        for i in range(self.n_agents):
            origin, dest = self.od_pairs[i]
            departure_time = self.departure_times[i]
            self.agents.append(
                {
                    "id": f"agent_{i+1}",
                    "origin": origin,
                    "destination": dest,
                    "departure_time": departure_time,
                }
            )

    def _load_or_compute_routes(self, seeds):
        if config.have_precomputed_routes:
            self.reconstruct_od_routes()
        else:
            self.od_routes = self.compute_k_routes(seeds)

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

    def compute_k_routes(
        self,
        seeds,
        k=config.n_routes_per_OD,
        max_attempts=config.max_attempts,
        random_factor=config.random_factor,
    ):
        # Weights of edges by default are free-flow travel times
        # --weights.random-factor: Edge weights for routing are dynamically disturbed by a random factor drawn uniformly from

        routes_per_od = None

        with tempfile.TemporaryDirectory() as tmpdir:
            trips_file = os.path.join(tmpdir, "trips.xml")
            routes_file = os.path.join(tmpdir, "routes.xml")

            # 1. Create trips.xml
            self._write_trip(trips_file)

            # 2. Compute best route according shortest-path
            best_routes = self._run_duarouter(
                trips_file, routes_file, random_factor=1.0, seed=config.seed
            )

            if not best_routes:
                return []

            # Initialize structure: one list per OD
            routes_per_od = [[r] for r in best_routes]

            # 3. Generate alternative routes
            for seed in seeds:
                # Early stop
                if all(len(rlist) >= k for rlist in routes_per_od):
                    break

                new_routes = self._run_duarouter(
                    trips_file,
                    routes_file,
                    random_factor=random_factor,
                    seed=seed,  # So each time we call duarouter, assigns different random factor to each edge
                )

                if not new_routes:
                    continue

                for i, route in enumerate(new_routes):
                    # Avoid duplicates per OD
                    if route not in routes_per_od[i]:
                        if len(routes_per_od[i]) < k:
                            routes_per_od[i].append(route)

        # 4. Delete undesired file
        UNDESIRED_ROUTE_FILE.unlink()

        od_routes = dict(zip(self.unique_ods, routes_per_od))
        # 5. Return k routes
        return od_routes

    def _generate_conf(self):
        """
        Create SUMO Config file
        """
        # Generate meandata file used for generation of edgedata output
        self._generate_meandata_file()

        write_sumo_conf(
            output_path=SUMO_CONF,
            net_file=self.network,
            additional_files=MEANDATA,
            report_outputs={
                "tripinfo-output": TRIPS_INFO_XML,
                "statistic-output": STATISTICS_XML,
                "summary-output": STATISTICS_XML,
                "vehroute-output": VEHROUTE_XML,
                "vehroute-output.exit-times": "true",
                "fcd-output": FCD_XML,
                "fcd-output.attributes": "x,y",
            },
            device_outputs={"device.fcd.probability": "0.2"},
        )
        return SUMO_CONF

    def _generate_meandata_file(self):
        write_meandata_file(MEANDATA, EDGEDATA_XML, config.time_interval)

    def _save_scenario_data(self):
        self._save_od_routes()

        self._generate_free_flow_tt_links()

        self._set_time_interval()

        self._add_time_intervals_to_agents()

        self._save_agents()

        self._write_od_matrix(
            self.od_pairs, self.departure_times, interval_size=config.time_interval
        )

        self._handle_compute_routes_mode()

    def _process_od_routes(self):
        """
        I want this format
        origin | dest | route_id | step | edge
        A         B      1          1       e1
        A         B      1          2       e5 ...
        """
        return od_routes_to_rows(self.od_routes)

    ########################
    ### HELPER FUNCTIONS ###
    ########################

    def _generate_od_for_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trips_file = os.path.join(tmpdir, "trips.xml")
            # Generate random ods for agents
            self._generate_random_trips_agents(trips_file)
            # OD space
            od_space = self._parse_od_agents(trips_file)
            # Restricted/bounded OD space
            restricted_od_space_counter = self._restrict_od_space(
                od_space, config.max_size_od_space
            )
            # Sample ods for all the agents from the restricted OD space
            od_pairs = self._sample_od_space(
                restricted_od_space_counter, self.n_agents, config.max_size_od_space
            )
        return od_pairs

    def _generate_random_trips_agents(self, output_file):
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

    def _parse_od_agents(self, trips_file):
        tree = etree.parse(trips_file)
        origins = tree.xpath("//trip/@from")
        destinations = tree.xpath("//trip/@to")
        od_pairs = list(zip(origins, destinations))
        return od_pairs

    def _restrict_od_space(self, od_list, k):
        """
        Make sure to restrict/bound the OD pool to <= k unique ODs
        """
        counter = Counter(od_list)

        # Limit pool to k ODs (e.g., most frequent)
        # .most_common() returns [(('A','B'), 3), (('C','D'), 2)]
        most_common = counter.most_common(k)
        return most_common

    def _sample_od_space(self, od_space_counter, n_agents, k):
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

    def _generate_departure_times(self, rng):
        departure_times = rng.integers(
            0,
            config.end_time,
            size=self.n_agents,
        )

        departure_times = [int(departure_time) for departure_time in departure_times]
        # Sort departure times, to avoid problems in SUMO simulation and for clarity. The agent_1 should be the first to departure, the agent_2 the second...
        departure_times.sort()
        return departure_times

    def _write_od_matrix(self, od_list, departure_times_list, interval_size):

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

        # Save all intervals in one file
        grouped.to_csv(OD_MATRIX_INTERVALS, index=False)

        # Optional: total OD matrix (without intervals)
        counts = Counter(od_list)

        total_df = pd.DataFrame(
            [(o, d, c) for (o, d), c in counts.items()],
            columns=["origin", "destination", "count"],
        )

        total_df.to_csv(OD_MATRIX_TOTAL, index=False)

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

        return self._parse_route(routes_file)

    def _write_trip(self, file_path):
        with open(file_path, "w") as f:
            f.write(f"<routes>\n")
            for i, (origin, destination) in enumerate(self.unique_ods):
                f.write(
                    f"""\t<trip id="t{i}" from="{origin}" to="{destination}" depart="0"/>\n"""
                )
            f.write("</routes>\n")

    def _parse_route(self, routes_file):
        try:
            document = routes_file
            tree = etree.parse(document)

            # Routes
            routes = tree.xpath("//route/@edges")
            edges = [route.split(" ") for route in routes]
            return edges

        except Exception:
            return None

    def _compute_median_free_flow_travel_time(self):
        edge_costs = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)
        edge_costs = edge_costs.set_index("edge")["free_flow_travel_time"].to_dict()

        path_costs = []
        for od, od_paths in self.od_routes.items():

            for path in od_paths:
                total_cost = sum(edge_costs[e] for e in path)
                path_costs.append(total_cost)

        median_free_flow_tt = float(np.median(path_costs))
        return median_free_flow_tt

    def _generate_free_flow_tt_links(self):
        """
        Called once per program execution
        Used for imputing missing values link costs table
        """
        data = []

        tree = etree.parse(config.network)
        edges = tree.xpath("//edge[not(@function='internal')]")
        for edge in edges:
            edge_id = edge.get("id")

            lane = edge.find("lane")

            free_flow_speed = float(lane.get("speed"))
            length = float(lane.get("length"))

            free_flow_travel_time = length / free_flow_speed
            data.append(
                {"edge": edge_id, "free_flow_travel_time": free_flow_travel_time}
            )

        df = pd.DataFrame(data)
        df.to_parquet(FREE_FLOW_TRAVEL_TIMES, engine="pyarrow", index=False)

    def _save_od_routes(self):
        processed_od_routes = self._process_od_routes()
        df = pd.DataFrame(processed_od_routes)
        df.to_parquet(OD_ROUTES, engine="pyarrow")

    def _set_time_interval(self):
        # SET TIME INTERVAL USED THROUGHOUT THE PROGRAM (AUTOMATICALLY ADAPTED TO EACH NETWORK)
        config.time_interval = int(
            self._compute_median_free_flow_travel_time()
            * config.time_interval_heuristic
        )

    def _add_time_intervals_to_agents(self):
        # // represents integer division
        for agent in self.agents:
            agent["time_interval"] = agent["departure_time"] // config.time_interval

    def _save_agents(self):
        df = pd.DataFrame(self.agents)
        df.to_parquet(AGENTS_OD, engine="pyarrow")

    def _handle_compute_routes_mode(self):
        # Check RunMode
        if config.mode == RunMode.COMPUTE_ROUTES:
            print(f"\nThe OD pairs and its k routes have been saved in {OD_ROUTES}")
            sys.exit()
