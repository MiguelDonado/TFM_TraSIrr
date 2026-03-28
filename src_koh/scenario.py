"""
Class that creates the required files for SUMO simulator in order to run simulation in this experiment.
"""

import os
import subprocess
import xml.etree.ElementTree as ET

import numpy as np

# Global constants
NET_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/net.net.xml"
TRIP_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/trips.trips.xml"
ROUTE_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/routes.rou.xml"
VTYPE_FILE = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/vtype.add.xml"
SUMO_CONF = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/basic.cfg"  # Final SUMO config file
DEFAULT_VTYPE_FILE = (
    "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/vtype.add.xml"
)
ACCIDENT_PROB = 0.01


class scenario:
    def __init__(self, map, duration, n_veh, vType_list=None, accidents=False):
        """
        Parameters:
        map: network file or .osm file
        duration: simulation time
        n_veh: number of vehicles
        vType_list: optional vehicle types
        accidents: whether to simulate accidents
        """

        # Store number of vehicles
        self.n_veh = n_veh

        """
        Convert map if needed
        If you give an OpenStreetMap file .osm, it converts it to SUMO format using netconvert
        Otherwise, it assumes it's already a SUMO network
        """
        if map.lower().endswith(".osm"):
            self.network = self.convert_map(map)
        else:
            self.network = map

        """
        If you provide vehicle type definitions in a list format (each element of the list is a dictionary), 
        it creates a new additional XML file
        Otherwise, it uses a default additional file

        Example of the list format:
        vType_list = [
            {
                "id": "car",
                "accel": "2.6",
                "decel": "4.5",
                "sigma": "0.5",
                "length": "5.0",
                "maxSpeed": "25.0"
            },
            {
                "id": "truck",
                "accel": "1.2",
                "decel": "3.0",
                "sigma": "0.5",
                "length": "12.0",
                "maxSpeed": "18.0"
            }
        """
        if vType_list is not None:
            self.vType = self.gen_vType(vType_list)
        else:
            self.vType = DEFAULT_VTYPE_FILE

        """
        Automatically
        1. Creates trips
        2. Converts trips to routes
        3. Creates a config file
        """
        self.trips = self.gen_trips(duration, n_veh)
        self.routes = self.gen_routes(accidents)
        self.conf = self.gen_conf()

    def convert_map(self, map):
        """
        Converts OSM to SUMO
        It uses netconvert tool with some options
        It outputs a .net.xml file

        It has some extra options, in order to try to make the conversion as good as possible
        """

        cmd = [
            "netconvert",
            "--osm",
            map,
            "--geometry.remove",
            "--geometry.min-dist",
            "1.0",
            "--geometry.avoid-overlap",
            "--ramps.guess",
            "--roundabouts.guess",
            "--junctions.join",
            "--junctions.join-dist",
            "15",
            "--junctions.corner-detail",
            "10",
            "--junctions.internal-link-detail",
            "10",
            "--osm.turn-lanes",
            "--tls.guess",
            "--tls.guess-signals",
            "--tls.join",
            "-o",
            NET_FILE,
        ]

        # Runs the command in the OS shell
        subprocess.run(cmd, check=True)

        return NET_FILE

    def gen_vType(self, vType_list, dist_id="Thesis"):
        """
        Creates an additional file that stores Vehicle Type
        Example:
            <additional>
                <vTypeDistribution>
                    <vType id="car1" accel="2.6" maxSpeed="30" />
                </vTypeDistribution>
            </additional>

        Example:
        vType_list = [
            {
                "id": "normal_car",
                "maxSpeed": "20.00",
                "color": "yellow",
                "accel": "2",
                "decel": "5",
                "probability": "0.80"
            },
            {
                "id": "Trucks",
                "length": "8.00",
                "maxSpeed": "5.00",
                "vClass": "truck",
                "color": "green",
                "accel": "1",
                "decel": "5",
                "probability": "0.20"
            }
        ]
        """
        # --- Validation ---
        total_prob = 0.0

        for i, vType in enumerate(vType_list):
            if "id" not in vType:
                raise ValueError(f"vType at index {i} missing 'id': {vType}")

            if "probability" not in vType:
                raise ValueError(f"vType '{vType['id']}' missing 'probability'")

            try:
                p = float(vType["probability"])
            except ValueError:
                raise ValueError(
                    f"Invalid probability in vType '{vType['id']}': {vType['probability']}"
                )

            total_prob += p

        with open(VTYPE_FILE, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write("<additional>\n\n")

            f.write(f'\t<vTypeDistribution id="{dist_id}">\n')

            for vType in vType_list:
                vtype_str = "\t\t<vType "
                for key, value in vType.items():
                    vtype_str += f'{key}="{value}" '
                vtype_str += "/>\n"

                f.write(vtype_str)

            f.write("\t</vTypeDistribution>\n\n")
            f.write("</additional>\n")

        return VTYPE_FILE

    def gen_trips(self, duration, n_veh):
        """
        How is calculated the departure interval
        Example:
        duration = 1000 seconds
        n_veh = 100
        one vehicle every 10 seconds

        It runs randomTrips.py (SUMO tool)
        Tool that randomly picks start and end edges
        It creates vehicles
        Assign departure times

        It saves trips into trips.trips.xml

        Explanation of options used with the command
        --trip-attributes: Adds extra attributes to each generated trip
                           We must already have a <vType id="normal_car"> defined
        -b: Begin time
        -e: End time
        -p: Generate 1 trip every n seconds
        --prefix veh_: Generated trips will look like:
            <trip id="veh_0" ... />
            <trip id="veh_1" ... />
        -o: Output file
        """
        n = duration / n_veh

        cmd = [
            "randomTrips.py",
            "-n",
            self.network,
            "--additional-file",
            self.vType,
            "--trip-attributes",
            'type="Thesis"',
            "-b",
            "0",
            "-e",
            str(duration),
            "-p",
            str(n),
            "--prefix",
            "veh_",
            "-o",
            TRIP_FILE,
        ]
        subprocess.run(cmd, check=True)

        return TRIP_FILE

    def gen_routes(self, accidents=False):
        """
        trips: Only specify origin, destination and departure time
        route: Specify all the edges for a given trip

        To generate routes from trips uses the tool duarouter
        It computes the shortest route for each vehicle

        Optional: Accidents
        """

        cmd = [
            "duarouter",
            "--route-files",
            TRIP_FILE,
            "--additional-files",
            self.vType,
            "-n",
            self.network,
            "-o",
            ROUTE_FILE,
        ]

        subprocess.run(cmd, check=True)

        if accidents:
            """
            If:
            100 vehicles
            0.01 probability
            -> 1 vehicle will have an accident
            """
            n_accidents = int(self.n_veh * ACCIDENT_PROB)
            accidents_id_list = []

            """
            Randomly select a vehicle that will be used to simulate an accident
            """
            for _ in range(n_accidents):
                while True:
                    j = np.random.randint(self.n_veh)
                    if j not in accidents_id_list:
                        accidents_id_list.append(j)
                        break

            """
            How accident is simulated

            1. Find the selected vehicle in the XML
            2. Then add: <stop lane="someEdge" endPos="10" duration="20"/>
            That forces the vehicle to stop randomly for 20 seconds
            That simulates an accident/blockage
            """
            for i in accidents_id_list:
                root = ET.parse(ROUTE_FILE).getroot()
                veh = root.find('.//vehicle[@id="veh_' + str(i) + '"]')

                if veh is None:
                    continue

                route = veh.find("route").attrib["edges"]
                route = route.split(" ")

                ET.SubElement(veh.find("route"), "stop")
                stop = veh.find("route").find("stop")
                stop.set("lane", route[np.random.randint(len(route))])
                stop.set("endPos", "10")
                stop.set("duration", "20")

                ET.ElementTree(root).write(ROUTE_FILE, encoding="unicode")

        return ROUTE_FILE

    def gen_conf(self):
        """
        Create SUMO Config file
        """
        with open(SUMO_CONF, "w+") as conf:
            conf.write('<?xml version="1.0"?>\n')
            conf.write("<configuration>\n")
            conf.write("\t<input>\n")
            conf.write('\t\t<net-file value="' + self.network + '"/>\n')
            conf.write('\t\t<route-files value="' + self.routes + '"/>\n')
            conf.write("\t</input>\n")
            conf.write("</configuration>\n")

        return SUMO_CONF
