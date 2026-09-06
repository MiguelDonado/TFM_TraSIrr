"""
One-off tool: sweeps a range of n_routes_per_od values and plots three metrics
used to select the best value.

n_routes_per_od controls how many alternative routes each OD pair has available
during learning. More routes give agents greater flexibility but enlarge the action
space, which may slow convergence.

Three metrics are plotted:

  1) First-episode R-gap — measures route-set quality before learning starts.
     Expected relationship: higher n_routes_per_od yields a higher initial
     R-gap, since traffic starts out spread across a larger, potentially
     worse route set.

  2) Final R-gap — measures route-choice quality at convergence. Lower is better.
     Expected relationship: higher n_routes_per_od yields lower R-gap, though
     diminishing returns are more likely in low-congestion networks.

  3) Episodes to convergence — measures learning speed. Lower is better.
     Expected relationship: larger action spaces require more exploration,
     so convergence should slow as n_routes_per_od grows.

After checking the plot, hypothesis 3 is confirmed; hypothesis 2 is not —
increasing n_routes_per_od does not produce a monotonic decrease in final
R-gap in all congestion regimes. Hypothesis 1 is confirmed

Decision rule: A high initial R-gap that the algorithm subsequently reduces
is a desirable and illustrative property of the experiment. We therefore
choose the n_routes_per_OD that produces a high initial R-gap and a lower
final R-gap, without increasing exaggerately the number of episodes
required for convergence.

Final decision: 8

###########################
Usage:
###########################

Run the sensitivity analysis and generate the plot:
python src/tools/sensitivity/plot_n_routes_per_OD.py <config.yaml>

Generate the plot using previously saved results:
python src/tools/sensitivity/plot_n_routes_per_OD.py <config.yaml> --plot-only



The --plot-only option reads the results stored in
SENSITIVITY_RESULTS_DIR/n_routes_per_OD.csv and generates the plot without
running the training simulations.

Parameter dependencies: Its effect on the initial R-gap depends on
random_factor. Raising n_routes_per_OD only has an effect once random_factor
is high enough to actually find that many alternative routes per OD — below
that threshold, the requested count is simply not reached. Given a
sufficiently high random_factor, more routes per OD raises the first-episode
R-gap, since traffic is then split across a larger, potentially worse route
set.
"""

import subprocess
import sys

PLOT_ONLY = "--plot-only" in sys.argv

if PLOT_ONLY:
    sys.argv.remove("--plot-only")

from pathlib import Path

import matplotlib.pyplot as plt

plt.style.use(Path(__file__).parent / "thesis_style.mplstyle")
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
    N_ROUTES_PER_OD = list(range(2,10))

    # Plot only from stored results
    if PLOT_ONLY:
        results = pd.read_csv(
            SENSITIVITY_RESULTS_DIR / "n_routes_per_OD.csv"
        )

        _make_plot(
            n_routes = results["n_routes_per_od"].tolist(),
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

        # 2. Calibrate demand (nº agents)
        calibrated_agents, unique_ods = demand_from_count(demand)

        # 3. Analyze different hyperparameter values
        for n in N_ROUTES_PER_OD:

            print("##########")
            print(f"# N routes per OD: {n}")
            print("##########")

            orchestrate_training(
                agents=calibrated_agents, unique_ods=unique_ods, k=n
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
            n_routes=N_ROUTES_PER_OD,
            first_rgaps=first_rgaps,
            last_rgaps=last_rgaps,
            episodes=episodes_to_converge,
            demand = demand
        )

        _make_plot(
            n_routes=N_ROUTES_PER_OD,
            first_rgaps=first_rgaps,
            last_rgaps=last_rgaps,
            episodes=episodes_to_converge,
            demand=demand,
        )

    # Play sound to signal end of script
    subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])

def save_results(n_routes, first_rgaps, last_rgaps, episodes, demand):
    results = pd.DataFrame({
        "n_routes_per_od": n_routes,
        "first_r_gap": first_rgaps,
        "final_r_gap": last_rgaps,
        "episodes_to_convergence": episodes,
        "demand": demand,
    })

    results.to_csv(
        SENSITIVITY_RESULTS_DIR / f"n_routes_per_OD.csv",
        index=False,
    )


def _make_plot(n_routes, first_rgaps, last_rgaps, episodes, demand):

    fontsize = 8

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "n_routes_per_OD_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{demand}_{network_name}.png"

    fig, ax1 = plt.subplots()

    # Convert to categorical
    x = range(len(n_routes))

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
        x,
        last_rgaps,
        color=color_final,
        marker="o",
        linewidth=2,
        label="Final R-gap",
    )

    ax1.set_xlabel("Number of alternative routes per OD", fontsize=fontsize)
    ax1.set_xticks(x)
    ax1.set_xticklabels(n_routes)
    ax1.set_ylabel("R-gap", fontsize=fontsize)
    ax1.yaxis.set_major_formatter(PercentFormatter())

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

    # 4. Legend on the right
    lines = line1 + line2 + line3
    labels = [line.get_label() for line in lines]

    ax1.legend(
        lines,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.2),
        ncol = 3,
        frameon=False,
        fontsize=6
    )

    ax1.tick_params(axis="both", labelsize=7)
    ax2.tick_params(axis="y", labelsize=7)

    # 5. Improve visualization
    plt.title(
        f"Effect of the Number of Alternative Routes per OD "
        f"(demand = {demand})"
    )

    ax1.grid(True, alpha=0.25)

    # Leave space for the legend on the right
    fig.tight_layout()

    plt.savefig(path, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
