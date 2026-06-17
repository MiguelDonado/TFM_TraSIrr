import subprocess

from config.config import config
from paths import (
    NET,
    ROUTES_DEMAND_CALIBRATION,
    SUMMARY_XML,
    SUMO_CONF_DEMAND_CALIBRATION,
    TRIPS_DEMAND_CALIBRATION,
)
from scripts.get_avg_speed import get_avg_speed
from utils.sumo_xml import write_sumo_conf


class DemandCalibration:
    def __init__(self, map, n_agents, free_flow_speed):
        self.network = map
        self.free_flow_speed = free_flow_speed
        self.n_agents = n_agents

    def _generate_trips(self):
        cmd = [
            "randomTrips.py",
            "-n",
            self.network,
            "-b",
            str(0),
            "-e",
            str(config.end_time),
            "-p",
            str(((config.end_time - 0) / self.n_agents)),
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
        self._generate_trips()
        self._generate_conf()
        self.run_episode()
        self.avg_speed = get_avg_speed(
            config.warm_up_time, summary_filepath=SUMMARY_XML
        )
        target_speed_ratio = round(self.avg_speed / self.free_flow_speed, 2)
        return target_speed_ratio
