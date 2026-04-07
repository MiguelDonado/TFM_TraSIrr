from dataclasses import dataclass


@dataclass
class SimulationConfig:
    n_agents: int = 50
    start_edge: str = "E0"
    end_edge: str = "E6"
    n_episodes: int = 2
    warm_up: int = 10


config_simulation = SimulationConfig()
