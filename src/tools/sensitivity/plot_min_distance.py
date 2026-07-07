"""
One-off tool: sweeps a range of min_distance_factor (α) values and plots the
distribution of free-flow travel times of the resulting OD shortest paths for each.
The minimum distance constraint is: α × network diagonal.

A low α admits short-trip OD pairs. A high α over-constrains the OD pool,
reducing the number of valid pairs until none can be found at the extreme.
The plot makes the trade-off visible so α can be fixed before running experiments.

Final decision: α = 0.8

Run with: python src/tools/sensitivity/plot_min_distance.py <config.yaml>

Parameter dependencies: Independent hyperparameter
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Workaround paths when import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.config import config
from config.paths import SENSITIVITY_PLOTS_DIR
from demand_calibration.demand_calibration import DemandCalibration
from utils.generate_agents import generate_agents


def main():

    # 0. Initial setup
    MIN_DISTANCE_FACTORS = np.arange(0.1, 0.9, 0.1)
    DEMAND = 1000
    demand_warmup = int(DEMAND * config.warm_up_time / config.end_time)
    demand_post_warmup = DEMAND - demand_warmup

    # 1. Reproducibility
    rng = np.random.default_rng(config.seed)

    # 2. Containers
    all_fftts = []
    labels = []
    counts = []

    for min_distance_factor in MIN_DISTANCE_FACTORS:

        print("\n##########")
        print(f"# Results using min_distance_factor: {min_distance_factor}")
        print("##########")

        # 1. Generate agents objects
        agents, _ = generate_agents(
            demand_warmup, demand_post_warmup, rng, min_distance_factor
        )

        # 2. Compute ff tt shortest paths
        demand_calibration = DemandCalibration(config.network, agents)

        # 3. Collect free-flow travel times
        free_flow_travel_times_short_paths = list(
            demand_calibration.od_min_paths_ff_tt.values()
        )

        # 4. Store fftt correspondent to current min_distance_factor
        all_fftts.append(free_flow_travel_times_short_paths)

        # 5. Get number of distinct OD generated
        n = len(free_flow_travel_times_short_paths)
        counts.append(n)

        labels.append(f"{min_distance_factor:.1f}")

    ##########
    # Plot
    ##########

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "min_distance_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{network_name}.png"

    # 2. Create figure (width of 10 inches and height of 6 inches)
    plt.figure(figsize=(10, 6))

    # 3. Draw a boxplot
    plt.boxplot(all_fftts, tick_labels=labels)

    # 4. Find largest travel time across all boxplots
    # This value will be used as the vertical position for the annotations
    y = max(max(x) for x in all_fftts)
    y = y + 2

    # 5. Annotate number of distinct OD found (config sets as max 10 ods)
    for i, n in enumerate(counts, start=1):
        plt.text(i, y, f"n={n}", ha="center", fontsize=9)

    # 6. Improve visualization
    plt.xlabel("α (minimum distance = α × network diagonal)")
    plt.ylabel("Free-flow shortest-path travel time (s)")
    plt.title(f"Distribution of free-flow shortest-path travel times ({network_name})")
    plt.grid(axis="y", alpha=0.3)

    # Automatically adjust spacing
    plt.tight_layout()

    # 7. Save
    plt.savefig(path, dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
