"""
One-off tool: sweeps a range of max_od_space values and plots three metrics
used to select the best value.

max_od_space controls the maximum number of different OD pairs that the
OD matrix will have. A priori, it is not easy to guess which effects it will have
on the first r-gap, the last r-gap or on the episodes to convergence.

Three metrics are plotted:

  1) First-episode R-gap 
  2) Final R-gap
  3) Episodes to convergence

Decision rule: A high initial R-gap that the algorithm subsequently reduces
is a desirable and illustrative property of the experiment. We therefore
choose the max_od_space that produces a high initial R-gap and a lower
final R-gap, without excessively increasing the number of episodes
required for convergence.

Final decision: 

Run with: python src/tools/sensitivity/plot_max_od_space.py <config.yaml>

Parameter dependencies: Independent hyperparameter
"""

import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import PercentFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.config import config
from config.paths import BM_PATHS, SENSITIVITY_PLOTS_DIR
from utils.generate_agents import demand_from_count
from utils.run_training_BM import run_full_training_BM


def main():
    # 0. Set-up
    DEMANDS = [2000]
    MAX_OD_SPACE_LIST = list(range(5,55,5))

    for demand in DEMANDS:
        print("##########")
        print(f"# Demand: {demand}")
        print("##########")

        # 1. Containers (metric values)
        last_rgaps = []
        episodes_to_converge = []
        first_rgaps = []

        # 2. Analyze different hyperparameter values
        for max_od_space in MAX_OD_SPACE_LIST:

            config.max_size_od_space = max_od_space

            # 3. Calibrate demand (nº agents)
            calibrated_agents, unique_ods = demand_from_count(demand)


            print("##########")
            print(f"# Max number of OD pairs: {max_od_space}")
            print("##########")

            run_full_training_BM(
                agents=calibrated_agents, unique_ods=unique_ods
            )

            # 4. Get values of metrics (first episode, last episode and its r-gap)
            rgap_df = pd.read_parquet(BM_PATHS.rgap)
            first_rgap = rgap_df.iloc[0]["rgap"]
            last_row = rgap_df.iloc[-1]
            last_episode = last_row["episode"]
            last_rgap = last_row["rgap"]

            # 5. Store metrics values relative to current hyperparameter value
            last_rgaps.append(last_rgap)
            episodes_to_converge.append(last_episode)
            first_rgaps.append(first_rgap)

        _make_plot(
            max_od_space=MAX_OD_SPACE_LIST,
            first_rgaps=first_rgaps,
            last_rgaps=last_rgaps,
            episodes=episodes_to_converge,
            demand=demand,
        )

    # Play sound to signal end of script
    subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])

def _make_plot(max_od_space, first_rgaps, last_rgaps, episodes, demand):
    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "max_OD_space_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{demand}_{network_name}.png"

    _, ax1 = plt.subplots()
    # Convert to categorical
    x = range(len(max_od_space))

    # 2. Left y-axis: R-gap (first and final episode)
    line1 = ax1.plot(
        x,
        first_rgaps,
        color="tab:blue",
        marker="^",
        linewidth=2,
        linestyle=":",
        label="First-episode R-gap",
    )
    line2 = ax1.plot(
        x, last_rgaps, color="tab:blue", marker="o", linewidth=2, label="Final R-gap"
    )
    ax1.set_xlabel("Maximum number of OD pairs")
    ax1.set_xticks(x)
    ax1.set_xticklabels(max_od_space)
    ax1.set_ylabel("R-gap", color="tab:blue")
    ax1.tick_params(axis="y", colors="tab:blue")

    # 3. Right y-axis: Episodes until convergence
    ax2 = ax1.twinx()
    line3 = ax2.plot(
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
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    # Put legend above the plot
    ax1.legend(
        lines,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
        frameon=False,
    )
    plt.title(f"Effect of the Maximum number of OD pairs (demand = {demand})")
    ax1.grid(True, alpha=0.25)
    ax1.yaxis.set_major_formatter(PercentFormatter())
    plt.tight_layout()
    plt.savefig(path)


if __name__ == "__main__":
    main()
