from dataclasses import dataclass


@dataclass
class Constants:
    random_factor: int = 100
    n_samples: int = 10
    gui: bool = False
    seed: int = 42


config_constants = Constants()
