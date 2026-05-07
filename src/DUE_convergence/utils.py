import pandas as pd
from paths import (
    AGENTS_OD,
    ACTIONS,
    TRIPS_INFO_PROCESSED,
    FREE_FLOW_TRAVEL_TIMES,
    VEHROUTE_PROCESSED,
    EDGEDATA_PROCESSED,
    AVG_LINK_TRAVEL_TIMES,
)
from lxml import etree
from config.config import config


def get_flows_path_per_odtp_k():
    """
    This function is used to get the table with all the: "Flows assigned on path p for OD pair (o,d) departing at the time interval t, at episode k"
    for all paths p, for all OD pairs, for all time intervals t and for all episodes k
    """
    # Observations table (fact table)
    df_actions = pd.read_parquet(ACTIONS)
    df_actions.rename(columns={"action": "path"}, inplace=True)
    # Lookup table
    df_agents_od = pd.read_parquet(AGENTS_OD)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)

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
    return flows


def get_avg_path_travel_time_per_odtp_k():
    """
    This function is used to get the table with all the: "Average path travel times on path p for OD pair (o,d) departing at the time interval t, at episode k"
    for all paths p, for all OD pairs, for all time intervals t and for all episodes k
    """
    # Observations table (fact table)
    df_actions = pd.read_parquet(ACTIONS)
    df_actions.rename(columns={"action": "path"}, inplace=True)
    # Lookup table
    df_agents_od = pd.read_parquet(AGENTS_OD)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)
    # Observations table (fact table). Trips info contains data about the whole episode for each vehicle (Duration = travel time...)
    df_travel_times = pd.read_parquet(
        TRIPS_INFO_PROCESSED, columns=["episode", "vehicle_id", "duration"]
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
    return df_avg_path_travel_time


def get_avg_link_travel_time_per_t_k():
    """
    This function is used to get the table with all the: "Average link travel times on link j departing at the time interval t, at episode k"
    for all links j, for all time intervals t and for all episodes k

    GOTCHAS:
    > vehroute output file only includes edges that were used in some episode of the training.
    If some edge was not used, it wont apppear on vehroute output.
    But when computing the avg link travel time table, we want all grid of combinations

    Steps:
    1. Generate free flow travel times of all liks. It would be needed when filling the empty cells in the average link travel time
    2. Get edges of the network (to generate all grid of combinations)
    3. Read files to get necessary info to build the table
    4. Add logic to compute entry time for the first edge of the path (is basically the departure time)
    5. Compute travel times on edges
    6. Compute time interval columns
    7. Compute avg travel time links per episode and time interval
    8. Apply logic to ensure table has all grid of combinations
    9. Apply logic to fill missing values of the table.
        a) Fill forward: We do not have any vehicle entering on link at t (NaN) and density_t > 0  (congestion)
        b) Free-flow: Otherwise
    """

    # 1. Generate file with free flow travel times of all links in the network and load it
    generate_free_flow_travel_times_links()
    free_flow_travel_times = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)

    delta_t = config.time_interval

    # 2. Get edges network
    document = config.network
    tree = etree.parse(document)
    all_edges = tree.xpath("//edge[not(@function='internal')]/@id")
    all_edges = set(all_edges)

    # 3. Read vehroute file (travel time edges)
    df_edges = pd.read_parquet(VEHROUTE_PROCESSED)
    df_edges.rename(columns={"vehicle_id": "agent_id"}, inplace=True)

    # 4. Read agents_od to get departure_times of each agent
    df_agents_od = pd.read_parquet(AGENTS_OD)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)

    # 5. Merge
    df_edges = df_edges.merge(
        df_agents_od[["agent_id", "departure_time"]], on="agent_id", how="left"
    )
    # 6. Sort, is not needed, but just in case to make sure
    df_edges = df_edges.sort_values(["episode", "agent_id", "exit_times"])

    # 7. Compute entry time (entry time 2nd edge = exit time 1st edge)
    df_edges["entry_time"] = df_edges.groupby(["episode", "agent_id"])[
        "exit_times"
    ].shift(1)

    # 8. Fill first edge correctly = departure time
    # The first edge for each vehicle and episode, I cannot assume that entry time is 0
    # because vehicles have different departure times.
    df_edges["entry_time"] = df_edges["entry_time"].fillna(df_edges["departure_time"])
    df_edges = df_edges.drop("departure_time", axis=1)

    # 9. Compute travel time
    df_edges["travel_time"] = df_edges["exit_times"] - df_edges["entry_time"]

    # 10. Check travel times on links are OK.
    assert (df_edges["travel_time"] >= 0).all()

    # 11. Create time interval (15 mins)
    df_edges["time_interval"] = (df_edges["entry_time"] // delta_t).astype(int)

    # 12. Compute avg travel times on links (per episode, edge and time interval)
    avg_travel_time_links = df_edges.groupby(["episode", "edge", "time_interval"])[
        "travel_time"
    ].mean()

    ###############
    # GOTCHA LOGIC (ENSURE FULL GRID OF COMBINATIONS)
    ###############

    # 1. We need full grid of combinations, not just the observed ones
    # For every (episode, edge, time_interval) have an average (even if missing)

    # Following code creates all possible combinations of the three sets
    # We are building (episode, edge, time_interval) for every possible combinatioon
    full_index = pd.MultiIndex.from_product(
        [
            df_edges["episode"].unique(),
            all_edges,  # full set of edges (used + unused)
            df_edges["time_interval"].unique(),
        ],
        names=["episode", "edge", "time_interval"],
    )
    # Reindex to force all combinations (missing combinations become travel_time = NaN)
    avg_travel_time_links = avg_travel_time_links.reindex(full_index).reset_index()

    ###############
    # GOTCHA LOGIC (FILL MISSING VALUES)
    ###############
    # 1. Read edgedata parquet (density edges by intervals)
    df_density = pd.read_parquet(EDGEDATA_PROCESSED)
    df_density.rename(columns={"interval": "time_interval"}, inplace=True)

    # 2. Ensure full grid (edges,episode,intervals) (even edges with zero density appear)
    # Because prior to that, edgedata.parquet only contains data when density > 0
    # (hence missing rows for edges not used at some intervals, or edges never used at all)
    # Fill with 0 densities for NaN values
    full_index = pd.MultiIndex.from_product(
        [
            df_density["episode"].unique(),
            df_density["time_interval"].unique(),
            all_edges,
        ],
        names=["episode", "time_interval", "edge"],
    )
    df_full = (
        df_density.set_index(["episode", "time_interval", "edge"])
        # Turn columns into index of df
        .reindex(full_index)
        .reset_index()
        .fillna(0)
    )

    # 3. Add helper column to avg link travel time table (Densities). Will be used to determine the method of filling NaN
    df = avg_travel_time_links.merge(
        df_full, on=["episode", "time_interval", "edge"], how="left"
    )
    # Sort (important for ffill)
    df = df.sort_values(["episode", "edge", "time_interval"])

    ###############
    # Missing values. Forward fill
    ###############

    # 1. Apply forward fill in NaN cells where density > threshold_density
    # Create helper column for ffill
    # For each episode + edge, look at
    # travel time over time (implicitly ordered by interval), copy last known value forward
    df["ffill"] = df.groupby(["episode", "edge"])["travel_time"].ffill()
    df = df.astype(
        {
            "episode": "Int64",
            "edge": str,
            "time_interval": "Int64",
            "travel_time": float,
            "density": float,
            "ffill": float,
        }
    )
    # Mask (condition). Select rows with travel_time missing and where density > threshold_density
    mask = df["travel_time"].isna() & (df["density"] > config.threshold_density)
    # Apply forward fill (only where mask true, replace travel_time with forward filled value)
    # .loc[rows,columns] It selects rows and columns
    df.loc[mask, "travel_time"] = df.loc[mask, "ffill"]

    ###############
    # Missing values. Free flow travel time
    ###############

    # Add free_flow travel time columns
    df = df.merge(
        free_flow_travel_times[["edge", "free_flow_travel_time"]], on="edge", how="left"
    )c one wa
    # For leftover NaN values that are still present after applying fill forward, use free flow travel times
    mask = df["travel_time"].isna()
    df.loc[mask, "travel_time"] = df.loc[mask, "free_flow_travel_time"]
    df = df.drop(["density", "ffill", "free_flow_travel_time"], axis="columns")
    df.to_parquet(AVG_LINK_TRAVEL_TIMES)


def generate_free_flow_travel_times_links():
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
