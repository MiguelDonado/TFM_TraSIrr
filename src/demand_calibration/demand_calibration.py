"""
Runs a single SUMO episode to measure the congestion level
produced by a given number of vehicles on the network.

The goal is to find the n_agents value that achieves a target
congestion level, defined as:

    congestion_ratio = (1/N) * Σ( T_i / T_i_free ),  i = 1..N agents

    where T_i is the actual trip duration and T_i_free the free-flow trip
    duration (shortest path under empty network conditions). A value of 1.4
    means trips take on average 40% longer than under free-flow conditions.
    The metric is dimensionless, network-size independent, and monotonically
    increasing with congestion.

    ~ [1.0,1.5)   — free flow (no congestion)
    ~ [1.5,2)   — light
    ~ [2,3)   — moderate
    > [3,+inf)     — heavy

Free-flow trip duration is obtained by running a dedicated SUMO episode
with one vehicle per unique route on an empty network, so that the measured
duration reflects actual vehicle dynamics (acceleration, deceleration at
junctions) rather than the theoretical length/max_speed estimate, which
systematically underestimates the true free-flow time and resulting in
an overestimation of the congestion metric

This class is instantiated and called repeatedly by the calibration
loop in src/demand_calibration/utils.py, which adjusts n_agents until
congestion_ratio reaches the target value.

Agents are generated externally (via utils.generate_agents) and passed
in, so calibration uses the same OD distribution as training.
"""

import subprocess

import numpy as np
from lxml import etree

from config.config import config
from config.paths import (
    ROUTES_DEMAND_CALIBRATION,
    ROUTES_FREE_FLOW,
    SUMO_CONF_DEMAND_CALIBRATION,
    SUMO_CONF_FREE_FLOW,
    TRIPS_DEMAND_CALIBRATION,
    TRIPS_INFO_FREE_FLOW,
    TRIPS_INFO_XML,
)
from utils.generate_free_flow_tt import generate_free_flow_tt_links
from utils.od_routes import parse_route
from utils.sumo_xml import write_sumo_conf


class DemandCalibration:
    def __init__(self, map, agents):
        self.network = map
        self.agents = agents

        self.od_routes = {}

        # Create table with free flow tt links (used to compute free flow shortest paths)
        generate_free_flow_tt_links()

        # 1. Compute shortest paths
        self._generate_routes()

        # 2. Get unique routes
        unique_routes = self._get_unique_routes()

        # 3. Generate od_routes data structure
        self.od_routes = self._generate_od_routes(unique_routes)

        # 4. Compute ff tt via simulation (accurate: accounts for acceleration/deceleration)
        self.od_min_paths_ff_tt = self._simulate_free_flow_tt(self.od_routes)

        # 5. Generate config file
        self._generate_conf()

    def _generate_routes(self):
        with open(TRIPS_DEMAND_CALIBRATION, "w") as f:
            f.write("<routes>\n")
            for agent in self.agents:
                f.write(
                    f'\t<trip id="{agent["id"]}" from="{agent["origin"]}"'
                    f' to="{agent["destination"]}" depart="{agent["departure_time"]}"/>\n'
                )
            f.write("</routes>\n")

        cmd = [
            "duarouter",
            "-n",
            self.network,
            "--route-files",
            str(TRIPS_DEMAND_CALIBRATION),
            "-o",
            str(ROUTES_DEMAND_CALIBRATION),
            "--routing-threads",
            str(config.n_threads),
            "--routing-algorithm",
            config.routing_algorithm,
            "--seed",
            str(config.seed),
        ]
        subprocess.run(cmd, check=True)

    def _get_unique_routes(self):
        routes = parse_route(ROUTES_DEMAND_CALIBRATION)
        return set(tuple(r) for r in routes)

    def _generate_od_routes(self, unique_routes):
        return {(r[0], r[-1]): [list(r)] for r in unique_routes}

    def _simulate_free_flow_tt(self, od_routes):
        """
        Runs a single SUMO episode with one vehicle per OD pair on an empty network
        to obtain accurate route-level free-flow travel times.

        Vehicles are spaced 200 s apart so they never interact with each other.
        Returns {(origin, destination): free_flow_travel_time}.
        """
        ods = list(od_routes.keys())

        # 1. Write routes file: one vehicle per OD, using its precomputed shortest-path route
        with open(ROUTES_FREE_FLOW, "w") as f:
            f.write("<routes>\n")
            for i, od in enumerate(ods):
                edges = " ".join(od_routes[od][0])
                f.write(f'\t<route id="ff_route_{i}" edges="{edges}"/>\n')
                f.write(
                    f'\t<vehicle id="ff_{i}" route="ff_route_{i}" depart="{i * 200}"/>\n'
                )
            f.write("</routes>\n")

        # 2. Create SUMO config
        write_sumo_conf(
            output_path=SUMO_CONF_FREE_FLOW,
            net_file=self.network,
            route_files=ROUTES_FREE_FLOW,
            report_outputs={"tripinfo-output": TRIPS_INFO_FREE_FLOW},
            seed=config.seed,
        )

        # 3. Run simulation
        subprocess.run(["sumo", "-c", str(SUMO_CONF_FREE_FLOW)], check=True)

        # 4. Parse tripinfo and map back to OD pairs
        tree = etree.parse(TRIPS_INFO_FREE_FLOW)
        durations = {
            trip.get("id"): float(trip.get("duration"))
            for trip in tree.xpath("//tripinfo")
        }

        return {od: durations[f"ff_{i}"] for i, od in enumerate(ods)}

    def _generate_conf(self):
        """
        Create SUMO Config file
        """

        write_sumo_conf(
            output_path=SUMO_CONF_DEMAND_CALIBRATION,
            net_file=self.network,
            route_files=ROUTES_DEMAND_CALIBRATION,
            report_outputs={"tripinfo-output": TRIPS_INFO_XML},
            seed=config.seed,
        )

        self.conf = SUMO_CONF_DEMAND_CALIBRATION

    def run_episode(self):
        cmd = ["sumo", "-c", self.conf]
        subprocess.run(cmd)

    def run_episode_with_gui(self):
        cmd = ["sumo-gui", "-c", self.conf]
        subprocess.run(cmd)

    def compute_congestion_metric(self):
        self.run_episode()
        durations = self._parse_trips_duration()
        per_agent_metric = [
            self._compute_agent_metric(agent, duration)
            for agent, duration in zip(self.agents, durations)
        ]

        congestion_metric_value = round(np.mean(per_agent_metric), 5)

        # Log
        print(f"Congestion metric: {congestion_metric_value}")

        return congestion_metric_value

    def _compute_agent_metric(self, agent, trip_duration):
        origin = agent["origin"]
        destination = agent["destination"]
        od = (origin, destination)

        # Free flow travel time
        trip_ff_tt = self.od_min_paths_ff_tt[od]

        return trip_duration / trip_ff_tt

    def _parse_trips_duration(self):
        tree = etree.parse(TRIPS_INFO_XML)
        durations = tree.xpath("//tripinfo/@duration")
        durations = [float(duration) for duration in durations]
        return durations
