# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np
from lxml import etree

from utils.network import get_edge_lengths


def get_edges_lengths_program(net):
    """
    Used in demand calibration -> initial guess (heuristic)
    Returns the median length of the edgess
    """
    return round(float(np.median(get_edge_lengths(net))), 2)


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
    seed: int = 42  # Seed used for the random number generator object numpy

    #####################
    # 1. Numerical constants
    #####################
    epsilon: float = 1e-8  # To avoid division by zero

    #####################
    # 2. Bush-Mosteller Learning
    #####################
    learning_rate: float = 0.3
    memory_level: float = 1
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

    heuristic_veh_km_hour_initial_guess: int = 100

    #####
    # Calibration loop
    #####
    # We do calibration loop until the actual congestion ratio reaches the target congestion
    target_congestion_ratio: float = 0.6
    # If the actual congestion ratio is closer than this tolerance to the target congestion we considered the calibration done
    tolerance_demand_calibration: float = 0.1
    # Proportional term that is used on the update rule in demand calibration
    k_demand_calib: float = 1

    #####
    # Interval time
    #####
    time_interval: int = field(init=False)
    time_interval_heuristic: float = 0.5

    #####################
    # 4. Simulation time
    #####################
    warm_up_time: int = 600
    simulation_time: int = 3600  # post warm-up
    end_time: int = field(init=False)

    #####################
    # 5. Network & scenario
    #####################
    network: str = "/home/miguel/6.Projects/Thesis/sumo/net/Popular/Sioux_Falls.net.xml"

    #####################
    # 6. RandomTrips (generating od pairs)
    #####################
    # To reduce OD space (for OD generation).
    max_size_od_space: int = 10
    fringe_factor: int = 50
    min_distance: int = field(init=False)

    #####################
    # 7. Duarouter
    #####################
    routing_algorithm: str = "CH"  # CH is faster than Djistra
    random_factor: int = 100  # For duarouter, the random factor it applies to the edges
    max_attempts: int = 25  # (duarouter) max number of attempts for the k routes
    n_threads: int = 7  # If we want to ensure reproducibility should be 1 :(
    n_routes_per_OD: int = 3  # Number of routes per OD (compute_k_routes)

    #####################
    # 8. Stopping rule
    #####################
    max_episodes: int = 200
    # Threshold for policy changes
    tolerance_stopping_rule: float = 10e-3
    # Nº of consecutive episodes that convergence criteria must be met
    k_no_change: int = 3

    #####################
    # 9. DUE convergence
    #####################
    # When computating the Rgap, we need the table of avg travel time on links
    # This table sometimes have empty cells. To impute missing, we can do a
    # free_flow_travel_time or a fill forward. The choice depends on the density
    # of the link. If higher than threshold we assign fill forward. Otherwise free flow.
    threshold_density: int = 10

    # duaIterate
    duaIterate_max_iterations: int = 10

    #####################
    # 10. Mode & flags
    #####################
    mode: RunMode = RunMode.TRAIN
    have_precomputed_routes: bool = False
    episodes_gui: set[int] = field(default_factory=lambda: {})
    last_episode_gui_BM: bool = False
    last_episode_gui_duaIterate: bool = False

    #####################
    # Derived values
    #####################
    def __post_init__(self):
        # Compute end_time
        self.end_time = self.warm_up_time + self.simulation_time

        # Compute min distance
        self.min_distance = int(2 * get_edges_lengths_program(self.network))

        # Compute warm-up BM agents
        self.warm_up = self.n_routes_per_OD * 3


config = Config()
