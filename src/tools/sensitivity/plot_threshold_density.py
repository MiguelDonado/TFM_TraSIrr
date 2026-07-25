"""
One-off tool: sweeps a range of threshold_density values and plots the
final R-gap for each, to determine whether this imputation hyperparameter
meaningfully affects the obtained R-gap and, if so, which value minimises it.

threshold_density governs how missing cells in the average link travel time
table are imputed before TDSP computation. The table spans
(episode × edge × time_interval); cells are missing wherever no vehicle
traversed an edge in a given interval and episode. Two strategies exist:

  density > threshold_density  →  forward-fill from the previous interval
                                  (signal: congestion was present, recent
                                   observation is a better proxy than free-flow)
  density ≤ threshold_density  →  free-flow travel time
                                  (signal: edge was essentially empty, so
                                   free-flow is the appropriate cost)

A threshold of 0 means forward-fill is applied whenever any vehicle was
recorded on the edge in that interval; higher thresholds require stronger
congestion evidence before forward-fill is preferred over free-flow.

The metric plotted:

  Final R-gap — R-gap at the last training episode. Lower is better.
  A higher value means drivers collectively lose more time by not switching
  to their time-dependent shortest path.

Decision rule: Choose the threshold_density that yields the lowest final R-gap.
If the curve is flat, the hyperparameter has negligible impact and any value
(e.g. the default of 0) can be kept.

Final decision: 10
(R-gap varies substantially for threshold values below approximately 5 vehicles/km/lane.
Beyond 10 vehicles/km/lane, further increases had a negligible effect on the R-gap.)


Run with: python src/tools/sensitivity/plot_threshold_density.py <config.yaml>

Parameter dependencies: Independent hyperparameter
(The threshold_density parameter is considered an independent hyperparameter.
Although its impact on the computed R-gap depends on factors such as the temporal
aggregation interval, network congestion level, and the proportion of missing
observations, these factors only influence the frequency with which the
imputation rule is applied. They do not alter the decision rule itself)
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
from DUE_convergence.DUE_convergence import run_due_convergence_checks
from utils.generate_agents import demand_from_count
from utils.run_training_BM import run_full_training_BM

THRESHOLD_DENSITIES = [0, 1, 2, 5, 10, 20, 50]
# THRESHOLD_DENSITIES = [0, 2]


def main():

    # 0. Set-up
    DEMAND = 1000

    # 1. Calibrate demand (nº agents)
    calibrated_agents, unique_ods = demand_from_count(DEMAND)

    # 2. Compute BM r-gap table for given threshold_density
    run_full_training_BM(agents=calibrated_agents, unique_ods=unique_ods, due=False)

    # 3. Container
    last_rgaps = []

    # 4. Check r-gap
    for threshold in THRESHOLD_DENSITIES:
        print("\n##########")
        print(f"# threshold_density: {threshold}")

        # 5. Compute R-gap BM-algorithm
        run_due_convergence_checks(
            duaIterate=False,
            threshold_density=threshold,
        )

        # 6. Record final R-gap (last episode)
        last_rgap = pd.read_parquet(BM_PATHS.rgap).iloc[-1]["rgap"]
        last_rgaps.append(last_rgap)

    _make_plot(THRESHOLD_DENSITIES, last_rgaps, DEMAND)
    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


def _make_plot(thresholds, rgaps, demand):

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "threshold_density_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{demand}_{network_name}.png"

    # 2. Create figure
    plt.figure()

    # 3. Draw a line
    # Convert to categorical
    x = range(len(thresholds))
    plt.plot(x, rgaps, marker="o", linewidth=2)

    # 4. Improve visualization
    plt.xlabel("threshold_density (vehicles/km/lane)")
    plt.ylabel("Final R-gap")
    plt.title("Effect of threshold_density on final R-gap")
    plt.xticks(x, thresholds)
    plt.gca().yaxis.set_major_formatter(PercentFormatter())
    plt.grid(axis="y", alpha=0.3)

    # 5. Automatically adjust spacing
    plt.tight_layout()

    # 6. Save
    plt.savefig(path)


if __name__ == "__main__":
    main()
