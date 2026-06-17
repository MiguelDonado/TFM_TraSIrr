import gzip
import shutil
import subprocess
from collections import defaultdict

import pandas as pd
from lxml import etree
from utils.od_routes import od_routes_to_rows
from utils.sumo_xml import write_meandata_file

from config.config import config
from experiment import parse_edgedata, parse_trips_info, parse_vehroute
from paths import (
    AGENTS_OD,
    BASE_DIR,
    DEMAND_ODT,
    FREE_FLOW_TRAVEL_TIMES,
    TIMES_INTERVAL,
    TRIPS_DUEITERATE,
    TRIPS_TDSP,
)


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


def compute_travel_time_links_t_k(
    time_interval,
    network,
    threshold_density,
    output_file,
    agents_od_file,
    vehroute_file,
    edgedata_file,
    missingness_report_file,
    missingness_interval_file,
    missingness_edge_file,
    missingness_episode_file,
):
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
    df_edges = pd.read_parquet(vehroute_file)
    df_edges.rename(columns={"vehicle_id": "agent_id"}, inplace=True)

    # 4. Read agents_od to get departure_times of each agent
    df_agents_od = pd.read_parquet(agents_od_file)
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

    # 11. Create time interval
    time_intervals_table = pd.read_parquet(TIMES_INTERVAL)
    # Clamp to handle dueIterate case (some vehicles insertion is delayed, and so departure time is change a little bit, and some vehicles depart beyond 4200 sec,
    # and so it creates artificial intervals. We just change interval to which those vehicles belong, but their travel times and everything else remain equal
    max_interval = (time_intervals_table["interval"]).max()
    df_edges["time_interval"] = (df_edges["entry_time"] // delta_t).astype(int)
    df_edges["time_interval"] = df_edges["time_interval"].clip(upper=max_interval)

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

    ######################
    # Study of missingness
    ######################
    with open(missingness_report_file, "w") as f:

        # 1. Proportion of missing values
        prop_missing = avg_travel_time_links["travel_time"].isna().mean()
        f.write(f"Proportion of missing values: {prop_missing:.4f}\n")

        # 2. Total missing values
        total_missing = avg_travel_time_links["travel_time"].isna().sum()
        f.write(f"Total missing values: {total_missing}\n\n")

        df_missingness = avg_travel_time_links.copy()
        df_missingness["col_missing"] = df_missingness["travel_time"].isna().astype(int)

    # 3. Missingness by time interval
    # It may allow us to justify that most missingness occurs during sparse intervals
    missing_by_interval = (
        df_missingness.groupby("time_interval")["col_missing"].sum().reset_index()
    )
    missing_by_interval.to_parquet(missingness_interval_file, index=False)

    # 4. Missingness by edge
    # It may allow us to justify that most missingness occurs on low-traffic edges
    missing_by_edge = df_missingness.groupby("edge")["col_missing"].sum().reset_index()
    missing_by_edge.to_parquet(missingness_edge_file, index=False)

    # 5. Missingness by episode
    missing_by_episode = (
        df_missingness.groupby("episode")["col_missing"].sum().reset_index()
    )
    missing_by_episode.to_parquet(missingness_episode_file, index=False)

    ###############
    # GOTCHA LOGIC (FILL MISSING VALUES)
    ###############
    # 1. Read edgedata parquet (density edges by intervals)
    df_density = pd.read_parquet(edgedata_file)

    # Drop the "entered" column
    df_density = df_density.drop(columns=["entered"])

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
    df.to_parquet(output_file)


def generate_weights_xmls(cost_links, weights_dir):
    """
    Called once per program execution
    This function creates the xml file containing the time depedent costs of edges for each episode.
    It does so, for all episodes.
    It will be passed as input to duarouter. Determines the costs of edges that will be used when computing shortest paths
    """
    # 1. Load intervals table
    time_intervals_table = pd.read_parquet(TIMES_INTERVAL)

    # 2. Load avg travel time links table (episode, edge, time_interval, travel_time)
    df = pd.read_parquet(cost_links)

    # 3. Precompute interval lookup (creates a dictionary for fast lookup)
    interval_info = time_intervals_table.set_index("interval")[
        ["start_time", "end_time"]
    ].to_dict("index")

    # 4. Group dataframe once (instead of repeatedly filtering episode, interval...)
    """
    Conceptually:
    (episode=0, interval=0)
        -> dataframe chunk

    (episode=0, interval=1)
        -> dataframe chunk
    """
    grouped = df.groupby(["episode", "time_interval"])

    # 5. Loop episodes (one XML file per episode)
    for episode in df["episode"].unique():

        root = etree.Element("meandata")

        """
        k: key    
        v: value
        
        Suppose grouped keys are: 
        ep|time_interval
        (0,0)
        (0,1)
        (1,0)

        If episode = 0, then episode_groups =
        {
            0: df_for_interval_0,
            1: df_for_interval_1
        }
        """
        # Already filtered df
        episode_groups = {k[1]: v for k, v in grouped if k[0] == episode}

        # filtered_interval: All the edges weights for a particular time interval
        for interval_id, filtered_interval in episode_groups.items():

            begin = str(interval_info[interval_id]["start_time"])
            end = str(interval_info[interval_id]["end_time"])
            interval_xml = etree.SubElement(
                root, "interval", begin=begin, end=end, id="whatever"
            )

            for edge_row in filtered_interval.itertuples():
                etree.SubElement(
                    interval_xml,
                    "edge",
                    id=str(edge_row.edge),
                    traveltime=str(edge_row.travel_time),
                )

        output_file = weights_dir / f"Weights_episode_{episode}.xml"

        etree.ElementTree(root).write(
            output_file,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )


def compute_time_dependent_shortest_paths(
    network, seed, weights_dir, shortest_path_dir
):
    """
    This function computes the time dependent shortest path for all od and for all t
    """
    episodes = len([f for f in weights_dir.iterdir() if f.is_file()])
    for episode in range(1, episodes + 1):
        routes_file = shortest_path_dir / f"shortest_path_episode_{episode}.xml"
        weights_file = weights_dir / f"Weights_episode_{episode}.xml"
        __run_duarouter(network, TRIPS_TDSP, routes_file, weights_file, seed)


def compute_cost_min_paths_odt_k(time_interval, shortest_path_dir, cost_min_paths):
    """
    Computes the table that contains the cost for all time dependent shortest paths
    """
    rows = []

    for file in shortest_path_dir.iterdir():
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
    df.to_parquet(cost_min_paths)


def compute_rgap_and_refined_rgap(
    flow_paths,
    cost_paths,
    cost_min_paths,
    rgap_path,
    refined_rgap_path,
    rgap_by_od_path,
    refined_rgap_by_od_path,
):
    flow_df = pd.read_parquet(flow_paths)
    flow_df = flow_df.rename(columns={"count": "flow"})
    cost_df = pd.read_parquet(cost_paths)
    cost_df = cost_df.rename(columns={"avg_travel_time": "cost"})
    min_cost_df = pd.read_parquet(cost_min_paths)
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
    compute_rgap(df, rgap_path)
    compute_redefined_rgap(df, refined_rgap_path)

    # Compute rgap versions by od
    compute_rgap_by_od(df, rgap_by_od_path)
    compute_redefined_rgap_by_od(df, refined_rgap_by_od_path)


def _compute_rgap_generic(df, group_keys, output_col, output_path):
    df = df.copy()

    # Compute numerator rgap per episode
    df["gap_term"] = df["flow"] * (df["cost"] - df["min_cost"])
    numerator = df.groupby(group_keys)["gap_term"].sum()

    # Compute denominator rgap per episode
    # Demand is duplicated. For each episode, origin, destination, time_interval -> demand is duplicated across paths (duplicated path times)
    denom_df = df[
        ["episode", "origin", "destination", "time_interval", "demand", "min_cost"]
    ].drop_duplicates()

    denominator = (
        (denom_df["demand"] * denom_df["min_cost"])
        .groupby([denom_df[k] for k in group_keys])
        .sum()
    )

    result = (numerator / denominator).reset_index(name=output_col)
    result.to_parquet(output_path)


def compute_rgap(df, rgap_path):
    _compute_rgap_generic(df, ["episode"], "rgap", rgap_path)


def compute_redefined_rgap(df, refined_rgap_path):
    """
    Like rgap but for each interval
    """
    _compute_rgap_generic(
        df, ["episode", "time_interval"], "refined_rgap", refined_rgap_path
    )


def compute_rgap_by_od(df, rgap_by_od_path):
    """
    Compute relative gap (rgap) for each episode and OD pair
    """
    _compute_rgap_generic(
        df, ["episode", "origin", "destination"], "rgap", rgap_by_od_path
    )


def compute_redefined_rgap_by_od(df, refined_rgap_by_od_path):
    """
    Compute redefined rgap, for each episode, OD pair and time interval
    """
    _compute_rgap_generic(
        df,
        ["episode", "origin", "destination", "time_interval"],
        "refined_rgap",
        refined_rgap_by_od_path,
    )


def generate_demand_odt():
    """
    This method basically generates a table that contains the demand for each od for all time intervals
    """
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
    Writes to an xml file, the grid of combinations od and t.
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


def delete_files_DUE_convergence(weights_dir, shortest_paths_dir):
    """
    This folders may contain too many files
    """
    # Target folders
    TARGET_FOLDERS = [weights_dir, shortest_paths_dir]

    for folder in TARGET_FOLDERS:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.is_file():
                    item.unlink()


#####################
#####################
# DUEITERATE
#####################
#####################
def generate_trips_file_duaIterate(agents):
    with open(TRIPS_DUEITERATE, "w") as f:
        f.write(f"<routes>\n")
        for i, agent in enumerate(agents):
            f.write(
                f"""\t<trip id="{agent["id"]}" from="{agent["origin"]}" to="{agent["destination"]}" depart="{agent["departure_time"]}"/>\n"""
            )
        f.write("</routes>\n")


def call_dueIterate(network, max_iterations):
    cmd = [
        "duaIterate.py",
        "-n",
        network,
        "-t",
        TRIPS_DUEITERATE,
        "--last-step",
        str(max_iterations),
        "sumo--step-length",
        "0.1",
        "sumo--vehroute-output",
        "vehroute.xml",
        "sumo--vehroute-output.exit-times",
        "true",
    ]

    subprocess.run(cmd, check=True)


def run_simulation_dueIterate(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)
    path_config_file = BASE_DIR / folder_number / f"iteration_{folder_number}.sumocfg"
    cmd = ["sumo-gui", "-c", path_config_file]
    subprocess.run(cmd, check=True)


def delete_dueIterate_folders(max_iterations):
    target_numbers = [str(number).zfill(3) for number in range(max_iterations)]

    for number in target_numbers:
        path_to_delete = BASE_DIR / number
        shutil.rmtree(path_to_delete)


def extract_routes_file_dueIterate(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration dueIterate
    folder_path = BASE_DIR / folder_number

    # Path of gzip file that contains routes generated from dueIterate
    gzip_path = folder_path / f"trips_dueIterate_{folder_number}.rou.xml.gz"

    # Path of xml file that contains routes generated from dueIterate
    xml_path = folder_path / f"trips_dueIterate_{folder_number}.rou.xml"

    # Decompress gzip file to get xml file with routes generated from dueIterate
    __decompress_gzip(gzip_path, xml_path)

    return xml_path


def __decompress_gzip(gzip_path, xml_path):
    """
    Decompress a gzip file
    """
    with gzip.open(gzip_path, "rb") as f_in:
        with open(xml_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


def compute_od_routes_table_dueIterate(routes_file, output_file):
    """
    This function computes the od routes table used during computation Rgap
    """
    # Dictionary with agents_id as keys, and routes (list of edges) as values
    dict_agent_routes = __parse_routes(routes_file)

    # Extract all routes used by agents (route = all its edges)
    all_routes = dict_agent_routes.values()

    # Get unique routes (route = all its edges)
    unique_routes = __get_unique_routes(all_routes)

    # Build od_routes dictionary
    od_routes = __build_od_routes_dict(unique_routes)

    # Put od_routes in right format to store in parquet file
    processed_od_routes = __process_od_routes(od_routes)

    df = pd.DataFrame(processed_od_routes)
    df.to_parquet(output_file, engine="pyarrow")

    return dict_agent_routes, od_routes


def __parse_routes(routes_file):
    """
    Returns a dictionary that contains:
    - keys: agents_id
    - values: route (list with all the edges)
    """
    document = routes_file
    tree = etree.parse(document)

    # Routes
    vehicles = tree.xpath("//vehicle")
    agents_id = [vehicle.xpath("@id")[0] for vehicle in vehicles]
    routes = [vehicle.xpath("route/@edges")[0] for vehicle in vehicles]
    edges = [route.split(" ") for route in routes]

    # Check
    assert len(edges) == len(agents_id)

    return dict(zip(agents_id, edges))


def __get_unique_routes(routes):
    unique_routes = [list(x) for x in set(tuple(inner) for inner in routes)]
    return unique_routes


def __build_od_routes_dict(unique_routes):
    # Initialize dictionary that will store as keys unique ods, and as values a list with all the used routes for that od
    od_routes = defaultdict(list)
    for route in unique_routes:
        od = (route[0], route[-1])
        od_routes[od].append(route)
    return od_routes


def __process_od_routes(od_routes):
    """
    I want this format
    origin | dest | route_id | step | edge
    A         B      1          1       e1
    A         B      1          2       e5 ...
    """
    return od_routes_to_rows(od_routes)


def compute_actions_table_dueIterate(agents, dict_agent_routes, od_routes, output_file):
    """
    Compute actions table used during Rgap computation
    """
    actions = []

    for agent in agents:
        agent_id = agent["id"]
        od = (agent["origin"], agent["destination"])
        route = dict_agent_routes[agent_id]
        idx_route = od_routes[od].index(route)
        actions.append({"episode": 1, "agent_id": agent_id, "action": idx_route})

    df = pd.DataFrame(actions)
    df.to_parquet(output_file, engine="pyarrow")


def process_trips_info_dueiterate(max_iterations, output_file):
    """
    Builds the processed trips info file
    """
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration dueIterate
    folder_path = BASE_DIR / folder_number

    # Raw trips info path
    trips_info_dueiterate_path = folder_path / f"tripinfo_{folder_number}.xml"

    # Parse trips info
    processed_data = parse_trips_info(
        episode=1, trips_info_path=trips_info_dueiterate_path
    )

    # Save trips info processed data in a parquet file
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")


def process_vehroute_dueIterate(max_iterations, output_file):
    """
    Builds the processed vehroute file
    """
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration dueIterate
    folder_path = BASE_DIR / folder_number

    # Raw vehroutes path
    vehroute_path = folder_path / "vehroute.xml"

    # Parse vehroutes
    processed_data = parse_vehroute(episode=1, vehroute_path=vehroute_path)

    # Save vehroutes processed data in a parquet file
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")


def generate_meandata_file(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration dueIterate
    folder_path = BASE_DIR / folder_number

    path = folder_path / "meandata_dueiterate.xml"

    write_meandata_file(path, "../edgedata_dueiterate.xml", config.time_interval)

    return path


def generate_edgedata_file(max_iterations, meandata_dueiterate_file):
    folder_number = _last_iteration_folder(max_iterations)
    path_config_file = BASE_DIR / folder_number / f"iteration_{folder_number}.sumocfg"

    tree = etree.parse(path_config_file)

    # Find and remove the additional-files element
    for elem in tree.xpath("//additional-files"):
        elem.getparent().remove(elem)

    tree.write(
        path_config_file, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )

    cmd = [
        "sumo",
        "-c",
        path_config_file,
        "--additional-files",
        meandata_dueiterate_file,
    ]

    subprocess.run(cmd, check=True)


def process_edgedata_file(max_iterations, output_file):
    """
    Builds the processed vehroute file
    """
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration dueIterate
    folder_path = BASE_DIR / folder_number

    # Raw edgedata path
    edgedata_path = folder_path / "edgedata_dueiterate.xml"

    # Parse edgedata
    processed_data = parse_edgedata(episode=1, edgedata_path=edgedata_path)

    # Save vehroutes processed data in a parquet file
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")


def _last_iteration_folder(max_iterations: int):
    """
    Return zero-padded folder name for the last dueIterate iteration.
    """
    return str(max_iterations - 1).zfill(3)


def _load_actions_and_agents(actions_path):
    df_actions = pd.read_parquet(actions_path)
    df_actions.rename(columns={"action": "path"}, inplace=True)
    df_agents_od = pd.read_parquet(AGENTS_OD)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)
    return df_actions, df_agents_od
