"""
This script is used to calibrate the demand of the experiment

I will use avg_speed / free_flow_speed as the ratio used to measure congestion

~ 1          -> No congestion
~ 0.7 - 0.9  -> Light
~ 0.4 - 0.7  -> Medium
< 0.4        -> Heavy

"""

from config.config import config
from demand_calibration_helper import DemandCalibration
from paths import MAP
from scripts.get_free_flow_speed import get_free_flow_speed

# Constants
TARGET_SPEED_RATIO = config.congestion_ratio
n_agents = 50
# Counter number of iterations until convergence
i = 0

# Compute once the free flow speed of the network
free_flow_speed = get_free_flow_speed(MAP)

# Calibration loop
while True:
    print("\n\n###############")
    print(f"Iteration {i}")
    print("###############")

    # Initialize necessary stuff to run the simulation
    demand_calibration = DemandCalibration(MAP, n_agents, free_flow_speed)
    speed_ratio = demand_calibration.compute_congestion_ratio()

    # Log
    print(f"Avg speed: {demand_calibration.avg_speed}")
    print(f"Nº agents: {n_agents}")

    # Check convergence
    if abs(speed_ratio - TARGET_SPEED_RATIO) < config.tolerance:
        break

    # Not sufficiently congested
    if speed_ratio > TARGET_SPEED_RATIO:
        # Increase demand
        n_agents = int(n_agents * 1.2)

    # Too congested
    else:
        # Decrease demand
        n_agents = int(n_agents * 0.8)

    # Increment cunter
    i += 1

# Visualize last episode
demand_calibration.run_episode_with_gui()
