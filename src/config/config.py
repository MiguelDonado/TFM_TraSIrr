# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass, field
from enum import Enum


# Enum: Clean way to represent a variable that can only take a few predefined values
class RunMode(Enum):
    COMPUTE_ROUTES = "compute_routes"
    TRAIN = "train"
    EVAL_GUI = "eval_gui"


@dataclass
class Config:
    #####################
    # Constants
    #####################
    epsilon: float = 1e-8

    #####################
    # Training BM
    #####################
    learning_rate: float = 0.3
    memory_level: float = 1  # Traveler memory

    #####################
    # Simulation
    #####################
    network: str = "Koh/FirstNetwork_Koh.net.xml"
    n_agents: int = 50
    n_episodes: int = 25
    warm_up: int = 10
    random_factor: int = 100  # For duarouter, the random factor it applies to the edges
    max_attempts: int = 25  # (duarouter) max number of attempts for the k routes
    seed: int = 42  # Seed used for the random number generator object numpy
    n_threads: int = 7  # If we want to ensure reproducibility should be 1 :(
    routing_algorithm: str = "CH"  # CH is faster than Djistra
    fringe_factor: int = 50

    #####################
    # Simulation mode
    #####################
    mode: RunMode = RunMode.TRAIN
    # Additional flags for training mode
    have_precomputed_routes: bool = False
    episodes_gui: set[int] = field(default_factory=lambda: {1, 25})


config = Config()
