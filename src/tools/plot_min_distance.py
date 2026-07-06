"""
One-off tool: sweeps a range of min_distance_factor values, plots the distribution
of free-flow travel times of the resulting OD shortest paths for each.

Useful for choosing a min_distance_factor that produces realistically long trips
without over-constraining the OD pool.

Run with: python src/tools/plot_min_distance.py <config.yaml>
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Workaround paths when import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.config import config
from config.paths import OUTPUT_PLOT_MIN_DISTANCE
from demand_calibration.demand_calibration import DemandCalibration
from utils.generate_agents import generate_agents


def main():

    # 0. Initial setup
    MIN_DISTANCE_FACTORS = np.arange(0.1, 0.9, 0.1)
    demand = 1000
    demand_warmup = int(demand * config.warm_up_time / config.end_time)
    demand_post_warmup = demand - demand_warmup
    rng = np.random.default_rng(config.seed)

    all_fftts = []
    labels = []
    counts = []

    for min_distance_factor in MIN_DISTANCE_FACTORS:

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

        all_fftts.append(free_flow_travel_times_short_paths)

        n = len(free_flow_travel_times_short_paths)
        counts.append(n)

        labels.append(f"{min_distance_factor:.1f}")

    # 4. Boxplot
    network_name = Path(config.network).stem

    plt.figure(figsize=(10, 6))
    plt.boxplot(all_fftts, tick_labels=labels)

    y = max(max(x) for x in all_fftts)

    for i, n in enumerate(counts, start=1):
        plt.text(i, y, f"n={n}", ha="center", fontsize=9)

    plt.xlabel("α (minimum distance = α × network diagonal)")
    plt.ylabel("Free-flow shortest-path travel time (s)")
    plt.title(f"Distribution of free-flow shortest-path travel times ({network_name})")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    # Save
    path = OUTPUT_PLOT_MIN_DISTANCE / f"min_distance_{network_name}.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()
    # Optional
    plt.close()


if __name__ == "__main__":
    main()
