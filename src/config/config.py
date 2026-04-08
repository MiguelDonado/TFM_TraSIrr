# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass


@dataclass
class Config:
    # Training BM
    learning_rate: float = 0.3
    memory_level: float = 1  # Traveler memory

    # Simulation
    network: str = "thesisToyNetwork.net.xml"
    n_agents: int = 50
    n_episodes: int = 30
    warm_up: int = 10
    episode_with_gui: int = 1  # 0 if you dont want gui in any episode
    random_factor: int = 100  # For duarouter, the random factor it applies to the edges
    max_attempts: int = 25  # (duarouter) max number of attempts for the k routes
    seed: int = 42  # Seed used for the random number generator object numpy

    # Constants
    epsilon: float = 1e-8


config = Config()
