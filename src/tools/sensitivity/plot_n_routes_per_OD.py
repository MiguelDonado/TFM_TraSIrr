"""
One-off tool: sweeps a range of n_routes_per_od values and plots two metrics used
to select the best value.

n_routes_per_od controls how many alternative routes each OD pair has available
during learning. More routes give agents greater flexibility but enlarge the action
space, which may slow convergence.

Two metrics are plotted:

  1) Final R-gap — measures route-choice quality at convergence. Lower is better.
     Expected relationship: higher n_routes_per_od yields lower R-gap, though
     diminishing returns are more likely in low-congestion networks.

  2) Episodes to convergence — measures learning speed. Lower is better.
     Expected relationship: larger action spaces require more exploration,
     so convergence should slow as n_routes_per_od grows.

After checking the plot, hypothesis 2 is confirmed; hypothesis 1 is not —
increasing n_routes_per_od does not produce a monotonic decrease in R-gap in all
congestion regimes.

Decision rule: Choose the smallest n_routes_per_od that achieves a near-minimum R-gap
under both low- and high-congestion conditions without substantially increasing
the number of episodes required for convergence.

Final decision: 3

Run with: python src/tools/sensitivity/plot_n_routes_per_OD.py <config.yaml>

Parameter dependencies: Depends on the value of the congestion metric.
"""

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt

plt.style.use(Path(__file__).parent / "thesis_style.mplstyle")
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.config import config
from config.paths import BM_PATHS, SENSITIVITY_PLOTS_DIR
from utils.generate_agents import demand_from_count
from utils.run_training_BM import run_full_training_BM


def main():
    # 0. Set-up
    DEMANDS = [1300, 2000]
    N_ROUTES_PER_OD = list(range(2,10))

    for demand in DEMANDS:
        print("##########")
        print(f"# Demand: {demand}")
        print("##########")

        # 1. Containers (metric values)
        last_rgaps = []
        episodes_to_converge = []

        # 2. Calibrate demand (nº agents)
        calibrated_agents, unique_ods = demand_from_count(demand)

        # 3. Analyze different hyperparameter values
        for n in N_ROUTES_PER_OD:

            print("##########")
            print(f"# N routes per OD: {n}")
            print("##########")

            run_full_training_BM(
                agents=calibrated_agents, unique_ods=unique_ods, k=n
            )

            # 4. Get values of metrics (last episode and its r-gap)
            last_row = pd.read_parquet(BM_PATHS.rgap).iloc[-1]
            last_episode = last_row["episode"]
            last_rgap = last_row["rgap"]

            # 5. Store metrics values relative to current hyperparameter value
            last_rgaps.append(last_rgap)
            episodes_to_converge.append(last_episode)

        _make_plot(
            n_routes=N_ROUTES_PER_OD,
            rgaps=last_rgaps,
            episodes=episodes_to_converge,
            demand=demand,
        )
    # Play sound to signal end of script
    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


def _make_plot(n_routes, rgaps, episodes, demand):
    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "n_routes_per_OD_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{demand}_{network_name}.png"

    fig, ax1 = plt.subplots()
    # Convert to categorical
    x = range(len(n_routes))

    # 2. Left y-axis: R-gap
    line1 = ax1.plot(
        x, rgaps, color="tab:blue", marker="o", linewidth=2, label="Final R-gap"
    )
    ax1.set_xlabel("Number of alternative routes per OD")
    ax1.set_xticks(x)
    ax1.set_xticklabels(n_routes)
    ax1.set_ylabel("Final R-gap", color="tab:blue")
    ax1.tick_params(axis="y", colors="tab:blue")

    # 3. Right y-axis: Episodes until convergence
    ax2 = ax1.twinx()
    line2 = ax2.plot(
        x,
        episodes,
        color="tab:orange",
        marker="s",
        linewidth=2,
        linestyle="--",
        label="Episodes to convergence",
    )
    ax2.set_ylabel("Episodes until convergence", color="tab:orange")
    ax2.tick_params(axis="y", colors="tab:orange")

    # 4. Improve visualization
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    # Put legend above the plot
    ax1.legend(
        lines,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=2,
        frameon=False,
    )
    plt.title(f"Effect of the Number of Alternative Routes per OD (demand = {demand})")
    ax1.grid(True, alpha=0.25)
    ax1.yaxis.set_major_formatter(PercentFormatter())
    plt.tight_layout()
    plt.savefig(path)


if __name__ == "__main__":
    main()
