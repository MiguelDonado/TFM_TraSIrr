# This file stores constants, hyperparameters used throughout the project

from dataclasses import dataclass, field


@dataclass
class Config:
    # Training BM
    learning_rate: float = 0.3
    memory_level: float = 1  # Traveler memory

    # Simulation
    network: str = "Koh/FirstNetwork_Koh.net.xml"
    n_agents: int = 50
    n_episodes: int = 25
    warm_up: int = 10
    random_factor: int = 100  # For duarouter, the random factor it applies to the edges
    max_attempts: int = 25  # (duarouter) max number of attempts for the k routes
    seed: int = 42  # Seed used for the random number generator object numpy
    episodes_gui: set[int] = field(default_factory=lambda: {1, 25})
    n_threads: int = 7
    routing_algorithm: str = "CH"  # CH is faster than Djistra
    fringe_factor: int = 50

    # In case I just wanna run the final simulation (from previous script execution)
    # Set learning = False and run_final_simul = True
    learning: bool = True
    run_final_simul: bool = False

    # Constants
    epsilon: float = 1e-8


config = Config()
