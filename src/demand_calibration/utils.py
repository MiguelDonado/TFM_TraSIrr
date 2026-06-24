"""
Calibrates the number of agents needed to achieve a target congestion
level on the network before starting the training with those agents in
the Multi Agent Reinforcement Learning setting.

Congestion metric
-----------------
    congestion_ratio = avg_speed_post_warmup / free_flow_speed

    ~ 1.0        — free flow
    ~ 0.7–0.9   — light
    ~ 0.4–0.7   — moderate
    < 0.4        — heavy

Two-phase procedure
-------------------
1. Initial guess
       n_agents = heuristic_veh_km_hour × total_length_km × hours
   Provides a starting point without running any simulation.

2. Calibration loop
   Runs SUMO iteratively, using as demand the current number of agents
   and adjusting n_agents after each simulation:

       error         = observed_congestion_ratio - target_congestion_ratio
       update_factor = clip(1 + k_demand_calib × error, 0.6, 1.4)
       n_agents      = int(n_agents × update_factor)

   Large errors produce aggressive corrections; smaller errors produce smoother
   corrections, helping convergence.
   The clip to [0.6, 1.4] prevents overshooting on the first iterations.
   Stops when |error| < tolerance_demand_calibration.
"""

import numpy as np

from config.config import config
from demand_calibration.demand_calibration import DemandCalibration
from utils.get_free_flow_speed import get_free_flow_speed
from utils.get_total_length_network import get_total_length_network


def demand_calibration(last_iteration_gui=True):
    ################################################
    ################################################
    # Initial guess (using heuristic length network)
    ################################################
    ################################################
    initial_demand = _compute_initial_guess()
    demand = _calibration_loop(initial_demand, last_iteration_gui)
    return demand


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


def _calibration_loop(initial_demand, last_iteration_gui):
    ################################################
    ################################################
    # Calibration loop
    ################################################
    ################################################
    # Compute once the free flow speed of the network
    free_flow_speed = get_free_flow_speed(config.network)
    demand = initial_demand

    # Counter number of iterations until convergence
    i = 0

    # Calibration loop
    while True:
        print("\n\n###############")
        print(f"Iteration {i}")
        print("###############")

        # Initialize necessary stuff to run the simulation
        demand_calibration = DemandCalibration(config.network, demand, free_flow_speed)
        speed_ratio = demand_calibration.compute_congestion_ratio()

        # Log
        print(f"Avg speed: {demand_calibration.avg_speed}")
        print(f"Demand (nº agents): {demand}")

        error = speed_ratio - config.target_congestion_ratio

        # Check convergence
        if abs(error) < config.tolerance_demand_calibration:
            break

        update_factor = 1 + (config.k_demand_calib * error)
        update_factor = round(float(np.clip(update_factor, 0.6, 1.4)), 3)

        demand = int(demand * update_factor)

        # Increment cunter
        i += 1

    return int(demand)
