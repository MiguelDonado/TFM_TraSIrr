# This file stores constants, hyperparameters used throughout the project

import sys
from dataclasses import dataclass, field
from enum import Enum

from scripts.network_stats import get_network_characteristics

##############################
# Heuristic to compute demand (nº agents)
##############################
# 0. Get number of lanes of the network
# lanes = get_network_characteristics()
# 1. Estimate capacity: In SUMO 1 lane = 1800 veh/h
# capacity = lanes * 1800
# 2. Demand
# demand = alpha * capacity (pero esto son veh/h)


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
    # Demand
    #####################
    alpha: float = 0.85
    congestion_ratio: float = 0.6
    tolerance: float = 0.02
    heuristic_veh_km_hour_initial_guess = 100

    #####################
    # Simulation
    #####################
    percentage_agents: float = 0.1
    start_time: int = 0
    warm_up_time: int = 600
    # Post warm-up simulation time
    simulation_time: int = 3600
    end_time: int = field(init=False)
    network: str = "Koh/FirstNetwork_Koh.net.xml"
    # Number of RL agents warmup
    n_agents_warmup: int = field(init=False)
    # Number of RL agents to analyze
    n_agents_post_warmup: int = 300
    # Total number of agents
    n_agents: int = field(init=False)
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

    def __post_init__(self):
        self.end_time = self.warm_up_time + self.simulation_time
        # Update the n_agents to use (includes the agents that are gonna have to be used on the warmup)
        # The agents introduce on warmup wont be analyzed
        total_time = self.end_time - self.start_time
        total_time_with_warmup = total_time + self.warm_up_time

        self.n_agents_warmup = int(
            (self.n_agents_post_warmup * total_time_with_warmup / total_time)
            - self.n_agents_post_warmup
        )
        self.n_agents = self.n_agents_warmup + self.n_agents_post_warmup


config = Config()
