"""
Calibrates the number of agents needed to achieve a target congestion
level on the network before starting the training with those agents in
the Multi Agent Reinforcement Learning setting.

Congestion metric
-----------------


Two-phase procedure
-------------------
1. Initial guess
       n_agents = heuristic_veh_km_hour × total_lengthtarget_congestion_metric_km × hours
   Provides a starting point without running any simulation.

2. Calibration loop
   Runs SUMO iteratively, using as demand the current number of agents
   and adjusting n_agents after each simulation:

       error         = target_congestion_metric - observed_congestion_ratio
       update_factor = clip(1 + k_demand_calib × error, 0.6, 1.4)
       n_agents      = int(n_agents × update_factor)

   Large errors produce aggressive corrections; smaller errors produce smoother
   corrections, helping convergence.
   The clip to [0.6, 1.4] prevents overshooting on the first iterations.
   Stops when |error| < tolerance_demand_calibration.

Returns
-------
demand_calibration() → (agents, unique_ods)
   agents      — final agent list from the converged iteration, passed
                 directly to Scenario so training uses the same OD matrix
   unique_ods  — unique (origin, dest) pairs in the OD pool, needed by
                 Scenario to compute k alternative routes
   config.n_agents is set as a side effect.
"""

import numpy as np

from config.config import config
from demand_calibration.demand_calibration import DemandCalibration
from utils.generate_agents import generate_agents
from utils.generate_free_flow_tt import generate_free_flow_tt_links
from utils.get_total_length_network import get_total_length_network


def demand_calibration(last_iteration_gui=True):
    ################################################
    ################################################
    # Initial guess (using heuristic length network)
    ################################################
    ################################################
    # Create table with free flow tt links (used to compute free flow shortest paths)
    generate_free_flow_tt_links()

    rng = np.random.default_rng(config.seed)
    initial_demand = _compute_initial_guess()
    agents, unique_ods = _calibration_loop(initial_demand, last_iteration_gui, rng)
    config.n_agents = len(agents)
    return agents, unique_ods


def _compute_initial_guess():
    """
    Initial guess (using heuristic length network)
    """
    total_length_network = get_total_length_network(config.network)
    hours = (config.end_time / 60) / 60

    # Heuristic is basically to consider 100 vehicles per kilometer and hour
    demand = int(
        config.heuristic_veh_km_hour_initial_guess * total_length_network * hours
    )
    # To avoid having a very small demand
    min_vehicles = 100
    result = max(demand, min_vehicles)
    return result


def _calibration_loop(initial_demand, last_iteration_gui, rng):
    ################################################
    ################################################
    # Calibration loop
    ################################################
    ################################################
    demand = initial_demand

    # Counter number of iterations until convergence
    i = 0

    # Calibration loop
    while True:
        print("\n\n###############")
        print(f"Iteration {i}")
        print("###############")
        print(f"Demand (nº agents): {demand}")

        # Generate agents using the same OD distribution as training
        demand_warmup = int(demand * config.warm_up_time / config.end_time)
        demand_post_warmup = demand - demand_warmup
        agents, unique_ods = generate_agents(demand_warmup, demand_post_warmup, rng)

        # Initialize necessary stuff to run the simulation
        demand_calibration = DemandCalibration(config.network, agents)
        congestion_metric = demand_calibration.compute_congestion_metric()

        error = config.target_congestion_metric - congestion_metric

        # Check convergence
        if abs(error) < config.tolerance_demand_calibration:
            return agents, unique_ods

        update_factor = 1 + (config.k_demand_calib * error)
        update_factor = round(float(np.clip(update_factor, 0.6, 1.4)), 3)

        demand = int(demand * update_factor)

        # Increment cunter
        i += 1
