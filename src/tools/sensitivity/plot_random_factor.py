"""
One-off tool: sweeps a range of random_factor values and plots two metrics used
to select the best value.

random_factor controls the weight-perturbation magnitude duarouter applies to the edge costs
when computing the shortest-path. Near 1, perturbation is negligible — repeated searches
return the same shortest path, so most ODs fall short of the k-route target. As the
value grows, route diversity increases and more OD pairs reach k routes, but paths
also lengthen, adding suboptimality to the route set.

Two metrics are plotted:

  5a) OD pairs reaching exactly k alternative routes — measures route-set completeness.
      Higher is better; the target is all OD pairs.

  5b) Mean of per-OD mean tt ratios (%), where ratio_i = ff_tt(route_i) / ff_tt(shortest path) − 1.
      Measures route-set suboptimality.

Decision rule: A high initial R-gap that the algorithm subsequently reduces
is a desirable and illustrative property of the experiment. We therefore
choose a random_factor at which metric 5a is maximised and
metric 5b is reasonably large.

Final decision: 50

Run with: python src/tools/sensitivity/plot_random_factor.py <config.yaml>

Parameter dependencies: The effect of this parameter on the R-gap—particularly 
during the early episodes—depends on n_routes_per_OD. When the alternative routes 
are suboptimal but still close to the shortest path, agents initially distribute 
themselves almost uniformly across a route set that is uniformly good, 
resulting in a low early R-gap. This effect is even more pronounced in 
grid-like networks such as Sioux Falls, where many feasible routes are 
already close to optimal.
Consequently, the quality distribution of the generated route set largely determines 
the initial R-gap: the poorer the routes included in the set, the higher the early R-gap. 
Increasing r-andom_factor promotes greater route diversity, making it more likely 
that the route set contains a mix of both good and poor routes rather than only near-optimal ones.

The influence of n_routes_per_OD follows naturally from this. As the number 
of routes per OD pair increases, so does the probability of including lower-quality routes 
in the route set. During the first episodes, when agents are still exploring, traffic is therefore 
spread over a larger number of suboptimal routes, leading to a higher initial R-gap.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

plt.style.use(Path(__file__).parent / "thesis_style.mplstyle")
import numpy as np
from matplotlib.ticker import PercentFormatter

# Workaround paths when import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.config import config
from config.paths import SENSITIVITY_PLOTS_DIR
from simulation.scenario import Scenario
from utils.generate_agents import demand_from_count
from utils.route_tt_ratio import compute_route_tt_ratios


def main():

    # Set-up
    random_factors = [1.25, 2, 5, 10, 25, 50, 100, 1000]

    # 0. Reproducibility
    rng = np.random.default_rng(config.seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    # 1. Calibrate demand (nº agents)
    agents, unique_ods = demand_from_count(config.n_agents)

    # 2. Containers
    all_n_ods_with_k_routes = []
    all_avg_tt_ratios = []

    for random_factor in random_factors:

        print("\n\n##########")
        print(f"# Random factor: {random_factor}")
        # 3. Compute k routes with given random_factor
        scen = Scenario(
            map=config.network,
            agents=agents,
            unique_ods=unique_ods,
            seeds=seeds,
            random_factor=random_factor,
        )

        # 4. Log
        for od, routes in scen.od_routes.items():
            print(od, len(routes))

        # 5. Compute number of OD pairs that achieved relevant metrics
        # a) Number of OD pairs that achieved exactly k alternative routes
        n_ods_with_k_routes = sum(
            len(routes) == config.n_routes_per_OD for routes in scen.od_routes.values()
        )

        # b) (optional) Avg tt ratio
        # ratio_i = ff_tt(route_i) / ff_tt(shortest_route_for_that_OD)
        ratios_by_od = compute_route_tt_ratios(scen.od_routes)
        avg_tt_ratio = 100 * (
            np.mean([np.mean(ratios) for ratios in ratios_by_od.values() if ratios]) - 1
        )

        all_n_ods_with_k_routes.append(n_ods_with_k_routes)
        all_avg_tt_ratios.append(avg_tt_ratio)

    ##########
    # 1st PLOT
    ##########

    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "random_factor_"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{network_name}.png"

    # 2. Create figure (width of 10 inches and height of 6 inches)
    plt.figure()

    # 3. Draw a line
    # Convert to categorical
    x = range(len(random_factors))
    plt.plot(
        x,
        all_n_ods_with_k_routes,
        marker="o",
        linewidth=2,
    )

    # 4. Improve visualization
    plt.xlabel("Random factor")
    plt.ylabel(f"OD pairs with all {config.n_routes_per_OD} alternative routes found")
    plt.title(
        "Effect of random factor on alternative route generation "
        f"(total OD pairs = {len(unique_ods)})"
    )
    plt.xticks(x, random_factors)
    plt.grid(axis="y", alpha=0.3)

    # Automatically adjust spacing
    plt.tight_layout()

    # 7. Save
    plt.savefig(path)

    ##########
    # 2nd PLOT
    ##########
    # 1. Manage path
    network_name = Path(config.network).stem
    plot_prefix = "random_factor_2nd"
    path = SENSITIVITY_PLOTS_DIR / f"{plot_prefix}{network_name}.png"

    # 2. Create figure (width of 10 inches and height of 6 inches)
    plt.figure()

    # 3. Draw a line
    # Convert to categorical
    x = range(len(random_factors))
    plt.plot(
        x,
        all_avg_tt_ratios,
        marker="o",
        linewidth=2,
    )

    # 4. Improve visualization
    plt.xlabel("Random factor")
    plt.ylabel("Average OD travel time ratio")
    plt.title("Effect of random factor on route set quality")
    ax = plt.gca()
    ax.yaxis.set_major_formatter(PercentFormatter())

    plt.xticks(x, random_factors)
    plt.grid(axis="y", alpha=0.3)

    # Automatically adjust spacing
    plt.tight_layout()

    # 7. Save
    plt.savefig(path)


if __name__ == "__main__":
    main()
