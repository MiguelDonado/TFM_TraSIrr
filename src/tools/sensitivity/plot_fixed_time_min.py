"""
One-off tool: sweeps a range of fixed_time_min values and plots, for each
demand scenario, the full R-gap convergence curve and the aggregate
missingness of the average link travel time table, to determine whether
this aggregation hyperparameter meaningfully affects the R-gap and, if
so, which value to choose.

fixed_time_min is an hyperparameter that affects the computation of
the r-gap. It does not alter the MARL algorithm, only the r-gap evaluation.
It governs the width of the time intervals used to
aggregate edge travel times and to assign departure-interval labels to agents.
It enters the R-gap computation through two competing effects:

  Smaller interval  →  higher temporal resolution and more accurate
                        average travel-time estimates, but fewer
                        observations per cell, leading to more missing
                        values and therefore more imputation.
  Larger interval   →  denser observations per cell (fewer missing values
                        and less imputation), but greater temporal
                        aggregation resulting in less accurate travel-time estimates.

Metrics plotted (one figure per demand scenario):

  R-gap convergence  — full R-gap curve across episodes, one line per
                       fixed_time_min candidate.

  Missingness (%)    — proportion of missing cells in the average link
                       travel time table (episode × edge × time_interval),
                       one point per candidate.

Within the range of intervals considered, improving the temporal
accuracy of the travel-time estimates has a larger positive effect on
the R-gap than the negative effect introduced by the additional
imputation. However, when the interval becomes excessively small, the
amount of missing data starts to dominate.

The candidate intervals were explored progressively, starting from
coarse intervals (minutes) and refining the search towards shorter
intervals (seconds) once the general trend had been identified.

Decision rule:
Select the smallest interval whose R-gap curve remains as close to zero
as possible while avoiding frequent negative R-gap values and taking into account
the trade-off with missing values. If two candidates produce similar R-gap curves,
prefer the one that generates fewer missing values.

Final decision:
30 seconds (0.5 minutes).

Run with: python src/tools/sensitivity/plot_fixed_time_min.py <config.yaml>

Parameter dependencies: fixed_time_min interacts with network size (more
edges → more potential missing cells) and traffic demand (higher demand →
denser observations, and potentially less missing values because we have more
vehicles in the network).
"""

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt

plt.style.use(Path(__file__).parent / "thesis_style.mplstyle")
import pandas as pd
from matplotlib.ticker import PercentFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.config import config
from config.paths import BM_PATHS, SENSITIVITY_PLOTS_DIR
from utils.generate_agents import demand_from_count
from utils.run_training_BM import run_full_training_BM

FIXED_TIME_MIN_CANDIDATES = [
    5 / 60,  # 5 s
    10 / 60,  # 10 s
    15 / 60,  # 15 s
    30 / 60,  # 30 s
]
DEMANDS = [1000, 1500, 1750, 2000]


def main():

    # 0. For each demand check r-gap and missingess for different time intervals
    total = len(DEMANDS) * len(FIXED_TIME_MIN_CANDIDATES)
    i = 0
    for demand in DEMANDS:

        # 1. Calibrate demand (nº agents)
        calibrated_agents, unique_ods = demand_from_count(demand)

        # 2. Containers
        rgap_curves = {}
        missingness_props = {}

        # 3. Re-run full BM training once per candidate. Route choices themselves
        # don't depend on fixed_time_min, but SUMO's edgedata density (used by the
        # r-gap's TDSP imputation) is aggregated *during simulation* over
        # config.time_interval, so it has to be re-measured fresh for every
        # candidate rather than reused from a single shared run.
        for fixed_time_min in FIXED_TIME_MIN_CANDIDATES:

            # 3b. Log (progress and current combination)
            i += 1
            print(f"\n--- [{i}/{total}] demand={demand} fixed_time_min={fixed_time_min} ---\n")

            # 4. Update the time interval globally so all downstream functions use it
            # We also convert it to seconds
            config.time_interval = int(fixed_time_min * 60)

            # 5. Run full BM training and compute R-gap/missingness for this time interval
            run_full_training_BM(
                agents=calibrated_agents,
                unique_ods=unique_ods,
                due=True,
                save_output=False,
            )

            # 6. Record full R-gap convergence curve
            rgap_curves[fixed_time_min] = pd.read_parquet(BM_PATHS.rgap)["rgap"]

            # 7. Record aggregate missingness proportion
            missingness_props[fixed_time_min] = _parse_missingness_proportion(
                BM_PATHS.missingness_report
            )

        # 9. Make plot for some demand value
        _make_plot(rgap_curves, missingness_props, demand)

    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


def _parse_missingness_proportion(report_file):
    with open(report_file) as f:
        for line in f:
            if line.startswith("Proportion missing:"):
                return float(line.split(":")[1].strip())


def _make_plot(rgap_curves, missingness_props, demand):

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "fixed_time_min_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{demand}_{network_name}.png"

    # 2. Create figure with two side-by-side subplots (left subplot bigger)
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={"width_ratios": [2, 1]})

    # 3. Left subplot: R-gap convergence curves (one per candidate)
    # R-gap is stored as a percentage (e.g. 20.0 means 20 %)
    for fixed_time_min, rgap_series in rgap_curves.items():
        ax1.plot(
            rgap_series.index,
            rgap_series.values,
            linewidth=1.5,
            label=f"{fixed_time_min} min",
        )

    # 4. Improve visualization
    ax1.set_xlabel("Episode")
    ax1.set_ylabel("R-gap")
    ax1.set_title(f"R-gap convergence by time interval (demand = {demand})")
    ax1.yaxis.set_major_formatter(PercentFormatter())
    ax1.legend(title="Time interval")
    ax1.grid(axis="y", alpha=0.3)

    # 5. Right subplot: aggregate missingness per candidate
    # Missingness is stored as a fraction in [0, 1]
    candidates = list(missingness_props.keys())
    props = list(missingness_props.values())
    x = range(len(candidates))
    ax2.plot(x, props, marker="o", linewidth=2, color="C1")

    # 6. Improve visualization
    ax2.set_xlabel("Time interval (minutes)")
    ax2.set_ylabel("Missing cells")
    ax2.set_title(f"Missingness of avg link travel time table (demand = {demand})")
    ax2.set_xticks(x)
    ax2.set_xticklabels(candidates)
    ax2.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    ax2.grid(axis="y", alpha=0.3)

    # 7. Automatically adjust spacing
    plt.tight_layout()

    # 8. Save
    plt.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    main()
