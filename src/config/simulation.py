from dataclasses import dataclass


@dataclass
class SimulationConfig:
    n_agents: int = 50
    start_edge: str = "E0"
    end_edge: str = "E6"
    n_episodes: int = 1000


config_simulation = SimulationConfig()
