import pandas as pd
from lxml import etree

from paths import AGENTS_OD

"""
Flow and path travel time aggregation
"""


def _load_actions_and_agents(actions_path):
    df_actions = pd.read_parquet(actions_path)
    df_actions.rename(columns={"action": "path"}, inplace=True)
    df_agents_od = pd.read_parquet(AGENTS_OD)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)
    return df_actions, df_agents_od


def _load_network_edges(network) -> set:
    # 1. Get edges network
    tree = etree.parse(network)
    all_edges = tree.xpath("//edge[not(@function='internal')]/@id")
    return set(all_edges)


def compute_flows_odtp_k(actions_path, output_file):
    """
    Called once per program execution
    This function is used to get the table with all the: "Flows assigned on path p for OD pair (o,d) departing at the time interval t, at episode k"
    for all paths p, for all OD pairs, for all time intervals t and for all episodes k
    """
    # df_actions = Observations table (fact table)
    # df_agents = Lookup table
    df_actions, df_agents_od = _load_actions_and_agents(actions_path)

    # Left join (one to many)
    df_merged_flows = df_actions.merge(df_agents_od, on="agent_id", how="left")

    # Outer parenthesis is to write an expression in multiple lines
    flows = (
        df_merged_flows.groupby(
            ["origin", "destination", "time_interval", "path", "episode"]
        )
        .size()
        .reset_index(name="count")
    )
    flows.to_parquet(output_file)


def compute_travel_time_paths_odtp_k(
    actions_path, trips_info_processed_path, output_file
):
    """
    Called once per program execution
    This function is used to get the table with all the: "Average path travel times on path p for OD pair (o,d) departing at the time interval t, at episode k"
    for all paths p, for all OD pairs, for all time intervals t and for all episodes k
    """

    # df_actions = Observations table (fact table)
    # df_agents = Lookup table
    df_actions, df_agents_od = _load_actions_and_agents(actions_path)
    # Observations table (fact table). Trips info contains data about the whole episode for each vehicle (Duration = travel time...)
    df_travel_times = pd.read_parquet(
        trips_info_processed_path, columns=["episode", "vehicle_id", "duration"]
    )
    # Cast
    df_travel_times["episode"] = df_travel_times["episode"].astype("int32")
    df_travel_times["vehicle_id"] = df_travel_times["vehicle_id"].astype("string")
    df_travel_times["duration"] = df_travel_times["duration"].astype("float32")
    df_travel_times.rename(
        columns={"vehicle_id": "agent_id", "duration": "travel_time"}, inplace=True
    )

    # 1. Join fact tables
    # (I have the agent_id multiple times because I have many episodes on this tables). But for each episode there is only one row per agent
    df_avg_path_travel_time = df_actions.merge(
        df_travel_times,
        on=["episode", "agent_id"],
        how="inner",
    )

    # 2. Join metadata
    df_avg_path_travel_time = df_avg_path_travel_time.merge(
        df_agents_od, on="agent_id", how="left"
    )

    # 3. Compute avg travel time per group
    df_avg_path_travel_time = (
        df_avg_path_travel_time.groupby(
            ["origin", "destination", "time_interval", "path", "episode"]
        ).agg(avg_travel_time=("travel_time", "mean"))
        # After grouping is convenient to reset index
        .reset_index()
    )
    df_avg_path_travel_time.to_parquet(output_file)
