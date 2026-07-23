"""
Builds and owns the static environment shared across all training episodes.

Scenario is constructed once before the training loop and exposes two
data structures consumed every episode:
  self.agents    — list of dicts {id, origin, destination, departure_time}
  self.od_routes — {(origin, dest): [[edge, …], …]} with k route alternatives

Agents and unique_ods are generated externally (via utils.generate_agents)
and passed in.

Construction runs three steps automatically in __init__:
1. Routes       — compute k alternative routes per OD by calling duarouter
                  repeatedly with a random edge-weight perturbation; or load
                  from a precomputed parquet if have_precomputed_routes=True.
2. Environment  — save agents, OD routes, free-flow link costs, OD matrix,
                  and time interval table to parquet files under data/.
3. Config       — write the SUMO .sumocfg and meandata XML files used by
                  Environment.run_episode() every episode.
                  The meandata XML instructs SUMO to collect per-edge
                  density and flow, aggregated over fixed time intervals,
                  into the edgedata output file.
"""

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np
import pandas as pd
from lxml import etree

from config.config import RunMode, config
from config.paths import (
    AGENTS_OD,
    EDGEDATA_XML,
    FCD_XML,
    MEANDATA,
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
from utils.od_routes import od_routes_to_rows, parse_route
from utils.sumo_xml import write_meandata_file, write_sumo_conf


class Scenario:
    def __init__(
        self,
        map,
        agents,
        unique_ods,
        seeds,
        seed=None,
        k=None,
        random_factor=None,
        max_attempts=None,
    ):
        """
        Parameters:
        map: network file or .osm file
        agents: list of {id, origin, destination, departure_time} from demand calibration
        unique_ods: list of unique (origin, dest) pairs in the OD pool
        """
        self.network = map
        self.agents = agents
        self.unique_ods = unique_ods
        self.seed = seed if seed is not None else config.seed

        # Dictionary that stores set of routes for each OD-pair
        self.od_routes = {}  # (origin, dest) → routes

        # Manage default arguments
        k = k if k is not None else config.n_routes_per_OD
        # Weights of edges by default are free-flow travel times
        # --weights.random-factor: Edge weights for routing are dynamically disturbed by a random factor drawn uniformly from
        random_factor = (
            random_factor if random_factor is not None else config.random_factor
        )
        max_attempts = max_attempts if max_attempts is not None else config.max_attempts

        self._load_or_compute_routes(
            seeds=seeds, k=k, random_factor=random_factor, max_attempts=max_attempts
        )
        self._save_scenario_data()
        self.conf = self._generate_conf()

    def _load_or_compute_routes(self, seeds, k, random_factor, max_attempts):
        if config.have_precomputed_routes:
            self.reconstruct_od_routes()
        else:
            self.od_routes = self.compute_k_routes(
                seeds, k=k, random_factor=random_factor
            )

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
        k,
        random_factor,
    ):

        with tempfile.TemporaryDirectory() as tmpdir:
            trips_file = os.path.join(tmpdir, "trips.xml")
            routes_file = os.path.join(tmpdir, "routes.xml")

            # 1. Create trips.xml
            self._write_trip(trips_file)

            # 2. Compute best route according shortest-path
            best_routes = self._run_duarouter(
                trips_file, routes_file, random_factor=1.0
            )

            if not best_routes:
                return {}

            # Initialize structure: one list per OD
            routes_per_od = [[r] for r in best_routes]

            # 3. Generate alternative routes
            self._fill_alternative_routes(
                routes_per_od, trips_file, routes_file, seeds, k, random_factor
            )

            # 4. Delete undesired file
            UNDESIRED_ROUTE_FILE.unlink(missing_ok=True)

            od_routes = dict(zip(self.unique_ods, routes_per_od))
            # 5. Return k routes
            return od_routes

    def _fill_alternative_routes(
        self, routes_per_od, trips_file, routes_file, seeds, k, random_factor
    ):
        """
        Does not need to return anything because it is already modifying the
        routes_per_od object passed by reference
        """
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
                if route not in routes_per_od[i] and len(routes_per_od[i]) < k:
                    routes_per_od[i].append(route)

    def _generate_conf(self):
        """
        Create SUMO Config file
        """
        # Generate meandata file used for generation of edgedata output
        self._generate_meandata_file()

        write_sumo_conf(
            output_path=SUMO_CONF,
            net_file=self.network,
            seed=self.seed,
            additional_files=MEANDATA,
            report_outputs={
                "tripinfo-output": TRIPS_INFO_XML,
                "statistic-output": STATISTICS_XML,
                "summary-output": SUMMARY_XML,
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

        self._save_agents()

        od_pairs = [(a["origin"], a["destination"]) for a in self.agents]
        departure_times = [a["departure_time"] for a in self.agents]
        self._write_od_matrix(
            od_pairs, departure_times, interval_size=config.time_interval
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

    def _write_od_matrix(self, od_list, departure_times_list, interval_size):

        df = pd.DataFrame(
            [(o, d, t) for (o, d), t in zip(od_list, departure_times_list)],
            columns=["origin", "destination", "departure_time"],
        )

        df["interval"] = (df["departure_time"] // interval_size).astype(int)

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

    def _run_duarouter(self, trips_file, routes_file, random_factor, seed=None):

        cmd = [
            "duarouter",
            "-n",
            config.network,
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
            str(self.seed),
        ]

        subprocess.run(cmd, check=True)

        return parse_route(routes_file)

    def _write_trip(self, file_path):
        with open(file_path, "w") as f:
            f.write(f"<routes>\n")
            for i, (origin, destination) in enumerate(self.unique_ods):
                f.write(
                    f"""\t<trip id="t{i}" from="{origin}" to="{destination}" depart="0"/>\n"""
                )
            f.write("</routes>\n")

    def _save_od_routes(self):
        processed_od_routes = self._process_od_routes()
        df = pd.DataFrame(processed_od_routes)
        df.to_parquet(OD_ROUTES, engine="pyarrow")

    def _save_agents(self):
        df = pd.DataFrame(self.agents)
        df.to_parquet(AGENTS_OD, engine="pyarrow")

    def _handle_compute_routes_mode(self):
        # Check RunMode
        if config.mode == RunMode.COMPUTE_ROUTES:
            print(f"\nThe OD pairs and its k routes have been saved in {OD_ROUTES}")
            sys.exit()
