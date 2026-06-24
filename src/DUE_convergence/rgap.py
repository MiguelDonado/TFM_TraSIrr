"""
R-gap computation and its variants for DUE convergence assessment.

R-gap formula
-------------
          Σ_{o,d,t,p} f_{odtp} · (c_{odtp} − c*_{odt})
R-gap =  ────────────────────────────────────────────────
          Σ_{o,d,t} d_{odt} · c*_{odt}

where:
  f_{odtp}  — flow on path p for OD (o,d) departing at interval t
  c_{odtp}  — average travel time on path p
  c*_{odt}  — minimum travel time (time-dependent shortest path)
  d_{odt}   — demand for OD (o,d) at interval t

R-gap = 0 if and only if the assignment is at Dynamic User Equilibrium.

R-gap variants (differ only in the grouping keys)
--------------------------------------------------
  rgap                — per episode (aggregate convergence signal)
  refined_rgap        — per episode × time interval (temporal heterogeneity)
  rgap_by_od          — per episode × OD pair (spatial heterogeneity)
  refined_rgap_by_od  — per episode × OD pair × time interval

References
----------
Linares Herreros, María Paz, and Jaime Barceló Bugeda.
    ‘A Mesoscopic Traffic Simulation Based Dynamic Traffic Assignment’.
    Universitat Politècnica de Catalunya, 2014.
    https://doi.org/10.5821/dissertation-2117-95313.
    Pag. 131-132.
"""

import pandas as pd

from config.paths import AGENTS_OD, DEMAND_ODT, TIMES_INTERVAL, TRIPS_TDSP


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
    _compute_rgap(df, rgap_path)
    _compute_redefined_rgap(df, refined_rgap_path)

    # Compute rgap versions by od
    _compute_rgap_by_od(df, rgap_by_od_path)
    _compute_redefined_rgap_by_od(df, refined_rgap_by_od_path)


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


def _compute_rgap(df, rgap_path):
    _compute_rgap_generic(df, ["episode"], "rgap", rgap_path)


def _compute_redefined_rgap(df, refined_rgap_path):
    """
    Like rgap but for each interval
    """
    _compute_rgap_generic(
        df, ["episode", "time_interval"], "refined_rgap", refined_rgap_path
    )


def _compute_rgap_by_od(df, rgap_by_od_path):
    """
    Compute relative gap (rgap) for each episode and OD pair
    """
    _compute_rgap_generic(
        df, ["episode", "origin", "destination"], "rgap", rgap_by_od_path
    )


def _compute_redefined_rgap_by_od(df, refined_rgap_by_od_path):
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
