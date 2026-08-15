"""
SUMO simulator wrapper for episodic training.

Responsibilities
----------------
1. generate_routes_file — writes a .rou.xml from agent actions before
                          each episode, so vehicles can be inserted
                          without TraCI.
2. run_episode          — invokes the sumo (or sumo-gui) CLI with the
                          generated routes file.
3. get_rewards          — parses tripinfo.xml after each episode and
                          returns travel times associated with each
                          agent id.
4. get_waiting_times    — parses tripinfo.xml after each episode and
                          returns waitingTime (seconds stopped/crawling
                          below 0.1 m/s) associated with each agent id,
                          used by RQ12's waiting-time-averse route choice.

No-TraCI design
---------------
Routes are written to a file and passed to SUMO via CLI instead of
using TraCI step-by-step control. This is significantly faster for
large fleets because it avoids the per-timestep Python↔SUMO socket
overhead. The trade-off is that routes cannot be changed mid-episode
(but in the implemented day-to-day learning we do not change routes
in mid-episode, so it does not matter)
"""

import subprocess
import xml.etree.ElementTree as ET

from config.config import config
from config.paths import ROUTES, TRIPS_INFO_XML


class Environment:
    def __init__(self, scenario, episode_with_gui=None):
        """
        scenario: Scenario object
        gui: Decide if running simulation in GUI mode or just CLI
        """
        self.scenario = scenario

    def _generate_routes_file(self, actions):
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
            departure_time = agent["departure_time"]

            route_idx = actions[agent_id]
            route_edges = self.scenario.od_routes[od][route_idx]
            edges_str = " ".join(route_edges)

            # Create vehicle
            veh = ET.SubElement(
                routes,
                "vehicle",
                {
                    "id": str(agent_id),
                    "type": "DEFAULT_VEHTYPE",
                    "depart": str(departure_time),
                },
            )

            # Add route inside vehicle
            ET.SubElement(veh, "route", {"edges": edges_str})

        # Write file
        tree = ET.ElementTree(routes)
        tree.write(ROUTES, encoding="utf_8", xml_declaration=True)

    def run_episode(self, actions, current_episode):
        # This functions creates a rou.xml file that allows to run simulation without traci
        self._generate_routes_file(actions)

        # Check if we want to visualize this episode
        if current_episode in config.episodes_gui:
            self.gui = True
        else:
            self.gui = False

        cmd = [
            "sumo-gui" if self.gui else "sumo",
            "-c",
            self.scenario.conf,
            "--route-files",  # Add the route-files through CLI (for simplicity, avoids having modify config file again)
            ROUTES,
            # Replace the per-step log with a single end-of-run summary
            # (duration, vehicles, teleports, collisions) so it's easy to sanity
            # check the episode regardless of how the script is run.
            "--no-step-log",
            "--duration-log.statistics",
        ]
        subprocess.run(cmd)

    def get_rewards(self):
        travel_times = {}

        tree = ET.parse(TRIPS_INFO_XML)
        root = tree.getroot()

        for trip in root.findall("tripinfo"):
            veh_id = trip.attrib["id"]
            duration = float(trip.attrib["duration"])

            travel_times[veh_id] = duration

        return travel_times

    def get_waiting_times(self):
        waiting_times = {}

        tree = ET.parse(TRIPS_INFO_XML)
        root = tree.getroot()

        for trip in root.findall("tripinfo"):
            veh_id = trip.attrib["id"]
            waiting_time = float(trip.attrib["waitingTime"])

            waiting_times[veh_id] = waiting_time

        return waiting_times
