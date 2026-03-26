from dataclasses import dataclass


@dataclass
class SimulationConfig:
    accident_prob: float = 0.01
    duration: int = 1000
    n_veh: int = 20
    accidents: bool = False
    start_edge: str = "E0"  # For agent vehicle
    end_edge: str = "E6"  # For agent vehicle


config_simulation = SimulationConfig()
