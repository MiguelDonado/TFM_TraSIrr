"""
Central configuration for the experiment.

Defines the object used throughout the codebase:

  config   — singleton Config dataclass instance, populated at import
             time from a YAML file passed as the first CLI argument

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
  Flags               — episodes_gui, gui flags
  Degradation         — network_normal/network_degraded, degradation_start/
                        end_episode (RQ4: temporal link degradation, off
                        by default — degradation_start_episode == 0)
  Heterogeneity       — heterogeneous_memory, memory_mean, memory_concentration
                        (RQ5: per-agent γ ~ Beta(mean·conc, (1-mean)·conc)
                        instead of one shared config.memory_level, off by
                        default)
  Reliability sensitivity — reliability_sensitivity (RQ11: θ ≥ 0, risk-loads
                        both the aspiration ET and each route's PT_r by
                        θ·σ, where σ is a γ-weighted travel-time std dev.
                        θ=0 recovers the original model exactly, off by
                        default)
  Waiting-time sensitivity — waiting_time_sensitivity (RQ12: φ ≥ 0, loads
                        both the aspiration ET and each route's PT_r by
                        φ·WT, where WT is a γ-weighted average of SUMO's
                        per-trip waitingTime (seconds stopped/crawling
                        below 0.1 m/s), same anchoring/weights as PT_r/ET.
                        φ=0 recovers the pre-RQ12 model exactly, off by
                        default)
  Nonlinear stimulus  — nonlinear_stimulus (RQ13: bool, off by default).
                        When true, each route's relative margin
                        (AC-PC_r)/AC is passed through a dead-zone +
                        quadratic-ramp transform (shape parameter
                        stimulus_tau, a fraction of AC) before max/min
                        normalisation, so margins within tau of AC
                        contribute zero stimulus. Unlike theta/phi above,
                        tau=0 does NOT recover the linear model (the
                        transform itself, not just its threshold, changes
                        the shape) — nonlinear_stimulus=False is the only
                        way to recover the pre-RQ13 model exactly.
  Custom demand       — custom_od_pairs (toy networks / manual OD control):
                        hand-picked OD pairs, agent split, and exact
                        alternative routes, bypassing randomTrips and the
                        duarouter route search. Off by default (empty list).
                        See utils/generate_agents.py and
                        simulation/scenario.py for where it's consumed.


Derived fields (computed in __post_init__)
------------------------------------------
  end_time  = warm_up_time + simulation_time
  warm_up   = n_routes_per_OD × 3 (min episodes before agent can start learning)

YAML locations
--------------
  Development  — experiments/developer_modes/
  Production   — experiments/tmp/  (populated by scripts/launcher.py
                 during batch runs)

Files aclaration
-----------------                 
1. ROUTES: File used by BM algorithm. It contains the trips and routes (actions) of agents
2. TRIPS_TDSP: File that contains the grid of combinations (time_interval, od) used by TDSP for both methods.
3. DuaIteratePaths.trips: File used by DuaIterate. It only contains the trips but not the routes.
"""

import argparse
from dataclasses import dataclass, field

import yaml


def load_config(path):
    with open(path) as f:
        data = yaml.safe_load(f)

    flat = {key: value for section in data.values() for key, value in section.items()}

    for section in data.values():
        flat.update(section)

    return Config(**flat)


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
    # 10. Flags
    #####################
    last_episode_gui_BM: bool
    last_episode_gui_duaIterate: bool
    config_name: str
    research_question: str = ""
    episodes_gui: set[int] = field(default_factory=lambda: {})
    network_normal: str = ""
    network_degraded: str = ""
    degradation_start_episode: int = 0
    degradation_end_episode: int = 0
    heterogeneous_memory: bool = False
    memory_mean: float = 0
    memory_concentration: float = 0
    reliability_sensitivity: float = 0.0
    waiting_time_sensitivity: float = 0.0
    nonlinear_stimulus: bool = False
    stimulus_tau: float = 0.0

    #####################
    # Custom demand (toy networks / manual OD control)
    #####################
    # When non-empty, replaces randomTrips-based OD generation (generate_agents)
    # AND the duarouter route search (Scenario.compute_k_routes) with hand-picked
    # values. Each entry:
    #   origin, destination — edge IDs in config.network
    #   count                — number of agents sampled onto this OD pair
    #                         (raw counts, not normalized — same convention
    #                         as an OD matrix; sample_ods normalizes
    #                         internally to draw the total agent count)
    #   routes              — list of alternative routes for this OD pair, each
    #                         a list of edge IDs from origin to destination
    custom_od_pairs: list = field(default_factory=list)

    # Example (in a YAML section, any section name works — load_config flattens
    # them all before constructing Config):
    
    # custom_demand:
    #   custom_od_pairs:
    #     - origin: "E1_2_WB"
    #       destination: "E21_24_EB"
    #       count: 500
    #       routes:
    #         - ["E1_2_WB", "E1_3_SB", "E3_12_SB", "E12_13_SB", "E13_24_EB", "E21_24_EB"]
    #         - ["E1_2_WB", "E1_3_SB", "E3_4_EB", "E4_11_SB", "E11_14_SB", "E14_23_SB", "E23_24_SB", "E21_24_EB"]
    #     - origin: "E3_4_EB"
    #       destination: "E20_21_EB"
    #       count: 300
    #       routes:
    #         - ["E3_4_EB", "E4_11_SB", "E11_14_SB", "E14_23_SB", "E23_24_SB", "E21_24_EB", "E20_21_EB"]


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
args = parser.parse_args()

# 2. Check validity arguments
if args.config is None:
    parser.error("the following argument is required: config")

# 3. Initialize config object
config = load_config(args.config)
