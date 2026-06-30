"""
Derives free-flow travel time per edge from the SUMO network (length / speed)
and stores it as a lookup table. Also computes route-level free-flow costs by
summing edge costs, used in scenario to get the median as heuristic for the adaptive time interval
"""

import sys
from pathlib import Path

import pandas as pd
from lxml import etree

from config.config import config
from config.paths import FREE_FLOW_TRAVEL_TIMES


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
