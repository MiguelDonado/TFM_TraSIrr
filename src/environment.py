"""
Encapsulate the use of SUMO simulator
"""

import math
import os
import statistics
import subprocess
import xml.etree.ElementTree as ET

import traci
from prettytable import PrettyTable
from sklearn import preprocessing

from paths import ROUTES, TRIPS_INFO


class Environment:
    def __init__(self, scenario, episode_with_gui=None):
        """
        scenario: Scenario object
        gui: Decide if running simulation in GUI mode or just CLI
        """
        self.scenario = scenario
        self.episode_with_gui = episode_with_gui

    def generate_routes_file(self, actions):
        """
        Generate a SUMO routes (.rou.xml) file from agent actions.

        Parameters
        ----------
        actions : dict
            Mapping agent_id -> route index
        scenario : object
            Must contain:
                - agents: list of dicts with keys ["id", "origin", "destination"]
                - od_routes: dict mapping (origin, destination) -> list of routes (list of edges)
        """
        # Root element
        routes = ET.Element("routes")

        for agent in self.scenario.agents:
            agent_id = agent["id"]
            od = (agent["origin"], agent["destination"])

            route_idx = actions[agent_id]
            route_edges = self.scenario.od_routes[od][route_idx]
            edges_str = " ".join(route_edges)

            # Create vehicle
            veh = ET.SubElement(
                routes,
                "vehicle",
                {"id": str(agent_id), "type": "DEFAULT_VEHTYPE", "depart": "0"},
            )

            # Add route inside vehicle
            ET.SubElement(veh, "route", {"edges": edges_str})

        # Write file
        tree = ET.ElementTree(routes)
        tree.write(ROUTES, encoding="utf_8", xml_declaration=True)

    def run_episode(self, actions, current_episode):
        # This functions creates a rou.xml file that allows to run simulation without traci
        self.generate_routes_file(actions)
        # Check if we want to enable gui for some episode
        self.gui = self.episode_with_gui == current_episode
        cmd = [
            "sumo-gui" if self.gui else "sumo",
            "-c",
            self.scenario.conf,
            "--route-files",  # Add the route-files through CLI (for simplicity, avoids having modify config file again)
            ROUTES,
        ]
        subprocess.run(cmd)

    def get_rewards(self):
        travel_times = {}

        tree = ET.parse(TRIPS_INFO)
        root = tree.getroot()

        for trip in root.findall("tripinfo"):
            veh_id = trip.attrib["id"]
            duration = float(trip.attrib["duration"])

            travel_times[veh_id] = duration

        return travel_times
