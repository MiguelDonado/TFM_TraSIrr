"""
Central configuration for the experiment.

Defines two objects used throughout the codebase:

  config   — singleton Config dataclass instance, populated at import
             time from a YAML file passed as the first CLI argument,
             with an optional --mode flag (default: train)
  RunMode  — enum controlling the execution mode (TRAIN, EVAL_GUI)

Config hyperparameter groups
-----------------------------
  Randomness          — global seed
  BM learning         — learning_rate (β), memory_level (γ), warm_up
  Demand              — n_agents, min_distance_factor, maxtries
  Simulation time     — warm_up_time, simulation_time, end_time (derived)
  Network & scenario  — network path, OD space size, fringe factor
  Duarouter           — routing algorithm, random_factor, n_routes_per_OD
  Stopping rule       — max_episodes, tolerance, k_no_change
  DUE convergence     — threshold_density, duaIterate settings
  Mode & flags        — episodes_gui, gui flags

Derived fields (computed in __post_init__)
------------------------------------------
  end_time  = warm_up_time + simulation_time
  warm_up   = n_routes_per_OD × 3 (min episodes before agent can start learning)

YAML locations
--------------
  Development  — experiments/developer_modes/
  Production   — experiments/tmp/  (populated by scripts/launcher.py
                 during batch runs)
"""

import argparse
from dataclasses import dataclass, field
from enum import Enum

import yaml


##############################
# Run modes
##############################
# Enum: Clean way to represent a variable that can only take a few predefined values
class RunMode(Enum):
    TRAIN = "train"
    EVAL_GUI = "eval_gui"


def load_config(path, mode):
    with open(path) as f:
        data = yaml.safe_load(f)

    flat = {key: value for section in data.values() for key, value in section.items()}

    for section in data.values():
        flat.update(section)

    return Config(mode=mode, **flat)


##############################
# Config
##############################


@dataclass
class Config:
    #####################
    # 0. Randomness
    #####################
    seed: int  # Seed used for the random number generator object numpy

    #####################
    # 1. Numerical constants
    #####################
    epsilon: float  # To avoid division by zero

    #####################
    # 2. Bush-Mosteller Learning
    #####################
    learning_rate: float
    memory_level: float
    warm_up: int = field(init=False)  # Min number of experiences before learning

    #####################
    # 3. Demand
    #####################
    n_agents: int
    # min-distance = min-distance-factor x network diagonal
    # 0.10 → many short trips.
    # 0.20 → balanced.
    # 0.30 → mostly long trips.
    min_distance_factor: float
    # Used in randomtrips.py. Used in reject random sampling
    # when searching a trip that meets the constraint   s
    maxtries: int

    #####
    # Interval time
    #####
    fixed_time_min: float
    time_interval: int = field(init=False)  # Seconds — derived from fixed_time_min

    #####################
    # 4. Simulation time
    #####################
    warm_up_time: int
    simulation_time: int  # post warm-up
    end_time: int = field(init=False)

    #####################
    # 5. Network & scenario
    #####################
    network: str

    #####################
    # 6. RandomTrips (generating od pairs)
    #####################
    # To reduce OD space (for OD generation).
    max_size_od_space: int
    fringe_factor: int

    #####################
    # 7. Duarouter
    #####################
    routing_algorithm: str  # CH is faster than Djistra
    random_factor: int  # For duarouter, the random factor it applies to the edges
    max_attempts: int  # (duarouter) max number of attempts for the k routes
    n_threads: int  # If we want to ensure reproducibility should be 1 :(
    n_routes_per_OD: int  # Number of routes per OD (compute_k_routes)

    #####################
    # 8. Stopping rule
    #####################
    max_episodes: int
    # Threshold for policy changes
    tolerance_stopping_rule: float
    # Nº of consecutive episodes that convergence criteria must be met
    k_no_change: int

    #####################
    # 9. DUE convergence
    #####################
    # When computating the Rgap, we need the table of avg travel time on links
    # This table sometimes have empty cells. To impute missing, we can do a
    # free_flow_travel_time or a fill forward. The choice depends on the density
    # of the link. If higher than threshold we assign fill forward. Otherwise free flow.
    threshold_density: int

    # duaIterate
    duaIterate_max_iterations: int
    duaIterate_step_length: float

    #####################
    # 10. Mode & flags
    #####################
    last_episode_gui_BM: bool
    last_episode_gui_duaIterate: bool
    config_name: str
    mode: RunMode = RunMode.TRAIN
    research_question: str = ""
    episodes_gui: set[int] = field(default_factory=lambda: {})

    #####################
    # Derived values
    #####################
    def __post_init__(self):
        # Compute end_time
        self.end_time = self.warm_up_time + self.simulation_time

        # Compute warm-up BM agents
        self.warm_up = self.n_routes_per_OD * 3

        # Compute time interval in seconds
        self.time_interval = int(self.fixed_time_min * 60)


#####
### INITIALIZE CONFIG
#####
# 1. Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("config", nargs="?")  # Optional positional argument
parser.add_argument(
    "--mode", choices=[m.value for m in RunMode], default=RunMode.TRAIN.value
)
args = parser.parse_args()

mode = RunMode(args.mode)

# 2. Check validity arguments
# If not eval_gui mode YAML config file is required
if mode != RunMode.EVAL_GUI and args.config is None:
    parser.error("the following argument is required: config")

# If eval_gui, YAML config file cannot be provided
if mode == RunMode.EVAL_GUI and args.config is not None:
    parser.error("'config' cannot be provided when using '--mode eval_gui'.")

# 3. Initialize config object
if mode == RunMode.EVAL_GUI:
    template_config = (
        "/home/miguel/6.Projects/Thesis/experiments/developer_modes/eval_gui.yaml"
    )
    config = load_config(template_config, mode)
else:
    config = load_config(args.config, mode)
