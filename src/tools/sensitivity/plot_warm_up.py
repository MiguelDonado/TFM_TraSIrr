"""
One-off tool to determine the minimum warm-up time required for the
initial transient caused by starting the simulation from an empty network
to disappear.

Context
-------
The simulation always starts with an empty network. Consequently, the
first vehicles experience unrealistically good traffic conditions (no
queues and little or no congestion), making them unrepresentative of the
steady operating conditions of interest.

A warm-up period is therefore introduced so that only vehicles entering
after the network has reached a representative traffic state are
evaluated.

Methodology
-----------
For each representative demand level:

1. Generate the agents
2. Run only the first SUMO episode using a random routing policy.
3. Compute the number of vehicles in the network every second and plot the resulting curve
4. Select the smallest warm-up candidate after which the initial
   increasing trend associated with the network filling process has
   disappeared.

Only the first episode is analyzed because it isolates the transient
caused by starting from an empty network. In later episodes, changes in
the occupancy curve may also reflect improvements in the learned routing
policy, making the initialization transient more difficult to interpret.

Metric
------
The number of vehicles in the network is used because it directly
captures the phenomenon that motivates the warm-up. Since the network
starts empty, the occupancy curve provides the most direct indication of
when the initial filling transient has ended.

Final decision
--------------
A warm-up time of 5 minutes was selected because it is the smallest
candidate after which all considered demand scenarios exhibit a
stable occupancy level rather than the initial increasing trend.

Dependencies
------------
The required warm-up time depends on:
- traffic demand,
- network topology.
- vehicle departure schedule (uniform in all experiments).

Run
---
python src/tools/sensitivity/plot_warm_up.py <config.yaml>
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.style.use(Path(__file__).parent / "thesis_style.mplstyle")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lxml import etree

from config.config import config
from config.paths import SENSITIVITY_PLOTS_DIR, TRIPS_INFO_XML
from utils.generate_agents import demand_from_count
from utils.run_training_BM import run_single_episode_BM


def _parse_depart_arrival():
    """
    Returns a list, in which each element it's a tuple that represents
    the depart and arrival time of each vehicle
    """
    tree = etree.parse(TRIPS_INFO_XML)
    trips = tree.xpath("//tripinfo")
    return [(float(t.get("depart")), float(t.get("arrival"))) for t in trips]


def main():

    # 0. Set-up
    WARM_UP_CANDIDATES_MIN = [0, 5, 10, 15]  # minutes
    DEMANDS = [1000, 1500, 1750, 2000]

    # 1. Container
    demand_curves = {}

    for demand in DEMANDS:

        print("\n##########")
        print(f"# Demand {demand}")
        print("##########")

        # 2. Calibrate demand (nº agents)
        calibrated_agents, unique_ods = demand_from_count(demand)

        # 3. Run first episode (random routing policy) and generate
        # new tripinfo output
        run_single_episode_BM(agents=calibrated_agents, unique_ods=unique_ods)

        # 4. Parse depart / arrival times
        trips = _parse_depart_arrival()

        # 5. Build time series: vehicles in network per second up to max warm-up time candidate
        max_warm_up_sec = max(WARM_UP_CANDIDATES_MIN) * 60
        times = np.arange(0, max_warm_up_sec + 1)
        vehicle_counts = np.array(
            [
                sum(1 for depart, arrival in trips if depart <= t < arrival)
                for t in times
            ]
        )

        demand_curves[demand] = vehicle_counts

    _make_plot(times, demand_curves, WARM_UP_CANDIDATES_MIN)


def _make_plot(times, demand_curves, warm_up_candidates):

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "warm_up_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{network_name}.png"

    # 2. Create figure
    fig, ax = plt.subplots()

    # 3. One curve per demand
    for demand, vehicle_counts in demand_curves.items():
        ax.plot(
            times / 60,
            vehicle_counts,
            linewidth=1.5,
            label=f"Demand = {demand}",
        )

    # 4. Draw vertical candidate lines + labels
    y_top = ax.get_ylim()[1]

    for warm_up_min in warm_up_candidates:
        ax.axvline(
            x=warm_up_min,
            color="0.7",  # 0=black, 1=white
            linestyle="--",
            linewidth=1,
            zorder=0,  # Draw behind the curves
        )

        ax.text(
            warm_up_min,
            y_top * 0.98,
            f"{warm_up_min} min",
            ha="center",
            va="top",
            fontsize=9,
            color="0.5",
        )

    # 5. Improve visualization
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Vehicles in network")
    ax.set_title(f"Vehicles in network over time ({network_name})")
    ax.legend()

    # 6. Automatically adjust spacing
    plt.tight_layout()

    # 7. Save
    plt.savefig(path)


if __name__ == "__main__":
    main()
