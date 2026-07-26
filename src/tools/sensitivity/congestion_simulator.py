"""
Runs a single SUMO episode to measure the congestion level
produced by a given number of vehicles on the network.

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

Free-flow trip duration comes from utils.generate_free_flow_tt.compute_od_free_flow_tt,
which runs a dedicated SUMO episode with one vehicle per unique route on an
empty network, so that the measured duration reflects actual vehicle dynamics
(acceleration, deceleration at junctions) rather than the theoretical
length/max_speed estimate, which systematically underestimates the true
free-flow time and results in an overestimation of the congestion metric.

Used by the sensitivity tools under src/tools/sensitivity/ (e.g.
plot_congestion_metric.py) to measure congestion at a given demand level.
Agents are generated externally (via utils.generate_agents) and passed in.
"""

import subprocess

import numpy as np
from lxml import etree

from config.config import config
from config.paths import (
    ROUTES_CONGESTION_SIM,
    SUMO_CONF_CONGESTION_SIM,
    TRIPS_INFO_XML,
)
from utils.generate_free_flow_tt import compute_od_free_flow_tt
from utils.sumo_xml import write_sumo_conf


class CongestionSimulator:
    def __init__(self, map, agents):
        self.network = map
        self.agents = agents

        self.od_min_paths_ff_tt = compute_od_free_flow_tt(self.network, agents)
        self._generate_conf()

    def _generate_conf(self):
        """
        Create SUMO Config file
        """

        write_sumo_conf(
            output_path=SUMO_CONF_CONGESTION_SIM,
            net_file=self.network,
            route_files=ROUTES_CONGESTION_SIM,
            report_outputs={"tripinfo-output": TRIPS_INFO_XML},
            seed=config.seed,
        )

        self.conf = SUMO_CONF_CONGESTION_SIM

    def run_episode(self):
        cmd = ["sumo", "-c", self.conf]
        subprocess.run(cmd)

    def run_episode_with_gui(self):
        cmd = ["sumo-gui", "-c", self.conf]
        subprocess.run(cmd)

    def compute_congestion_metric(self):
        self.run_episode()
        durations_by_id = self._parse_trips_duration()
        per_agent_metric = [
            self._compute_agent_metric(agent, durations_by_id[agent["id"]])
            for agent in self.agents
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
        return {
            trip.get("id"): float(trip.get("duration"))
            for trip in tree.xpath("//tripinfo")
        }