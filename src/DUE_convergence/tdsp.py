"""
Link travel time + TDSP generation
"""

import pandas as pd
from lxml import etree

from config.config import config
from paths import FREE_FLOW_TRAVEL_TIMES, TIMES_INTERVAL, TRIPS_TDSP

from .aggregation import _load_network_edges
from .duaiterate import run_duarouter


def _compute_edge_travel_times(
    vehroute_file, agents_od_file, time_interval
) -> pd.DataFrame:
    delta_t = time_interval

    # 1. Read vehroute file (travel time edges)
    df_edges = pd.read_parquet(vehroute_file)
    df_edges.rename(columns={"vehicle_id": "agent_id"}, inplace=True)

    # 2. Read agents_od to get departure_times of each agent
    df_agents_od = pd.read_parquet(agents_od_file)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)

    # 3. Merge
    df_edges = df_edges.merge(
        df_agents_od[["agent_id", "departure_time"]], on="agent_id", how="left"
    )
    # 4. Sort, is not needed, but just in case to make sure
    df_edges = df_edges.sort_values(["episode", "agent_id", "exit_times"])

    # 5. Compute entry time (entry time 2nd edge = exit time 1st edge)
    df_edges["entry_time"] = df_edges.groupby(["episode", "agent_id"])[
        "exit_times"
    ].shift(1)

    # 6. Fill first edge correctly = departure time
    # The first edge for each vehicle and episode, I cannot assume that entry time is 0
    # because vehicles have different departure times.
    df_edges["entry_time"] = df_edges["entry_time"].fillna(df_edges["departure_time"])
    df_edges = df_edges.drop("departure_time", axis=1)

    # 7. Compute travel time
    df_edges["travel_time"] = df_edges["exit_times"] - df_edges["entry_time"]

    # 8. Check travel times on links are OK.
    assert (df_edges["travel_time"] >= 0).all()

    # 9. Create time interval
    time_intervals_table = pd.read_parquet(TIMES_INTERVAL)
    # Clamp to handle duaIterate case (some vehicles insertion is delayed, and so departure time is change a little bit, and some vehicles depart beyond 4200 sec,
    # and so it creates artificial intervals. We just change interval to which those vehicles belong, but their travel times and everything else remain equal
    max_interval = (time_intervals_table["interval"]).max()
    df_edges["time_interval"] = (df_edges["entry_time"] // delta_t).astype(int)
    df_edges["time_interval"] = df_edges["time_interval"].clip(upper=max_interval)
    return df_edges


def _build_full_grid(df_edges, all_edges):
    # 1. Compute avg travel times on links (per episode, edge and time interval)
    avg_tt = df_edges.groupby(["episode", "edge", "time_interval"])[
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
    return avg_tt.reindex(full_index).reset_index()


def _save_missingness_report(
    avg_tt: pd.DataFrame,
    missingness_report_file,
    missingness_interval_file,
    missingness_edge_file,
    missingness_episode_file,
):
    ######################
    # Study of missingness
    ######################
    df = avg_tt.copy()
    df["col_missing"] = df["travel_time"].isna().astype(int)
    with open(missingness_report_file, "w") as f:
        f.write(f"Proportion missing: {df['col_missing'].mean():.4f}\n")
        f.write(f"Total missing: {df['col_missing'].sum()}\n")

    # 1. Missingness by time interval
    # It may allow us to justify that most missingness occurs during sparse intervals
    missing_by_interval = df.groupby("time_interval")["col_missing"].sum().reset_index()
    missing_by_interval.to_parquet(missingness_interval_file, index=False)

    # 2. Missingness by edge
    # It may allow us to justify that most missingness occurs on low-traffic edges
    missing_by_edge = df.groupby("edge")["col_missing"].sum().reset_index()
    missing_by_edge.to_parquet(missingness_edge_file, index=False)

    # 3. Missingness by episode
    missing_by_episode = df.groupby("episode")["col_missing"].sum().reset_index()
    missing_by_episode.to_parquet(missingness_episode_file, index=False)


def _fill_missing_travel_times(
    avg_tt, edgedata_file, all_edges, threshold_density
) -> pd.DataFrame:
    # 1. Generate file with free flow travel times of all links in the network and load it
    free_flow = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)

    ###############
    # GOTCHA LOGIC (FILL MISSING VALUES)
    ###############
    # 1. Read edgedata parquet (density edges by intervals)
    df_density = pd.read_parquet(edgedata_file)
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
    df = avg_tt.merge(df_full, on=["episode", "time_interval", "edge"], how="left")
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
    mask_ffill = df["travel_time"].isna() & (df["density"] > threshold_density)
    # Apply forward fill (only where mask true, replace travel_time with forward filled value)
    # .loc[rows,columns] It selects rows and columns
    df.loc[mask_ffill, "travel_time"] = df.loc[mask_ffill, "ffill"]

    ###############
    # Missing values. Free flow travel time
    ###############

    # Add free_flow travel time columns
    df = df.merge(free_flow[["edge", "free_flow_travel_time"]], on="edge", how="left")
    # For leftover NaN values that are still present after applying fill forward, use free flow travel times
    mask_fft = df["travel_time"].isna()
    df.loc[mask_fft, "travel_time"] = df.loc[mask_fft, "free_flow_travel_time"]
    return df.drop(["density", "ffill", "free_flow_travel_time"], axis="columns")


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
        run_duarouter(network, TRIPS_TDSP, routes_file, weights_file, seed)


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


def run_tdsp_pipeline(
    time_interval,
    vehroute_file,
    edgedata_file,
    agents_od_file,
    missingness_edge_file,
    missingness_episode_file,
    missingness_interval_file,
    missingness_report_file,
    cost_links,
    weights_dir,
    shortest_path_dir,
    cost_min_paths,
):
    # 4. TIME DEPENDENCE SHORTEST PATH
    # 4.1. Compute avg link travel time for all time intervals across all episodes
    compute_travel_time_links_t_k(
        time_interval=time_interval,
        network=config.network,
        threshold_density=config.threshold_density,
        output_file=cost_links,
        agents_od_file=agents_od_file,
        vehroute_file=vehroute_file,
        edgedata_file=edgedata_file,
        missingness_edge_file=missingness_edge_file,
        missingness_episode_file=missingness_episode_file,
        missingness_interval_file=missingness_interval_file,
        missingness_report_file=missingness_report_file,
    )
    # 4.2. Transform the parquet travel time links file into a XML file for duarouter TDSP
    generate_weights_xmls(cost_links=cost_links, weights_dir=weights_dir)
    # 4.3. Compute the time dependence shortest paths
    compute_time_dependent_shortest_paths(
        config.network,
        config.seed,
        weights_dir=weights_dir,
        shortest_path_dir=shortest_path_dir,
    )
    # 4.4. Compute cost time dependence shortest paths for all time intervals and for all episodes
    compute_cost_min_paths_odt_k(
        time_interval=time_interval,
        cost_min_paths=cost_min_paths,
        shortest_path_dir=shortest_path_dir,
    )
    # 4.5. Delete some files generated on due convergence check
    delete_files_due_convergence(
        weights_dir=weights_dir, shortest_paths_dir=shortest_path_dir
    )


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
    all_edges = _load_network_edges(network)
    df_edges = _compute_edge_travel_times(
        vehroute_file=vehroute_file,
        agents_od_file=agents_od_file,
        time_interval=time_interval,
    )
    avg_tt = _build_full_grid(df_edges, all_edges)
    _save_missingness_report(
        avg_tt,
        missingness_report_file,
        missingness_interval_file,
        missingness_edge_file,
        missingness_episode_file,
    )
    df_filled = _fill_missing_travel_times(
        avg_tt, edgedata_file, all_edges, threshold_density
    )
    df_filled.to_parquet(output_file)


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


def delete_files_due_convergence(weights_dir, shortest_paths_dir):
    """
    This folders may contain too many files
    """
    # Target folders
    folders_to_clear = [weights_dir, shortest_paths_dir]

    for folder in folders_to_clear:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.is_file():
                    item.unlink()
