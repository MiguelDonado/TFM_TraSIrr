"""
Computes the free-flow travel time ratio for each route alternative relative
to the shortest path for that OD pair:

    ratio_i = ff_tt(route_i) / ff_tt(shortest_route_for_that_OD)

A ratio of:
- 1.0 means the route is the shortest.
- 1.2 means the route is 20% longer.
- 1.5 means the route is 50% longer.
"""

import pandas as pd

from config.paths import FREE_FLOW_TRAVEL_TIMES


def compute_route_tt_ratios(od_routes: dict) -> dict[tuple, list[float]]:
    """
    Returns {(origin, dest): [ratio_route0, ratio_route1, ...]} for each OD pair.
    """
    edge_costs = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)
    edge_costs = edge_costs.set_index("edge")["free_flow_travel_time"].to_dict()

    result = {}
    for od, od_paths in od_routes.items():
        path_tts = [sum(edge_costs[e] for e in path) for path in od_paths]
        shortest_tt = min(path_tts)
        ratios = [tt / shortest_tt for tt in path_tts]
        ratios.remove(1.0)
        result[od] = ratios
    return result
