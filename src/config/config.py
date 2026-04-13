# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass


@dataclass
class Config:
    # Training BM
    learning_rate: float = 0.3
    memory_level: float = 1  # Traveler memory

    # Simulation
    network: str = "random/FirstRandom.net.xml"
    n_agents: int = 50
    n_episodes: int = 25
    warm_up: int = 10
    episode_with_gui: int = 0  # 0 if you dont want gui in any episode
    random_factor: int = 100  # For duarouter, the random factor it applies to the edges
    max_attempts: int = 25  # (duarouter) max number of attempts for the k routes
    seed: int = 42  # Seed used for the random number generator object numpy
    # In case I just wanna run the final simulation (from previous script execution)
    learning: bool = True
    # In case I just wanna run the final simulation (from previous script execution)
    run_final_simul: bool = True
    n_threads: int = 7
    routing_algorithm: str = "CH"  # CH is faster than Djistra
    fringe_factor: int = 50

    # Constants
    epsilon: float = 1e-8


config = Config()
