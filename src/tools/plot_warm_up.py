"""
One-off tool: determines the minimum warm-up time needed for the transient phase
due to initial empty network to dissapear.

Runs one SUMO episode with calibrated demand (random routing), then plots
the number of vehicles in the network over time. The curve rises from zero
(empty network at t=0). Choose the smallest candidate cutoff (vertical
dashed line) after which the curve shows no upward trend.

Run with: python src/tools/plot_warm_up.py <config.yaml>
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.factory import initialize_agents, select_actions
from config.config import config
from config.paths import OUTPUT_PLOT_WARM_UP, TRIPS_INFO_XML
from demand_calibration.utils import demand_calibration
from simulation.environment import Environment
from simulation.scenario import Scenario

WARM_UP_CANDIDATES_MIN = [0, 5, 10, 15]
CANDIDATE_COLORS = ["gray", "orange", "green", "red"]


def _parse_depart_arrival():
    """
    Returns a list, in which each element it's a tuple that represents
    the depart and arrival time of each vehicle
    """
    tree = etree.parse(TRIPS_INFO_XML)
    trips = tree.xpath("//tripinfo")
    return [(float(t.get("depart")), float(t.get("arrival"))) for t in trips]


def main():
    # 0. Reproducibility
    rng = np.random.default_rng(config.seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    # 1. Calibrate demand (nº agents)
    agents, unique_ods = demand_calibration(last_iteration_gui=False)

    # 2. Create Scenario (files)
    scen = Scenario(
        map=config.network,
        agents=agents,
        unique_ods=unique_ods,
        seeds=seeds,
    )

    # 3. Create environment
    env = Environment(scenario=scen)

    # 4. Create agents
    agents = initialize_agents(scen=scen, seed=config.seed)

    # 5. Choose routes
    actions = select_actions(agents)

    # 6. Run episode
    episode = 1
    env.run_episode(actions, episode)

    # 7. Parse depart / arrival times
    trips = _parse_depart_arrival()

    # 8. Build time series: vehicles in network per second up to max warm-up time candidate
    max_warm_up_sec = max(WARM_UP_CANDIDATES_MIN) * 60
    times = np.arange(0, max_warm_up_sec + 1)
    vehicle_counts = np.array(
        [sum(1 for depart, arrival in trips if depart <= t < arrival) for t in times]
    )

    # 9. Plot
    network_name = Path(config.network).stem
    path = OUTPUT_PLOT_WARM_UP / f"warm_up_{network_name}.png"

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(times / 60, vehicle_counts, linewidth=1.5, color="steelblue")

    for warm_up_min, color in zip(WARM_UP_CANDIDATES_MIN, CANDIDATE_COLORS):
        ax.axvline(
            warm_up_min,
            linestyle="--",
            linewidth=1,
            color=color,
            label=f"{warm_up_min} min",
        )

    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Vehicles in network")
    ax.set_title(f"Vehicles in network over time  -  ({network_name})")
    ax.legend()

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
