"""
Encapsulate the use of SUMO simulator with TraCI
"""

import math
import os
import statistics
import xml.etree.ElementTree as ET

import numpy as np
import traci
from prettytable import PrettyTable
from sklearn import preprocessing

SUMO_DIR = "/home/miguel/6.Projects/ReplicateSongThesis"
TEMP_ROUTE_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/temp.rou.xml"
TEMP_TRIP_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/temp.trips.xml"
ROUTE_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/network.rou.xml"
TRIP_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/trip.trips.xml"
VTYPE_FILE = "D:/LJMU/PhD/SUMO_Projects/Deep_Learning/sumo_files/network.rou.xml"
ERROR_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/error"
NAV_VEH_ID = "nav_veh"
NAV_VEH_TYPE = "nav_car"
STATUS_IN_ZONE = "IN_ZONE"
STATUS_ARRIVED = "ARRIVED"
ACCIDENT_CLEARANCE_TIME = 20


class Sumo:

    def __init__(
        self,
        sumo_conf,
        max_n_veh,
        gui=False,
        reward_method=0,  # 0 = travel time based, 1 = VEI based
        start_edge="",
        end_edge="",
        incl_travel_time=True,  # Component of the state (expected travel times all roads)
        incl_n_veh=True,  # Component of the state (number of vehicles in all roads)
    ):
        """
        sumo_conf: Path to SUMO config file (that file defines network, routes, additional files...)
        gui: Decide if running simulation in GUI mode or just CLI
        reward_method: Choose the reward function to use
        start_edge: Edge ID where the agent (nav_veh) starts
        end_edge: Edge ID where the agent (nav_veh) must arrive
        incl_travel_time: Include travel time of edges in the state
        incl_n_veh: Include nº vehicles per edge in the state
        """
        self.max_n_veh = max_n_veh
        sumo_cmd = "sumo-gui" if gui else "sumo"
        self.sumo_conf = sumo_conf
        self.cmd = [sumo_cmd, "-c", sumo_conf]

        self.start_edge = start_edge
        self.end_edge = end_edge
        self.incl_travel_time = incl_travel_time
        self.incl_n_veh = incl_n_veh
        self.reward_method = reward_method

        # Run once to extract network info
        """
        e_conn_dict: Dictionary that contains for each 
        edge all its connected edges: Edge -> connected edges
        
        e_lane_dict: Dictionary that contains for each 
        edge all its lanes: Edge -> lanes

        max_n_actions: Maximum number of outgoing edges. 
        (The action space is variable-sized)
        Used to create a fixed output layer of size max_n_actions

        edges: List of all edges

        """
        traci.start(["sumo", "-c", sumo_conf])
        (
            self.e_conn_dict,
            self.e_lane_dict,
            self.max_n_actions,
            self.edges,
        ) = self.get_edge_conn_info()

        # Stores the distance to the destination for all edges in the network
        self.e_distance_dest_dict = self.get_dist_to_dest()

        """
        Size of the observation vector (state)
        Input dimension of the neural network
        Two features per road (expected travel time, vehicle number)
        plus coordinates of the origin and destination (coordinates are 2D)         
        """
        self.n_features = (self.incl_travel_time + self.incl_n_veh) * len(
            self.edges
        ) + 4
        traci.close()

        # Stores destination edge of the agent
        self.target = ""
        # Counter for agents inserted
        self.veh_counter = 0
        # For readability and encapsulation
        # Instead of traci.vehicle inside the class we use self.traci.vehicle
        self.traci = traci

    # ---------------------------------------------------------
    # EDGE CONNECTION INFO
    # ---------------------------------------------------------

    def get_edge_conn_info(self):
        # Outgoing connections
        e_conn_dict = {}
        # Lanes for each edge
        e_lane_dict = {}

        # max number of actions (for NN output size)
        max_link = 0
        # list of all edges
        edges = []
        # To normalize travel times
        self.shortest_travel_time = 1000
        self.longest_travel_time = 0

        # SUMO works at lane level, not edge level
        for lane in traci.lane.getIDList():
            # Ignore internal lanes
            if lane[:1] != ":":
                # Edge the lane belongs to
                l_edge = traci.lane.getEdgeID(lane)
                # Length of the edge
                e_length = traci.lane.getLength(lane)
                # Max speed of the edge
                e_max_speed = traci.lane.getMaxSpeed(lane)

                # Compute travel time bounds
                # Free-flow travel time
                if (e_length / e_max_speed) < self.shortest_travel_time:
                    self.shortest_travel_time = e_length / e_max_speed

                # Worst-case time (very slow)
                if (e_length / 0.1) > self.longest_travel_time:
                    self.longest_travel_time = e_length / 0.1

                # Build list with unique edges
                if l_edge not in edges:
                    edges.append(l_edge)

                # Build edge -> lanes mapping
                # Example: E1 → [E1_0, E1_1]
                if l_edge in e_lane_dict:
                    e_lane_dict[l_edge].append(lane)
                else:
                    e_lane_dict[l_edge] = [lane]

                # Build edge -> outgoing connections
                if traci.lane.getLinks(lane) != []:
                    e_conn_dict[l_edge] = (
                        []
                    )  # Only last lane processed determines connections

                    if len(traci.lane.getLinks(lane)) > max_link:
                        max_link = len(traci.lane.getLinks(lane))

                    # Extract connections
                    # Converts lane -> next lanes
                    # Into
                    # edge -> next edges
                    for i in range(len(traci.lane.getLinks(lane))):
                        connected_lanes = traci.lane.getLinks(lane)[i][0]
                        connected_edges = traci.lane.getEdgeID(connected_lanes)
                        e_conn_dict[l_edge].append(connected_edges)

        # Build a Debug table
        t = PrettyTable()
        field_names = ["Edge_ID"]

        for i in range(max_link):
            field_names.append("action_" + str(i))

        t.field_names = field_names

        for edge in e_conn_dict:
            row = [None for _ in range(max_link)]

            for i, connected_edge in enumerate(e_conn_dict[edge]):
                row[i] = connected_edge

            row = [edge] + row
            t.add_row(row)

        with open("connected_edge.txt", "w+") as f:
            f.write(str(t))

        return e_conn_dict, e_lane_dict, max_link, edges

    # ---------------------------------------------------------
    # DISTANCE TO DESTINATION
    # ---------------------------------------------------------

    def get_dist_to_dest(self):
        """
        Builds a dictionary: Edge -> Distance to destination
        Used for the two-stage epsilon-greedy algorithm that Song proposed

        Initialize dictionary
        It will store
        {
            edge_1: distance_to_destination,
            edge_2: distance_to_destination,
            ...
        }
        """
        e_distance_dest_dict = {}

        # Get destination coordinates
        # Take first lane of that edge (we select one representative lane of destination)
        dest_lane = self.e_lane_dict[self.end_edge][0]
        dest_x, dest_y = traci.lane.getShape(dest_lane)[-1]

        for edge, lanes in self.e_lane_dict.items():
            """
            We select one representative lane of the edge: lanes[0]
            traci.lane.getShape(lane) returns a list of coordinates describing the lane geometry
            Example: [(x1,y1), (x2,y2), ...]
            [-1] means take the last coordinate (the end of the lane)
            end_x, end_y: Is the endpoint of the destination edge
            """
            # Take first lane of edge and last coordinate of the lane
            end_x, end_y = traci.lane.getShape(lanes[0])[-1]
            # Compute euclidean distance
            distance = math.hypot(dest_x - end_x, dest_y - end_y)
            e_distance_dest_dict[edge] = distance

            # -------- PrettyTable (debug output) --------
            t = PrettyTable()
            t.field_names = ["Edge_ID", "distance to destination"]

            for edge, distance in e_distance_dest_dict.items():
                t.add_row([edge, distance])

            with open("distance_to_destination.txt", "w+") as f:
                f.write(str(t))

        return e_distance_dest_dict

    # ---------------------------------------------------------
    # RESET
    # ---------------------------------------------------------

    def reset(self):
        """
        1. Starts SUMO
        2. Adds agent
        3. Initializes route tracking
        4. Runs simulation until first decision point
        """
        traci.start(self.cmd)
        self.actual_route = [self.start_edge]

        self.status = "NONE"

        self.time_in_edge = [0]
        self.VEI_in_edge = []
        self.CO = 0
        self.HC = 0
        self.NOX = 0
        self.PMX = 0
        self.total_CO = 0
        self.total_HC = 0
        self.total_NOX = 0
        self.total_PMX = 0
        self.time_in_edge = [0]
        self.VEI_in_edge = []

        self.add_veh(is_nav=True)

        return self.run_simulation()

    # ---------------------------------------------------------
    # DEFAULT ROUTE
    # ---------------------------------------------------------

    def get_default_route(self, start_edge, end_edge):
        """
        Computes a default route between two edges using duarouter (shortest-path)
        """

        # Get the network file used in SUMO config
        root = ET.parse(self.sumo_conf)
        net_file = root.find("input/net-file").get("value")

        """
        Create a temporary trip file
        It writes the following:
        <?xml version="1.0"?>
        <trips>
            <trip id="0" depart="0.00" from="start_edge" to="end_edge" />
        </trips>

        We are creating an artificial request: Route this vehicle from A to B
        """
        with open(TEMP_TRIP_FILE, "w") as trip_file:
            trip_file.write('<?xml version="1.0"?>\n')
            trip_file.write("<trips>\n")
            trip_file.write(
                f'\t<trip id="0" depart="0.00" from="{start_edge}" to="{end_edge}" />\n'
            )
            trip_file.write("</trips>\n")

        # Shell command. Read trip. Computes shortest path. Write full route file
        cmd = (
            f"duarouter --route-files {TEMP_TRIP_FILE} "
            f"-n {net_file} -o {TEMP_ROUTE_FILE}"
        )

        # Return code 0 -> Sucess
        if os.system(cmd) == 0:
            """
            Read generated route
            Output file looks like:
            <vehicle id="0">
                <route edges="E1 E5 E9 E12"/>
            </vehicle>
            After split, we return ["E1", "E5", "E9", "E12"]. That is a list of edges forming shortest path
            """
            root = ET.parse(TEMP_ROUTE_FILE).getroot()
            route = root.find("vehicle/route").get("edges")
            self.default_route = route.split(" ")
            return route.split(" ")

        return None

    # ---------------------------------------------------------
    # ADD VEHICLE
    # ---------------------------------------------------------

    def add_veh(self, is_nav=False, veh_id=None, route=None, type=None):
        """
        Adds the agent to SUMO simulation
        Is not used for the other vehicles
        """
        if is_nav:
            # Asssign vehicle id (nav_veh)
            veh_id = NAV_VEH_ID
            # Compute route if not given
            route = route or self.get_default_route(self.start_edge, self.end_edge)
            """
            If type was passed to the function use it
            Otherwise use the default NAV_VEH_TYPE
            It ensures the vehicle always has a valid type
            """
            type = type or NAV_VEH_TYPE

            # Create unique Route ID (Routes must have a unique ID)
            route_id = veh_id + str(self.veh_counter)

            # Add route to SUMO (only in-memory doesnt modify the file)
            traci.route.add(route_id, route)
            # Add vehicle
            # traci.vehicle.add(veh_id, route_id, type)
            traci.vehicletype.copy("DEFAULT_VEHTYPE", NAV_VEH_TYPE)
            traci.vehicletype.setColor(NAV_VEH_TYPE, (255, 0, 0))
            traci.vehicle.add(veh_id, route_id, NAV_VEH_TYPE)

            self.in_zone = None
            self.actual_route.append(self.start_edge)
            self.time_in_edge.append(0)
        else:
            v_id = veh_id + str(self.veh_counter)
            traci.route.add(v_id, route)
            traci.vehicle.add(v_id, v_id, type)
        self.veh_counter += 1

    # ---------------------------------------------------------
    # RUN SIMULATION
    # ---------------------------------------------------------

    def run_simulation(self, action=None):
        # Get current edge
        v_edge = traci.vehicle.getRoadID(NAV_VEH_ID)

        """
        self.e_conn_dict[v_edge] → possible next edges
        [action] → choose one
        changeTarget → reroute vehicle
        """
        if action is not None:
            self.target = self.e_conn_dict[v_edge][action]
            traci.vehicle.changeTarget(NAV_VEH_ID, self.target)

        while True:
            # Advances SUMO by one step
            traci.simulationStep()
            # Increase time spent in current edge
            # Example
            # [3, 5, 2] → now [3, 5, 3]
            self.time_in_edge[-1] += 1

            # Check status
            status = self.get_status()

            if NAV_VEH_ID in traci.vehicle.getIDList():
                self.get_emissions()

            if status == "NEW":
                # Start timing new adge
                self.time_in_edge.append(0)
                self.VEI_in_edge.append(self.get_VEI())
                # Add new edge to the route of the car
                self.actual_route.append(v_edge)
                self.CO = 0
                self.HC = 0
                self.NOX = 0
                self.PMX = 0

                n_actions = 0
                # Get reward
                done = 0
                reward = self.get_reward(done)

                # Get observation
                # State vector + Debug table
                obs, t = self.get_observation()

                return obs, t, n_actions, reward, done

            # Decision point
            if status == "IN_ZONE":
                done = 0
                # State vector + Debug table
                obs, t = self.get_observation()
                # Get current edge
                v_edge = traci.vehicle.getRoadID(NAV_VEH_ID)
                # Get available actions
                n_actions = len(self.e_conn_dict[v_edge])
                # No reward yet (intermediate step)
                reward = 0

                # What RL expects
                return obs, t, n_actions, reward, done

            # Terminal state
            elif status == "DONE":
                done = 1
                reward = self.get_reward(done)
                obs = np.zeros(self.n_features)
                t = ""
                n_actions = 0

                return obs, t, n_actions, reward, done

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def get_status(self):
        # Check if vehicle is in simulation
        if NAV_VEH_ID in traci.vehicle.getIDList():
            # Get lane info
            v_lane = traci.vehicle.getLaneID(NAV_VEH_ID)

            # Ignore junction lanes
            if v_lane[:1] != ":":
                # Get position
                v_pos = traci.vehicle.getLanePosition(NAV_VEH_ID)
                # Get length
                l_len = traci.lane.getLength(v_lane)
                # Get edge
                v_edge = traci.vehicle.getRoadID(NAV_VEH_ID)
                # Get zone length
                zone_length = self.get_decision_zone_length()

                # If vehicle was not previously in decision zone
                # and is near the end of the edge and the edge is not the destination edge
                if (
                    self.in_zone == None
                    and l_len - v_pos <= zone_length
                    and v_edge not in [self.end_edge]
                ):
                    # Only once when entering the decision zone
                    self.in_zone = v_edge
                    self.status = "IN_ZONE"
                    return "IN_ZONE"

                # Entering a new edge
                elif self.in_zone != None and self.in_zone != v_edge:
                    self.in_zone = None
                    self.status = "NEW"
                    return "NEW"

                # No event happened
                else:
                    self.status = "NONE"
                    return "NONE"

        # Vehicle finished trip
        elif NAV_VEH_ID in traci.simulation.getArrivedIDList():
            self.status = "DONE"
            return "DONE"

    # ---------------------------------------------------------
    # DECISION ZONE LENGTH
    # ---------------------------------------------------------

    def get_decision_zone_length(self):
        # Get current lane
        v_lane = traci.vehicle.getLaneID(NAV_VEH_ID)
        # Get maximum speed
        v_max_speed = traci.vehicle.getMaxSpeed(NAV_VEH_ID)
        # Get decelaration capability
        v_decel = traci.vehicle.getDecel(NAV_VEH_ID)
        # Reaction time driver
        v_tau = traci.vehicle.getTau(NAV_VEH_ID)
        # Length lane
        l_len = traci.lane.getLength(v_lane)

        zone_length = v_max_speed + (v_max_speed * v_decel * v_tau)

        # If lane is short, then decision zone entire length
        if l_len <= zone_length:
            return l_len

        return zone_length

    def get_emissions(self):
        self.CO += traci.vehicle.getCOEmission(NAV_VEH_ID)
        self.HC += traci.vehicle.getHCEmission(NAV_VEH_ID)
        self.NOX += traci.vehicle.getNOxEmission(NAV_VEH_ID)
        self.PMX += traci.vehicle.getPMxEmission(NAV_VEH_ID)
        self.total_CO += traci.vehicle.getCOEmission(NAV_VEH_ID)
        self.total_HC += traci.vehicle.getHCEmission(NAV_VEH_ID)
        self.total_NOX += traci.vehicle.getNOxEmission(NAV_VEH_ID)
        self.total_PMX += traci.vehicle.getPMxEmission(NAV_VEH_ID)

    def get_observation(self):
        """
        Builds:
            obs = [
                destination_position,
                vehicle_position,
                travel_time_all_edges,
                number_of_vehicles_all_edges
            ]

        Returns: (np_obs, display_obs)
            np_obs: Input to your NN
            display_obs: Debug string (human readable)
        """
        # Initialize arrays
        np_veh_pos = np.array([])
        np_travel_time = np.array([])
        np_n_veh = np.array([])
        np_obs = np.array([])

        # Get vehicle position (the end of the lane, not exact position)
        l_ID = traci.vehicle.getLaneID(NAV_VEH_ID)
        v_pos_x, v_pos_y = traci.lane.getShape(l_ID)[-1]
        # v_pos_x, v_pos_y = traci.vehicle.getPosition(NAV_VEH_ID)
        # Get network boundaries (to normalize coordinates)
        [min_x, min_y], [max_x, max_y] = traci.simulation.getNetBoundary()

        # Get destination position (endpoint)
        l_ID = self.e_lane_dict[self.end_edge][0]
        des_x, des_y = traci.lane.getShape(l_ID)[-1]

        # For visualization
        display_obs = "Destination: " + str([des_x, des_y]) + "\n"
        display_obs += "Vehicle Position: " + str([v_pos_x, v_pos_y]) + "\n"

        # Ensure destination is inside bounds
        min_x = des_x if des_x < min_x else min_x
        min_y = des_y if des_y < min_y else min_y
        max_x = des_x if des_x > max_x else max_x
        max_y = des_y if des_y > max_y else max_y

        # Normalize positions
        des_x = (des_x - min_x) / (max_x - min_x)
        des_y = (des_y - min_y) / (max_y - min_y)
        v_pos_x = (v_pos_x - min_x) / (max_x - min_x)
        v_pos_y = (v_pos_y - min_y) / (max_y - min_y)

        # Store position features
        np_veh_pos = np.append(np_veh_pos, [des_x, des_y])
        np_veh_pos = np.append(np_veh_pos, [v_pos_x, v_pos_y])

        # Add to observation
        np_obs = np.append(np_obs, np_veh_pos)

        # Edge-level features (travel time and nº veh)
        if self.incl_travel_time or self.incl_n_veh:
            t = PrettyTable()
            field_names = ["Edge ID"]

            # Loop over all edges
            for e_ID in traci.edge.getIDList():
                # Skip internal edges
                if e_ID[:1] != ":":
                    # Add edge to the prettytable
                    row = [e_ID]

                    # Travel time feature
                    if self.incl_travel_time:

                        # Mean speed edge
                        e_mean_speed = traci.edge.getLastStepMeanSpeed(e_ID)
                        # Lanes of the edge
                        e_lane = self.e_lane_dict[e_ID][0]
                        # Length edge
                        e_length = traci.lane.getLength(e_lane)
                        # Max speed edge
                        e_max_speed = traci.lane.getMaxSpeed(e_lane)

                        # Case 1: Mean speed = 0
                        if e_mean_speed == 0:
                            # Subcase A: full occupancy
                            if traci.edge.getLastStepOccupancy(e_ID) == 100:
                                # Assume very slow speed
                                e_travel_time = e_length / 0.1
                            else:
                                is_accident = True
                                first_veh_pos = 0
                                last_veh_pos = e_length

                                # Find first and last vehicle in the lane
                                for veh in traci.edge.getLastStepVehicleIDs(e_ID):
                                    v_lane_pos = traci.vehicle.getLanePosition(veh)

                                    if v_lane_pos == e_length:
                                        is_accident = False

                                    if v_lane_pos > first_veh_pos:
                                        first_veh_pos = v_lane_pos

                                    if v_lane_pos < last_veh_pos:
                                        last_veh_pos = v_lane_pos

                                # Subcase B: Accident detected
                                if is_accident:
                                    e_travel_time = (
                                        (last_veh_pos / e_max_speed)
                                        + ACCIDENT_CLEARANCE_TIME
                                        + ((e_length - first_veh_pos) / e_max_speed)
                                    )
                                # Subcase C: No accident (partial congestion)
                                else:
                                    e_travel_time = (last_veh_pos / e_max_speed) + (
                                        (e_length - last_veh_pos) / 0.1
                                    )
                        # Case 2: normal traffic
                        else:
                            # getTraveltime (length / mean speed)
                            e_travel_time = traci.edge.getTraveltime(e_ID)

                        # Normalize travel time
                        e_travel_time = (e_travel_time - self.shortest_travel_time) / (
                            self.longest_travel_time - self.shortest_travel_time
                        )

                        # Store travel_time
                        np_travel_time = np.append(np_travel_time, e_travel_time)

                        # For PrettyTable
                        field_names.append("expected travel time")
                        row.append(e_mean_speed)

                    # Number of vehicles
                    if self.incl_n_veh:
                        # Get vehicle number
                        e_n_veh = traci.edge.getLastStepVehicleNumber(e_ID)
                        # Normalize by max vehicles
                        e_n_veh = e_n_veh / self.max_n_veh
                        # Store
                        np_n_veh = np.append(np_n_veh, e_n_veh)
                        # Pretty table
                        field_names.append("vehicle number")
                        row.append(e_n_veh)

                    if t.field_names == []:
                        t.field_names = field_names

                    t.add_row(row)

            display_obs += str(t)

            # Final observation tensor
            np_obs = np.append(np_obs, np_travel_time)
            np_obs = np.append(np_obs, np_n_veh)

        return np_obs, display_obs

    def get_reward(self, done):
        """
        Reward has two phases
        During the trip: Negative reward (penalty)
        At the end: Positive reward (success)
        """
        # When vehicle reaches destination +1 reward (TERMINAL REWARD)
        if done:
            reward = 1
        # (INTERMEDIATE REWARD) during trip
        else:
            # If we are using reward function based on travel time
            # [-2]: Last completed edge
            # [-1]: Current edge (still ongoing)
            # We gave the reward after we complete the edge
            if self.reward_method == 0:
                reward = self.time_in_edge[-2] / -1
            # If we are using reward function based on emissions
            else:
                reward = self.VEI_in_edge[-1] / -1

        return reward

    def get_VEI(self):
        # Some values for calculation in this function is hardcoded by following the euro standard
        # need to change when using different vehicle type

        w_CO = 1
        w_HC = 1 / 0.068
        w_NOX = 1 / 0.06
        w_PMX = 1 / 0.005

        std_CO = 1000
        std_HC = 68
        std_NOX = 60
        std_PMX = 5

        # convert from miles to km
        CO_edge = self.CO * 1.6
        HC_edge = self.HC * 1.6
        NOX_edge = self.NOX * 1.6
        PMX_edge = self.PMX * 1.6

        VEI_CO = (CO_edge * w_CO) / std_CO
        VEI_HC = (HC_edge * w_HC) / std_HC
        VEI_NOX = (NOX_edge * w_NOX) / std_NOX
        VEI_PMX = (PMX_edge * w_PMX) / std_PMX

        VEI = VEI_CO + VEI_HC + VEI_NOX + VEI_PMX

        return VEI

    # ---------------------------------------------------------
    # STEP COUNT
    # ---------------------------------------------------------

    def step_count(self):
        return traci.simulation.getTime()

    # ---------------------------------------------------------
    # CLOSE
    # ---------------------------------------------------------

    def close(self):
        traci.close()
