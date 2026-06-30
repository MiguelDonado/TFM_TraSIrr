"""
One-off tool: sweeps a range of demand levels, measures the congestion
metric for each, and plots the result.

Useful for understanding how the network responds to different demands
before choosing a calibration target, and to gain insights about adequacy
of the congestion metric

Run with: python src/tools/plot_congestion_metric.py <config.yaml>
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Workaround paths when import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.config import config
from config.paths import OUTPUT_PLOT_CONGESTION_METRIC
from demand_calibration.demand_calibration import DemandCalibration
from utils.generate_agents import generate_agents
from utils.generate_free_flow_tt import generate_free_flow_tt_links

# CONSTANTS
SEED = 42
DEMANDS = range(100, 2500, 100)


def main():
    # -----------------------------
    # 0. DEMAND CALIBRATION
    # -----------------------------
    result = []
    for demand in DEMANDS:
        # Every iteration gets a fresh rng starting from the same point
        rng = np.random.default_rng(SEED)
        demand_warmup = int(demand * config.warm_up_time / config.end_time)
        demand_post_warmup = demand - demand_warmup
        agents, _ = generate_agents(demand_warmup, demand_post_warmup, rng)

        demand_calibration = DemandCalibration(config.network, agents)
        congestion_metric_value = demand_calibration.compute_congestion_metric()
        result.append(
            {"demand": demand, "congestion_metric": congestion_metric_value},
        )

    # -----------------------------
    # 1. PLOT
    # -----------------------------
    network_name = Path(config.network).stem
    path = OUTPUT_PLOT_CONGESTION_METRIC / f"congestion_metric_{network_name}.png"

    demands = [r["demand"] for r in result]
    congestion_metric_values = [r["congestion_metric"] for r in result]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(demands, congestion_metric_values, marker="o", linewidth=2, markersize=4)

    ax.set_xlabel("Demand (vehicles)")
    ax.set_ylabel("Congestion metric")
    ax.set_title(f"Congestion metric vs demand  -  ({network_name})")
    ax.legend()

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
