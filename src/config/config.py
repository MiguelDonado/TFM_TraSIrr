# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass, field
from enum import Enum
from lxml import etree
import numpy as np


def get_edges_lengths_program(net):
    document = net
    tree = etree.parse(document)

    # Edges
    edges_length = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    edges_length = [float(edge_length) for edge_length in edges_length]

    data = np.array(edges_length)
    median_length = round(float(np.median(data)), 2)
    return median_length


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
    warm_up: int = 10  # Min number of experiences before learning

    #####################
    # 3. Demand & Calibration
    #####################
    # ~ 1          -> No congestion
    # ~ 0.7 - 0.9  -> Light
    # ~ 0.4 - 0.7  -> Medium
    # < 0.4        -> Heavy
    target_congestion_ratio: float = 0.6
    tolerance: float = 0.1
    heuristic_veh_km_hour_initial_guess: int = 100

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
    # 7. Duaroouter
    #####################
    routing_algorithm: str = "CH"  # CH is faster than Djistra
    random_factor: int = 100  # For duarouter, the random factor it applies to the edges
    max_attempts: int = 25  # (duarouter) max number of attempts for the k routes
    n_threads: int = 7  # If we want to ensure reproducibility should be 1 :(

    #####################
    # 8. Experiment control
    #####################
    n_episodes: int = 25

    #####################
    # 9. Mode & flags
    #####################
    mode: RunMode = RunMode.TRAIN
    have_precomputed_routes: bool = False
    episodes_gui: set[int] = field(default_factory=lambda: {1, 25})

    #####################
    # Derived values
    #####################
    def __post_init__(self):
        # Compute end_time
        self.end_time = self.warm_up_time + self.simulation_time

        # Coompute min distance
        self.min_distance = int(4 * get_edges_lengths_program(self.network))


config = Config()
