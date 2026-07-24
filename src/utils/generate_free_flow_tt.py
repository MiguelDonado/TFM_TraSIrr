"""
Free-flow travel time utilities for edges and routes.

Function                              Purpose
------------------------------------  -----------------------------------------------
generate_free_flow_tt_links           Build FREE_FLOW_TRAVEL_TIMES parquet (length/speed
                                      per edge). Used as imputation fallback in the TDSP
                                      link cost table and as edge weights for route-level
                                      cost functions below.

compute_od_free_flow_tt               Free-flow travel time per OD pair: duarouter finds
                                      the shortest-path route, then a single vehicle per
                                      OD is simulated on an empty network. More accurate
                                      than length/max_speed since it accounts for
                                      acceleration/deceleration at junctions.
"""

import subprocess

import pandas as pd
from lxml import etree

from config.config import config
from config.paths import (
    FREE_FLOW_TRAVEL_TIMES,
    ROUTES_CONGESTION_SIM,
    ROUTES_FREE_FLOW,
    SUMO_CONF_FREE_FLOW,
    TRIPS_CONGESTION_SIM,
    TRIPS_INFO_FREE_FLOW,
)
from utils.od_routes import parse_route
from utils.sumo_xml import write_sumo_conf


def generate_free_flow_tt_links():
    """
    Called once per program execution
    Used for imputing missing values link costs table
    """
    data = []

    tree = etree.parse(config.network)
    edges = tree.xpath("//edge[not(@function='internal')]")
    for edge in edges:
        edge_id = edge.get("id")

        lane = edge.find("lane")

        free_flow_speed = float(lane.get("speed"))
        length = float(lane.get("length"))

        free_flow_travel_time = length / free_flow_speed
        data.append({"edge": edge_id, "free_flow_travel_time": free_flow_travel_time})

    df = pd.DataFrame(data)
    df.to_parquet(FREE_FLOW_TRAVEL_TIMES, engine="pyarrow", index=False)


def compute_od_free_flow_tt(network, agents, seed=None):
    """
    Returns {(origin, destination): free_flow_travel_time}.
    """
    seed = seed if seed is not None else config.seed

    od_routes = _compute_shortest_path_routes(network, agents)
    return _simulate_free_flow_tt(network, od_routes, seed)

def _compute_shortest_path_routes(network, agents):
    with open(TRIPS_CONGESTION_SIM, "w") as f:
        f.write("<routes>\n")
        for agent in agents:
            f.write(
                f'\t<trip id="{agent["id"]}" from="{agent["origin"]}"'
                f' to="{agent["destination"]}" depart="{agent["departure_time"]}"/>\n'
            )
        f.write("</routes>\n")

    cmd = [
        "duarouter",
        "-n", network,
        "--route-files", str(TRIPS_CONGESTION_SIM),
        "-o", str(ROUTES_CONGESTION_SIM),
        "--routing-threads", str(config.n_threads),
        "--routing-algorithm", config.routing_algorithm,
    ]
    subprocess.run(cmd, check=True)

    routes = parse_route(ROUTES_CONGESTION_SIM)
    unique_routes = set(tuple(r) for r in routes)
    return {(r[0], r[-1]): list(r) for r in unique_routes}


def _simulate_free_flow_tt(network, od_routes, seed):
    """
    Runs a single SUMO episode with one vehicle per OD pair on an empty network
    to obtain accurate route-level free-flow travel times.

    Vehicles are spaced 200 s apart so they never interact with each other.
    """
    ods = list(od_routes.keys())

    with open(ROUTES_FREE_FLOW, "w") as f:
        f.write("<routes>\n")
        for i, od in enumerate(ods):
            edges = " ".join(od_routes[od])
            f.write(f'\t<route id="ff_route_{i}" edges="{edges}"/>\n')
            f.write(f'\t<vehicle id="ff_{i}" route="ff_route_{i}" depart="{i * 200}"/>\n')
        f.write("</routes>\n")

    write_sumo_conf(
        output_path=SUMO_CONF_FREE_FLOW,
        net_file=network,
        route_files=ROUTES_FREE_FLOW,
        report_outputs={"tripinfo-output": TRIPS_INFO_FREE_FLOW},
        seed=seed,
    )

    subprocess.run(["sumo", "-c", str(SUMO_CONF_FREE_FLOW)], check=True)

    tree = etree.parse(TRIPS_INFO_FREE_FLOW)
    durations = {
        trip.get("id"): float(trip.get("duration"))
        for trip in tree.xpath("//tripinfo")
    }

    return {od: durations[f"ff_{i}"] for i, od in enumerate(ods)}