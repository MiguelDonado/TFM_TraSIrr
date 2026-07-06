"""
Evaluate the effect of the number of alternative routes per OD on route choice performance.

This script performs a sensitivity analysis of the `n_routes_per_od` hyperparameter.
Increasing the number of alternative routes gives agents greater routing flexibility,
which generally reduces the final R-gap. However, it also enlarges the reinforcement learning
action space, requiring more exploration and typically slowing convergence.

The script generates a dual-axis plot showing:
    - Final R-gap versus `n_routes_per_od`.
    - Episodes to convergence versus `n_routes_per_od`.

The resulting figure is used to select the smallest number of alternative routes
that achieves diminishing improvements in the final R-gap while avoiding a
substantial increase in convergence time.

Run:
    python src/tools/plot_n_routes_per_OD.py <config.yaml>
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.factory import initialize_agents
from config.config import config
from config.paths import BM_PATHS, OUTPUT_PLOT_N_ROUTES_PER_OD, POLICY_CHANGE_BM
from demand_calibration.utils import demand_calibration
from DUE_convergence.DUE_convergence import run_due_convergence_checks
from experiment import save_processed_data
from main import _run_training_loop
from simulation.environment import Environment
from simulation.scenario import Scenario

n_routes_per_od = [3, 5, 10]


def main():
    # Containers for metric values
    last_rgaps = []
    episodes_to_converge = []

    # Reproducibility
    rng = np.random.default_rng(config.seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    # Calibrate demand (nº agents)
    calibrated_agents, unique_ods = demand_calibration(last_iteration_gui=False)

    # Loop to get metric values for different hyperparameter values
    for n in n_routes_per_od:

        print(f"----- N routes per OD: {n} -----")

        # 1. Create Scenario (files)
        scen = Scenario(
            map=config.network,
            agents=calibrated_agents,
            unique_ods=unique_ods,
            seeds=seeds,
            k=n,
        )

        # 2. Create environment
        env = Environment(scenario=scen)

        # 3. Initialize agents
        rl_agents = initialize_agents(scen=scen, seed=config.seed)

        # -----------------------------
        # 4. TRAINING LOOP
        # -----------------------------
        results, policy_change_history = _run_training_loop(env=env, agents=rl_agents)

        # -----------------------------
        # 5. SAVE OUTPUT
        # -----------------------------
        save_processed_data(results)
        df_policy_change = pd.DataFrame(policy_change_history)
        df_policy_change.to_parquet(POLICY_CHANGE_BM)
        # -----------------------------
        # 6. CHECK DUE convergence
        # -----------------------------
        run_due_convergence_checks(
            scen=scen,
            end_time=config.end_time,
            time_interval=config.time_interval,
            duaIterate=False,
        )

        # Plot
        # 1. Get r-gap from last episode and number of last episode itself
        last_row = pd.read_parquet(BM_PATHS.rgap).iloc[-1]
        last_episode = last_row["episode"]
        last_rgap = last_row["rgap"]

        # 2. Store metric results hyperparameter value
        last_rgaps.append(last_rgap)
        episodes_to_converge.append(last_episode)

    _make_plot(n_routes_per_od, last_rgaps, episodes_to_converge)


def _make_plot(n_routes, rgaps, episodes):
    # Path
    network_name = Path(config.network).stem
    path = OUTPUT_PLOT_N_ROUTES_PER_OD / f"n_routes_per_od_{network_name}.png"

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # Left y-axis: R-gap
    line1 = ax1.plot(n_routes, rgaps, marker="o", linewidth=2, label="Final R-gap")
    ax1.set_xlabel("Number of alternative routes per OD")
    ax1.set_ylabel("Final R-gap")
    ax1.tick_params(axis="y")

    # Right y-axis: Episodes until convergence
    ax2 = ax1.twinx()
    line2 = ax2.plot(
        n_routes,
        episodes,
        marker="s",
        linewidth=2,
        linestyle="--",
        label="Episodes to convergence",
    )
    ax2.set_ylabel("Episodes until convergence")
    ax2.tick_params(axis="y")

    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="best")

    plt.title("Effect of the Number of Alternative Routes per OD")
    ax1.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
