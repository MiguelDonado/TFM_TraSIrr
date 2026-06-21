# This file stores constants, hyperparameters used throughout the project
#


import sys
from dataclasses import dataclass, field
from enum import Enum

import yaml


def load_config(path):
    with open(path) as f:
        data = yaml.safe_load(f)

    flat = {key: value for section in data.values() for key, value in section.items()}

    for section in data.values():
        flat.update(section)

    return Config(**flat)


# Enum: Clean way to represent a variable that can only take a few predefined values


##############################
# Run modes
##############################
class RunMode(Enum):
    COMPUTE_ROUTES = "compute_routes"
    TRAIN = "train"
    EVAL_GUI = "eval_gui"


##############################
# Config
##############################


@dataclass
class Config:
    #####################
    # 0. Randomness
    #####################
    seed: int  # Seed used for the random number generator object numpy

    #####################
    # 1. Numerical constants
    #####################
    epsilon: float  # To avoid division by zero

    #####################
    # 2. Bush-Mosteller Learning
    #####################
    learning_rate: float
    memory_level: float
    warm_up: int = field(init=False)  # Min number of experiences before learning

    #####################
    # 3. Demand & Calibration
    #####################
    # ~ 1          -> No congestion
    # ~ 0.7 - 0.9  -> Light
    # ~ 0.4 - 0.7  -> Medium
    # < 0.4        -> Heavy

    #####
    # Initial guess
    #####
    # Used for initial guess
    """
        Scenario	Vehicles / km / hour
        Light traffic	5–15
        Moderate traffic	15–40
        Heavy traffic	40–80
        Near congestion/saturation	80–150+
    """

    heuristic_veh_km_hour_initial_guess: int

    #####
    # Calibration loop
    #####
    # We do calibration loop until the actual congestion ratio reaches the target congestion
    target_congestion_ratio: float
    # If the actual congestion ratio is closer than this tolerance to the target congestion we considered the calibration done
    tolerance_demand_calibration: float
    # Proportional term that is used on the update rule in demand calibration
    k_demand_calib: float

    #####
    # Interval time
    #####
    time_interval: int = field(init=False)
    time_interval_heuristic: float
    fixed_time_interval: bool
    fixed_time_min: int

    #####################
    # 4. Simulation time
    #####################
    warm_up_time: int
    simulation_time: int  # post warm-up
    end_time: int = field(init=False)

    #####################
    # 5. Network & scenario
    #####################
    network: str

    #####################
    # 6. RandomTrips (generating od pairs)
    #####################
    # To reduce OD space (for OD generation).
    max_size_od_space: int
    fringe_factor: int

    #####################
    # 7. Duarouter
    #####################
    routing_algorithm: str  # CH is faster than Djistra
    random_factor: int  # For duarouter, the random factor it applies to the edges
    max_attempts: int  # (duarouter) max number of attempts for the k routes
    n_threads: int  # If we want to ensure reproducibility should be 1 :(
    n_routes_per_OD: int  # Number of routes per OD (compute_k_routes)

    #####################
    # 8. Stopping rule
    #####################
    max_episodes: int
    # Threshold for policy changes
    tolerance_stopping_rule: float
    # Nº of consecutive episodes that convergence criteria must be met
    k_no_change: int

    #####################
    # 9. DUE convergence
    #####################
    # When computating the Rgap, we need the table of avg travel time on links
    # This table sometimes have empty cells. To impute missing, we can do a
    # free_flow_travel_time or a fill forward. The choice depends on the density
    # of the link. If higher than threshold we assign fill forward. Otherwise free flow.
    threshold_density: int

    # duaIterate
    duaIterate_max_iterations: int

    #####################
    # 10. Mode & flags
    #####################
    have_precomputed_routes: bool
    last_episode_gui_BM: bool
    last_episode_gui_duaIterate: bool
    config_name: str
    mode: RunMode = RunMode.TRAIN
    episodes_gui: set[int] = field(default_factory=lambda: {})

    #####################
    # Derived values
    #####################
    def __post_init__(self):
        # Compute end_time
        self.end_time = self.warm_up_time + self.simulation_time

        # Compute warm-up BM agents
        self.warm_up = self.n_routes_per_OD * 3


# Initialize config
path = sys.argv[1]
config = load_config(path)
