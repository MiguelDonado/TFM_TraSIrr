"""
Encapsulate the use of SUMO simulator with TraCI
"""

import math
import os
import statistics
import xml.etree.ElementTree as ET

import traci
from prettytable import PrettyTable
from sklearn import preprocessing

from paths import TRIPSINFO_OUTPUT_FILE


class Environment:
    def __init__(self, scenario, episode_with_gui=None):
        """
        scenario: Scenario object
        gui: Decide if running simulation in GUI mode or just CLI
        """
        self.scenario = scenario
        self.episode_with_gui = episode_with_gui

    def reset(self, current_episode):
        # Check if we want to enable gui for some episode
        self.gui = self.episode_with_gui == current_episode

        cmd = [
            "sumo-gui" if self.gui else "sumo",
            "-c",
            self.scenario.conf,
            # "--output-prefix",
            # "TIME",
        ]
        traci.start(cmd)

    def insert_vehicles(self, actions):
        for agent in self.scenario.agents:

            agent_id = agent["id"]
            od = (agent["origin"], agent["destination"])

            route_idx = actions[agent_id]
            route_edges = self.scenario.od_routes[od][route_idx]

            route_id = f"route_{agent_id}"

            # Add route
            traci.route.add(route_id, route_edges)

            # Add vehicle
            traci.vehicle.add(vehID=agent_id, routeID=route_id, depart="0")

    def run_episode(self):

        # Get number of vehicles active and waiting to start
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

        traci.close()

    def get_rewards(self):
        travel_times = {}

        tree = ET.parse(TRIPSINFO_OUTPUT_FILE)
        root = tree.getroot()

        for trip in root.findall("tripinfo"):
            veh_id = trip.attrib["id"]
            duration = float(trip.attrib["duration"])

            travel_times[veh_id] = duration

        return travel_times
