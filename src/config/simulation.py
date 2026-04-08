from dataclasses import dataclass


@dataclass
class SimulationConfig:
    n_agents: int = 50
    od_1_start: str = "E0"
    od_2_start: str = "-E6"
    od_1_end: str = "E6"
    od_2_end: str = "E7"
    n_episodes: int = 30
    warm_up: int = 10


config_simulation = SimulationConfig()
