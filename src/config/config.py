# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass, field
from enum import Enum

from scripts.network_stats import get_network_characteristics

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
    target_congestion_ratio: float = 0.6
    tolerance: float = 0.02
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
    network: str = "Koh/FirstNetwork_Koh.net.xml"

    #####################
    # 6. RandomTrips (generating od pairs)
    #####################
    # To reduce OD space (for OD generation).
    # Consider only a percentage of agents when generating od pairs
    percentage_agents: float = 0.1
    fringe_factor: int = 50

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


config = Config()
