"""
Derives free-flow travel time per edge from the SUMO network (length / speed)
and stores it as a lookup table. Also computes route-level free-flow costs by
summing edge costs, used in scenario to get the median as heuristic for the adaptive time interval
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

from config.config import config
from config.paths import (
    FREE_FLOW_TRAVEL_TIMES,
    ROUTES_FF_EDGES,
    SUMO_CONF_FF_EDGES,
    VEHROUTE_FF_EDGES,
)
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


def generate_free_flow_tt_links_simulation():
    """
    Called once per program execution.
    Used for imputing missing values in the link costs table.

    Runs a dedicated SUMO episode on an empty network with one vehicle per edge,
    using sandwich routes [P, E, S] so the vehicle enters E at free-flow speed
    (no acceleration bias). Falls back to length/speed for any edge SUMO did
    not record (source/sink edges or insertion failures).
    """
    tree = etree.parse(config.network)

    # Collect non-internal edges with length/speed as fallback values
    edges_data = {}
    for edge in tree.xpath("//edge[not(@function='internal')]"):
        edge_id = edge.get("id")
        lane = edge.find("lane")
        edges_data[edge_id] = {
            "length": float(lane.get("length")),
            "speed": float(lane.get("speed")),
        }
    edges = list(edges_data.keys())

    # Build predecessor/successor maps from network connections
    predecessors = {}
    successors = {}
    for conn in tree.xpath("//connection"):
        from_edge = conn.get("from")
        to_edge = conn.get("to")
        if (
            from_edge
            and to_edge
            and not from_edge.startswith(":")
            and not to_edge.startswith(":")
        ):
            # setdefault: If the key does not exist, give me an empty list automatically
            predecessors.setdefault(to_edge, []).append(from_edge)
            successors.setdefault(from_edge, []).append(to_edge)

    # Build sandwich routes: [P, E, S], [P, E], [E, S], or [E]
    routes = []  # list of (edge_list, has_predecessor)
    for edge_id in edges:
        pred = predecessors.get(edge_id, [None])[0]
        succ = successors.get(edge_id, [None])[0]
        route = []
        if pred:
            route.append(pred)
        route.append(edge_id)
        if succ:
            route.append(succ)
        routes.append((route, pred is not None))

    # Write routes file: one vehicle per edge, staggered 200s apart
    with open(ROUTES_FF_EDGES, "w") as f:
        f.write("<routes>\n")
        for i, (route, _) in enumerate(routes):
            f.write(f'\t<vehicle id="ff_edge_{i}" depart="{i * 200}">\n')
            f.write(f'\t\t<route edges="{" ".join(route)}"/>\n')
            f.write(f"\t</vehicle>\n")
        f.write("</routes>\n")

    write_sumo_conf(
        output_path=SUMO_CONF_FF_EDGES,
        net_file=config.network,
        route_files=ROUTES_FF_EDGES,
        report_outputs={
            "vehroute-output": VEHROUTE_FF_EDGES,
            "vehroute-output.exit-times": "true",
        },
        seed=config.seed,
    )
    subprocess.run(["sumo", "-c", str(SUMO_CONF_FF_EDGES)], check=True)

    # Parse vehroute: extract TT for each target edge
    # Route has predecessor → E is at index 1: TT = exit_times[1] - exit_times[0]
    # No predecessor (source edge) → E is at index 0: TT = exit_times[0] - depart
    veh_tree = etree.parse(VEHROUTE_FF_EDGES)
    edge_tt = {}
    for vehicle in veh_tree.xpath("//vehicle"):
        vid = vehicle.get("id")
        i = int(vid.split("_")[-1])
        target_edge = edges[i]
        has_pred = routes[i][1]
        depart = i * 200.0

        route_elem = vehicle.find("route")
        exit_times = list(map(float, route_elem.get("exitTimes").split()))

        tt = exit_times[1] - exit_times[0] if has_pred else exit_times[0] - depart
        edge_tt[target_edge] = tt

    data = [
        {
            "edge": e,
            # dict.get(key, default) returns the value for key if it exists
            # in the dict, otherwise returns default. length / speed is a fallback
            "free_flow_travel_time": edge_tt.get(
                e, edges_data[e]["length"] / edges_data[e]["speed"]  #
            ),
        }
        for e in edges
    ]
    pd.DataFrame(data).to_parquet(FREE_FLOW_TRAVEL_TIMES, engine="pyarrow", index=False)


def generate_free_flow_tt_paths(od_routes):
    edge_costs = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)
    edge_costs = edge_costs.set_index("edge")["free_flow_travel_time"].to_dict()

    path_costs = []
    for od, od_paths in od_routes.items():

        for path in od_paths:
            total_cost = sum(edge_costs[e] for e in path)
            path_costs.append(total_cost)
    return path_costs


def generate_free_flow_tt_shortest_paths(od_routes):
    """
    Returns {(origin, dest): free_flow_tt}
    """

    edge_costs = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)
    edge_costs = edge_costs.set_index("edge")["free_flow_travel_time"].to_dict()

    return {
        od: sum(edge_costs[e] for e in od_paths[0])
        for od, od_paths in od_routes.items()
    }
