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
from paths import MAP, SUMMARY
from scenario import Scenario
from scripts.get_avg_speed import get_avg_speed
from scripts.get_free_flow_speed import get_free_flow_speed

# Constants
TARGET_SPEED_RATIO = config.congestion_ratio

# Calibration loop
for _ in range(10):
    # Initialize necessary stuff to run the simulation
    demand_calibration = DemandCalibration(MAP)

    free_flow_speed = get_free_flow_speed(MAP)

    avg_speed = get_avg_speed(config.warm_up_time, summary_filepath=SUMMARY)

    target_speed_ratio = round(avg_speed / free_flow_speed, 2)

    print(free_flow_speed, avg_speed, target_speed_ratio)

    break
