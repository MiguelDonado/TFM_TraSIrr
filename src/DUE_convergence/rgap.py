"""
R-gap computation and its variants for DUE convergence assessment.

The R-gap requires exactly three tables:

  1. flows_odtp_k          — agents choosing each path (p), per OD (od), interval (t), episode (k)
  2. costs_paths_odtp_k    — agents' average travel time on each path (p), per OD (od), interval (t), episode (k)
  3. cost_min_paths_odt_k  — time-dependent shortest path cost per OD (od), interval (t), episode (k) (from TDSP pipeline)


R-gap formula
-------------
          Σ_{o,d,t,p} f_{odtp} · (c_{odtp} − c*_{odt})
R-gap =  ────────────────────────────────────────────────
          Σ_{o,d,t} d_{odt} · c*_{odt}

where:
  f_{odtp}  — flow on path p for OD (o,d) departing at interval t
  c_{odtp}  — average travel time on path p departing at interval t
  c*_{odt}  — minimum travel time (time-dependent shortest path) for OD (o,d) departing at interval t
  d_{odt}   — demand for OD (o,d) at interval t

R-gap = 0 if and only if the assignment is at Dynamic User Equilibrium.

R-gap variants (differ only in the grouping keys)
--------------------------------------------------
  rgap                — per episode (aggregate convergence signal)
  refined_rgap        — per episode × time interval (temporal heterogeneity)
  rgap_by_od          — per episode × OD pair (spatial heterogeneity)
  refined_rgap_by_od  — per episode × OD pair × time interval

Numerator: total extra cost incurred by not routing all drivers on shortest paths.
Denominator: total cost if all drivers pick shortest paths — normalises the gap so
it is dimensionless and comparable across networks and demand levels.
R-gap = 0.20 means drivers experienced, on average, travel costs 20 % above the
time-dependent shortest-path cost.

Sources of inaccuracy
---------------------
The dominant source of inaccuracy is time aggregation. The avg link travel time
table stores one mean cost per (edge, interval), so every vehicle departing within
the same interval is assumed to face the same shortest path. In reality congestion
changes continuously: a vehicle leaving at 8:02 may have a different optimal route
than one leaving at 8:09. The larger the interval, the less precise the edge-cost
estimates and the less accurate the resulting shortest paths.

  Example: two vehicles use the same edge in interval t. The first experiences
  5 min, the second 20 min. The table records 12.5 min. If the interval were
  split, the first vehicle’s edge cost would be 5 min and the edge would appear
  in its shortest path; the second’s would be 20 min and the edge might not.
  Aggregating over the full interval distorts both.

Why the R-gap can be negative
------------------------------
If c*_{odt} is overestimated (due to the aggregation above), the term
(c_{odtp} − c*_{odt}) can become negative for vehicles whose actual cost is below
the aggregated "shortest path" cost. The sum across all vehicles can then be
negative even when drivers took the true shortest path.

  Example: vehicle 1 took the true shortest path of 20 min; vehicle 2 took
  the true shortest path of 60 min. Both depart in the same interval and the
  aggregated c*_{odt} = 45 min.

    Accurate:   (20−20)·1 + (60−60)·1 =   0
    Aggregated: (20−45)·1 + (60−45)·1 = −10

  The R-gap is negative despite both drivers being at equilibrium.

Why time aggregation can violate FIFO
--------------------------------------
Aggregating travel times over an interval can make the link cost table
non-FIFO: a vehicle entering an edge later may exit earlier than one that
entered before it, which is physically impossible but can appear in the
aggregated data.

  Example: in interval t, the first vehicle traverses an edge in 80 s and the
  last vehicle traverses it in 20 s (congestion clearing). The table records
  50 s for interval t. In interval t+1 all vehicles take 20 s, so the table
  records 20 s.

  Now suppose vehicle A enters the edge at t=28 s (interval t) and vehicle B
  enters at t=30 s (interval t+1):

    A exits at: 28 + 50 = 78 s
    B exits at: 30 + 20 = 50 s

  B exits before A despite entering later — FIFO is violated. Smaller
  intervals reduce this effect by making each bucket more homogeneous.

When edge costs are temporally aggregated, the estimated shortest path is itself
only an approximation of the true shortest path experienced by each individual
vehicle. Consequently, the computed R-gap captures not only the actual network
disequilibrium but also an approximation error introduced by temporal aggregation.
As the assignment interval widens, this error grows because a wider range of
traffic conditions is collapsed into a single travel time.

References
----------
Linares Herreros, María Paz, and Jaime Barceló Bugeda.
    ‘A Mesoscopic Traffic Simulation Based Dynamic Traffic Assignment’.
    Universitat Politècnica de Catalunya, 2014.
    https://doi.org/10.5821/dissertation-2117-95313.
    Pag. 131-132.
"""

import pandas as pd

from config.config import config
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

    result = ((numerator / denominator) * 100).reset_index(name=output_col)
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
    agents_od["time_interval"] = agents_od["departure_time"] // config.time_interval
    demand_odt = (
        agents_od.groupby(["origin", "destination", "time_interval"])
        .size()
        .reset_index(name="count")
    )
    demand_odt.to_parquet(DEMAND_ODT)


def generate_time_intervals_table():
    """
    Called once per program execution.
    Create a table that contains time interval | start time | end time
    """
    starts = list(range(0, config.end_time, config.time_interval))
    ends = [min(s + config.time_interval, config.end_time) for s in starts]
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

            if interval_row["start_time"] < config.warm_up_time:
                continue

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
