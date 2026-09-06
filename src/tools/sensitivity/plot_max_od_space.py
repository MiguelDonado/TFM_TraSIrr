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

Final decision: 10

###########################
Usage:
###########################

Run the sensitivity analysis and generate the plot:
python src/tools/sensitivity/plot_max_od_space.py <config.yaml>

Generate the plot using previously saved results:
python src/tools/sensitivity/plot_max_od_space.py <config.yaml> --plot-only

The --plot-only option reads the results stored in
SENSITIVITY_RESULTS_DIR/max_od_space.csv and generates the plot without
running the training simulations.

Parameter dependencies: May depend on the traffic demand and network topology, 
as these determine how vehicles are distributed and the extent to which they 
compete for shared network resources.
"""

import subprocess
import sys

PLOT_ONLY = "--plot-only" in sys.argv

if PLOT_ONLY:
    sys.argv.remove("--plot-only")

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import PercentFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.config import config
from config.paths import BM_PATHS, SENSITIVITY_PLOTS_DIR, SENSITIVITY_RESULTS_DIR
from utils.generate_agents import demand_from_count
from utils.run_training_BM import orchestrate_training


def main():
    # 0. Set-up
    DEMANDS = [2000]
    MAX_OD_SPACE_LIST = list(range(5,55,5))

    # Plot only from stored results
    if PLOT_ONLY:
        results = pd.read_csv(
            SENSITIVITY_RESULTS_DIR / "max_od_space.csv"
        )

        _make_plot(
            max_od_space = results["max_od_space"].tolist(),
            first_rgaps = results["first_r_gap"].tolist(),
            last_rgaps = results["final_r_gap"].tolist(),
            episodes = results["episodes_to_convergence"].tolist(),
            demand = DEMANDS[0],
        )

        return 

    # Run sensitivity analysis

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

            orchestrate_training(
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

        save_results(
            max_od_space=MAX_OD_SPACE_LIST,
            first_rgaps=first_rgaps,
            last_rgaps=last_rgaps,
            episodes=episodes_to_converge,
            demand = demand
        )

        _make_plot(
            max_od_space=MAX_OD_SPACE_LIST,
            first_rgaps=first_rgaps,
            last_rgaps=last_rgaps,
            episodes=episodes_to_converge,
            demand=demand,
        )

    # Play sound to signal end of script
    subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])

def save_results(max_od_space, first_rgaps, last_rgaps, episodes, demand):
    results = pd.DataFrame({
        "max_od_space": max_od_space,
        "first_r_gap": first_rgaps,
        "final_r_gap": last_rgaps,
        "episodes_to_convergence": episodes,
        "demand": demand,
    })

    results.to_csv(
        SENSITIVITY_RESULTS_DIR / f"max_od_space.csv",
        index=False,
    )

def _make_plot(max_od_space, first_rgaps, last_rgaps, episodes, demand):

    fontsize = 8

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "max_OD_space_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{demand}_{network_name}.png"

    _, ax1 = plt.subplots()
    # Convert to categorical
    x = range(len(max_od_space))

    # Colors
    color_first = "#404040"     # dark gray
    color_final = "#808080"     # medium gray
    color_episodes = "#B0B0B0"  # light gray

    # 2. Left y-axis: R-gap (first and final episode)
    line1 = ax1.plot(
        x,
        first_rgaps,
        color=color_first,
        marker="^",
        linewidth=2,
        linestyle=":",
        label="First-episode R-gap",
    )
    line2 = ax1.plot(
        x, last_rgaps, color=color_final, marker="o", linewidth=2, label="Final R-gap"
    )
    ax1.set_xlabel("Maximum number of OD pairs", fontsize=fontsize)
    ax1.set_xticks(x)
    ax1.set_xticklabels(max_od_space)
    ax1.set_ylabel("R-gap", fontsize=fontsize)

    # 3. Right y-axis: Episodes until convergence
    ax2 = ax1.twinx()
    line3 = ax2.plot(
        x,
        episodes,
        color=color_episodes,
        marker="s",
        linewidth=2,
        linestyle="--",
        label="Episodes to convergence",
    )
    ax2.set_ylabel("Episodes until convergence", fontsize=fontsize)

    # 4. Improve visualization
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    # Put legend above the plot
    ax1.legend(
        lines,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=3,
        frameon=False,
        fontsize = 6
    )

    ax1.tick_params(axis="both", labelsize=7)
    ax2.tick_params(axis="y", labelsize=7)

    plt.title(f"Effect of the Maximum number of OD pairs (demand = {demand})")
    ax1.grid(True, alpha=0.25)
    ax1.yaxis.set_major_formatter(PercentFormatter())
    plt.tight_layout()
    plt.savefig(path)


if __name__ == "__main__":
    main()
