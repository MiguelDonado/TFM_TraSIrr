"""
This file stores a function that is used to calibrate the demand of the experiment

I will use avg_speed / free_flow_speed as the ratio used to measure congestion

~ 1          -> No congestion
~ 0.7 - 0.9  -> Light
~ 0.4 - 0.7  -> Medium
< 0.4        -> Heavy

"""

import numpy as np

from config.config import config
from demand_calibration.demand_calibration import DemandCalibration
from scripts.get_free_flow_speed import get_free_flow_speed
from scripts.get_total_length_network import get_total_length_network


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
