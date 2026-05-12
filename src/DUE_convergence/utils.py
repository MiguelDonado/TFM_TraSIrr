import shutil
import subprocess
import pandas as pd
from paths import (
    DEMAND_ODT,
    AGENTS_OD,
    ACTIONS,
    TRIPS_INFO_PROCESSED,
    FREE_FLOW_TRAVEL_TIMES,
    VEHROUTE_PROCESSED,
    EDGEDATA_PROCESSED,
    COST_LINKS,
    TIMES_INTERVAL,
    WEIGHTS_DIR,
    TRIPS_TDSP,
    SHORTEST_PATHS_DIR,
    FLOWS_PATHS,
    COST_PATHS,
    COST_MIN_PATHS,
)
from lxml import etree


def compute_flows_odtp_k():
    """
    Called once per program execution
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
    flows.to_parquet(FLOWS_PATHS)


def compute_travel_time_paths_odtp_k():
    """
    Called once per program execution
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
    df_avg_path_travel_time.to_parquet(COST_PATHS)


def compute_travel_time_links_t_k(time_interval, network, threshold_density):
    """
    Called once per program execution
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
    free_flow_travel_times = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)

    delta_t = time_interval

    # 2. Get edges network
    document = network
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
    mask = df["travel_time"].isna() & (df["density"] > threshold_density)
    # Apply forward fill (only where mask true, replace travel_time with forward filled value)
    # .loc[rows,columns] It selects rows and columns
    df.loc[mask, "travel_time"] = df.loc[mask, "ffill"]

    ###############
    # Missing values. Free flow travel time
    ###############

    # Add free_flow travel time columns
    df = df.merge(
        free_flow_travel_times[["edge", "free_flow_travel_time"]], on="edge", how="left"
    )
    # For leftover NaN values that are still present after applying fill forward, use free flow travel times
    mask = df["travel_time"].isna()
    df.loc[mask, "travel_time"] = df.loc[mask, "free_flow_travel_time"]
    df = df.drop(["density", "ffill", "free_flow_travel_time"], axis="columns")
    df.to_parquet(COST_LINKS)


def generate_weights_xmls():
    """
    Called once per program execution
    This function creates the xml file containing the time depedent costs of edges for each episode.
    It does so, for all episodes.
    It will be passed as input to duarouter. Determines the costs of edges that will be used when computing shortest paths
    """
    time_intervals_table = pd.read_parquet(TIMES_INTERVAL)

    # Load parquet file that will be converted to xml file
    df = pd.read_parquet(COST_LINKS)

    # One xml file per episode
    for episode in df["episode"].unique():

        root = etree.Element("meandata")

        for interval_id in time_intervals_table["interval"]:

            row = time_intervals_table[
                (time_intervals_table["interval"] == interval_id)
            ].iloc[0]

            begin = str(row["start_time"])
            end = str(row["end_time"])

            # XML Interval element
            interval_xml = etree.SubElement(
                root, "interval", begin=begin, end=end, id="whatever"
            )

            # Filter once
            filtered_interval = df[
                (df["episode"] == episode) & (df["time_interval"] == interval_id)
            ]

            for _, edge_row in filtered_interval.iterrows():
                # Edge element
                etree.SubElement(
                    interval_xml,
                    "edge",
                    id=str(edge_row["edge"]),
                    traveltime=str(edge_row["travel_time"]),
                )

        # Write XML
        tree = etree.ElementTree(root)

        output_file = WEIGHTS_DIR / f"Weights_episode_{episode}.xml"

        tree.write(
            output_file,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )


def compute_time_dependent_shortest_paths(network, seed):
    """
    This function computes the time dependent shortest path for all od and for all t
    """
    episodes = len([f for f in WEIGHTS_DIR.iterdir() if f.is_file()])
    for episode in range(1, episodes + 1):
        routes_file = SHORTEST_PATHS_DIR / f"shortest_path_episode_{episode}.xml"
        weights_file = WEIGHTS_DIR / f"Weights_episode_{episode}.xml"
        __run_duarouter(network, TRIPS_TDSP, routes_file, weights_file, seed)


def compute_cost_min_paths_odt_k(time_interval):
    """
    Computes the table that contains the cost for all time dependent shortest paths
    """
    rows = []

    for file in SHORTEST_PATHS_DIR.iterdir():
        episode = file.stem.split("_")[-1]

        tree = etree.parse(file)
        odt_s = tree.xpath("//vehicle")

        # For each od pair on each interval
        for odt in odt_s:

            depart = float(odt.get("depart"))
            interval = int(depart // time_interval)

            cost = odt.xpath("route/@cost")[0]

            edges = odt.xpath("route/@edges")[0]
            edges = edges.split()

            origin = edges[0]
            destination = edges[-1]

            rows.append(
                {
                    "episode": episode,
                    "origin": origin,
                    "destination": destination,
                    "time_interval": interval,
                    "cost": cost,
                }
            )

    df = pd.DataFrame(rows)
    df["episode"] = df["episode"].astype(int)
    df = df.sort_values(
        by=["episode", "origin", "destination"],
    ).reset_index(drop=True)
    df.to_parquet(COST_MIN_PATHS)


def compute_rgap_and_refined_rgap():
    flow_df = pd.read_parquet(FLOWS_PATHS)
    flow_df = flow_df.rename(columns={"count": "flow"})
    cost_df = pd.read_parquet(COST_PATHS)
    cost_df = cost_df.rename(columns={"avg_travel_time": "cost"})
    min_cost_df = pd.read_parquet(COST_MIN_PATHS)
    min_cost_df = min_cost_df.rename(columns={"cost": "min_cost"})
    demand_df = pd.read_parquet(DEMAND_ODT)
    demand_df = demand_df.rename(columns={"count": "demand"})

    # Merge into a single table
    df = (
        flow_df.merge(
            cost_df, on=["episode", "origin", "destination", "time_interval", "path"]
        )
        .merge(min_cost_df, on=["episode", "origin", "destination", "time_interval"])
        .merge(demand_df, on=["origin", "destination", "time_interval"])
    )

    # Reorder columns
    df = df[
        [
            "episode",
            "origin",
            "destination",
            "time_interval",
            "path",
            "flow",
            "cost",
            "min_cost",
            "demand",
        ]
    ]

    # Sort df
    df = df.sort_values(
        by=["episode", "origin", "destination", "time_interval", "path"]
    ).reset_index(drop=True)

    # Right column types
    df["min_cost"] = df["min_cost"].astype("float32")

    # Compute 2 versions rgap
    rgap = compute_rgap(df)
    redefined_rgap = compute_redefined_rgap(df)
    return (rgap, redefined_rgap)


def compute_redefined_rgap(df):
    """
    Like rgap but for each interval
    """
    # Compute numerator rgap per episode
    df["gap_term"] = df["flow"] * (df["cost"] - df["min_cost"])
    numerator = df.groupby(["episode", "time_interval"])["gap_term"].sum()

    # Compute denominator rgap per episode
    # Demand is duplicated. For each episode, origin, destination, time_interval -> demand is duplicated across paths (duplicated path times)
    denominator_df = df[
        ["episode", "origin", "destination", "time_interval", "demand", "min_cost"]
    ].drop_duplicates()

    denominator = (
        (denominator_df["demand"] * denominator_df["min_cost"])
        .groupby([denominator_df["episode"], denominator_df["time_interval"]])
        .sum()
    )

    refined_rgap = numerator / denominator

    refined_rgap = refined_rgap.reset_index(name="refined_rgap")
    return refined_rgap


def compute_rgap(df):
    # Compute numerator rgap per episode
    df["gap_term"] = df["flow"] * (df["cost"] - df["min_cost"])
    numerator = df.groupby("episode")["gap_term"].sum()

    # Compute denominator rgap per episode
    # Demand is duplicated. For each episode, origin, destination, time_interval -> demand is duplicated across paths (duplicated path times)
    denominator_df = df[
        ["episode", "origin", "destination", "time_interval", "demand", "min_cost"]
    ].drop_duplicates()
    denominator = (
        (denominator_df["demand"] * denominator_df["min_cost"])
        .groupby(denominator_df["episode"])
        .sum()
    )

    return numerator / denominator


def generate_demand_odt():
    agents_od = pd.read_parquet(AGENTS_OD)
    demand_odt = (
        agents_od.groupby(["origin", "destination", "time_interval"])
        .size()
        .reset_index(name="count")
    )
    demand_odt.to_parquet(DEMAND_ODT)


#####
# Helper functions
#####
def generate_time_intervals_table(end_time, time_interval):
    """
    Called once per program execution.
    Create a table that contains time interval | start time | end time
    """
    starts = list(range(0, end_time, time_interval))
    ends = [min(s + time_interval, end_time) for s in starts]
    df = pd.DataFrame(
        {"interval": range(len(starts)), "start_time": starts, "end_time": ends}
    )

    df.to_parquet(TIMES_INTERVAL)


def generate_trips_odt_file():
    """
    Called once per program execution.
    Writes to an xml file, the grid of combinations odt.
    It will be passed as input to duarouter. So that time dependence shortest paths can be computed
    """
    time_intervals_table = pd.read_parquet(TIMES_INTERVAL)
    agents_ods = pd.read_parquet(AGENTS_OD)
    unique_ods = (
        agents_ods[["origin", "destination"]].drop_duplicates().reset_index(drop=True)
    )
    unique_ods = list(unique_ods.itertuples(index=False, name=None))

    with open(TRIPS_TDSP, "w") as f:

        f.write("<routes>\n")

        i = 0

        for _, interval_row in time_intervals_table.iterrows():

            depart = interval_row["start_time"] + 1

            for origin, destination in unique_ods:

                f.write(
                    f'\t<trip id="t{i}" '
                    f'from="{origin}" '
                    f'to="{destination}" '
                    f'depart="{depart}"/>\n'
                )

                i += 1

        f.write("</routes>\n")


def __run_duarouter(network, trips_file, routes_file, weights_file, seed):
    cmd = [
        "duarouter",
        "-n",
        network,
        "--route-files",
        trips_file,
        "--weight-files",
        weights_file,
        "--write-costs",
        "true",
        "-o",
        routes_file,
        "--seed",
        str(seed),
    ]

    subprocess.run(cmd, check=True)

    # Delete alternative route files (undesirable)
    alt_route_file_to_delete = routes_file.with_name(
        f"{routes_file.stem}.alt{routes_file.suffix}"
    )
    if alt_route_file_to_delete.exists():
        alt_route_file_to_delete.unlink()


def delete_files_DUE_convergence():
    """
    This folders may contain too many files
    """
    # Target folders
    TARGET_FOLDERS = [WEIGHTS_DIR, SHORTEST_PATHS_DIR]

    for folder in TARGET_FOLDERS:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.is_file():
                    item.unlink()
