"""
Free-flow travel time utilities for edges and routes.

Function                              Purpose
------------------------------------  -----------------------------------------------
generate_free_flow_tt_links           Build FREE_FLOW_TRAVEL_TIMES parquet (length/speed
                                      per edge). Used as imputation fallback in the TDSP
                                      link cost table and as edge weights for route-level
                                      cost functions below.

generate_free_flow_tt_paths           Sum edge costs along every route for each OD pair.
                                      Used by Scenario to compute the median free-flow
                                      route TT, which drives the adaptive time-interval
                                      heuristic.

generate_free_flow_tt_shortest_paths  Same as above but returns only the shortest-path
                                      cost per OD pair as {(origin, dest): tt}.
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
