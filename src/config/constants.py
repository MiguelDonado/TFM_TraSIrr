from dataclasses import dataclass


@dataclass
class Constants:
    random_factor: int = 100
    max_attempts: int = 25
    seed: int = 42
    epsilon: float = 1e-8
    episode_with_gui: int = 30  # 0 if you dont want gui in any episode
    write_output: bool = True


config_constants = Constants()
