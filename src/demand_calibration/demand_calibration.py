"""
Runs a single SUMO episode to measure the congestion level
produced by a given number of vehicles on the network.

The goal is to find the n_agents value that achieves a target
congestion level, defined as:

    congestion_ratio = avg_speed_post_warmup / free_flow_speed

    ~ 1.0        — free flow (no congestion)
    ~ 0.7–0.9   — light
    ~ 0.4–0.7   — moderate
    < 0.4        — heavy

This class is instantiated and called repeatedly by the calibration
loop in src/demand_calibration/utils.py, which adjusts n_agents until
congestion_ratio reaches the target value.

Agents are generated externally (via utils.generate_agents) and passed
in, so calibration uses the same OD distribution as training.
"""

import subprocess

from config.config import config
from config.paths import (
    ROUTES_DEMAND_CALIBRATION,
    SUMMARY_XML,
    SUMO_CONF_DEMAND_CALIBRATION,
    TRIPS_DEMAND_CALIBRATION,
)
from utils.get_avg_speed import get_avg_speed
from utils.sumo_xml import write_sumo_conf


class DemandCalibration:
    def __init__(self, map, agents, free_flow_speed):
        self.network = map
        self.agents = agents
        self.free_flow_speed = free_flow_speed

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

    def _generate_conf(self):
        """
        Create SUMO Config file
        """

        write_sumo_conf(
            output_path=SUMO_CONF_DEMAND_CALIBRATION,
            net_file=self.network,
            route_files=ROUTES_DEMAND_CALIBRATION,
            report_outputs={"summary-output": SUMMARY_XML},
            seed=config.seed,
        )

        self.conf = SUMO_CONF_DEMAND_CALIBRATION

    def run_episode(self):
        cmd = ["sumo", "-c", self.conf]
        subprocess.run(cmd)

    def run_episode_with_gui(self):
        cmd = ["sumo-gui", "-c", self.conf]
        subprocess.run(cmd)

    def compute_congestion_ratio(self):
        self._generate_routes()
        self._generate_conf()
        self.run_episode()
        self.avg_speed = get_avg_speed(
            config.warm_up_time, summary_filepath=SUMMARY_XML
        )
        target_speed_ratio = round(self.avg_speed / self.free_flow_speed, 2)
        return target_speed_ratio
