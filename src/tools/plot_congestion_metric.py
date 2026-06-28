import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Workaround paths when import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.config import config
from config.paths import OUTPUT_PLOT_CONGESTION_METRIC
from demand_calibration.demand_calibration import DemandCalibration
from utils.get_free_flow_speed import get_free_flow_speed

# CONSTANTS
SEED = 42
MAX_ATTEMPS = 20
DEMANDS = range(100, 3000, 100)


def main():

    # Compute once the free flow speed of the network
    free_flow_speed = get_free_flow_speed(config.network)

    # -----------------------------
    # 0. DEMAND CALIBRATION
    # -----------------------------
    result = []
    for demand in DEMANDS:
        demand_calibration = DemandCalibration(
            config.network, demand, free_flow_speed, SEED
        )
        speed_ratio = demand_calibration.compute_congestion_ratio()
        result.append(
            {"demand": demand, "speed_ratio": speed_ratio},
        )

    # -----------------------------
    # 1. PLOT
    # -----------------------------
    demands = [r["demand"] for r in result]
    speed_ratios = [r["speed_ratio"] for r in result]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(demands, speed_ratios, marker="o", linewidth=2, markersize=4)

    ax.set_xlabel("Demand (vehicles)")
    ax.set_ylabel("Speed ratio (avg speed / free flow speed)")
    ax.set_title("Congestion metric vs demand")
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUTPUT_PLOT_CONGESTION_METRIC, dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
