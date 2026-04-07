from dataclasses import dataclass


@dataclass
class Constants:
    random_factor: int = 100
    max_attempts: int = 100
    seed: int = 42
    epsilon: float = 1e-8
    episode_with_gui: int = 2


config_constants = Constants()
