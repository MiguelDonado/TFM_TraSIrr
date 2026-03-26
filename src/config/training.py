from dataclasses import dataclass, field


@dataclass
class TrainingConfig:
    memory_size: int = 10000
    batch_size: int = 32
    min_replay_size: int = field(init=False)

    def __post_init__(self):
        self.min_replay_size = self.batch_size * 10


config_training = TrainingConfig()
