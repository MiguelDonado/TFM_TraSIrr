"""
Contract that every learning algorithm (Bush-Mosteller, later Thompson
Sampling, Q-learning…) must follow, so the training loop, stopping rule and
logging can use any of them without knowing which one it is.

Abstract Base Class (ABC)
-------------------------
Learner inherits from ABC, which means two things:
  1. Learner only defines a contract for its subclasses: it cannot be
     instantiated directly.
  2. Every method marked @abstractmethod must be implemented by the
     subclass. If one is missing, instantiating the subclass raises a
     TypeError immediately, not halfway through a run.

What lives where
----------------
  Learner.__init__   fields every agent has, whatever its algorithm: id,
                     routes, n_routes, rng (for action selection),
                     departure_time, post_warm_up
  subclass.__init__  calls super().__init__(...) first, then sets its own
                     fields (BM: p, history, beta, gamma…)
  agents.factory     creates the agents, and knows each algorithm's own
                     parameters (which config fields map to which argument)

Methods
-------
  select_action      route index chosen for the next episode
  update             learn from the episode's travel and waiting time
  convergence_state  values whose change between episodes the stopping rule
                     tracks (BM: p)
  internal_state     rows of the agent's internal variables for the
                     agent_state parquet (BM: ET, PT, stimulus, p…)
  snapshot           full state for the single-agent debug trace (optional)

Class attributes each subclass sets
-----------------------------------
  name               identifier used in config.algorithm ("bush_mosteller")
  results_filename   parquet under agent_state/ for internal_state rows
                     ("BM_results.parquet")
"""

from abc import ABC, abstractmethod

import numpy as np


class Learner(ABC):
    name: str  # "bush_mosteller"
    results_filename: str  # "BM_results.parquet"

    def __init__(self, agent_id, routes, seed, departure_time, post_warm_up):
        self.id = agent_id
        self.routes = routes
        self.n_routes = len(routes)
        self.rng = np.random.default_rng(seed)
        self.departure_time = departure_time
        # Whether this agent departs after the SUMO network warm-up window
        # (see module docstring); used by the stopping rule to exclude
        # warm-up agents from the convergence signal.
        self.post_warm_up = post_warm_up

    @abstractmethod
    def select_action(self) -> int:
        """Index of the route chosen for the next episode."""

    @abstractmethod
    def update(self, route, travel_time, waiting_time, episode) -> None:
        """Learn from the travel and waiting time experienced on `route`."""

    @abstractmethod
    def convergence_state(self) -> np.ndarray:
        """Values whose change between episodes signals convergence (BM: p). Used by the stopping rule."""

    @abstractmethod
    def internal_state(self, episode) -> list[dict]:
        """Rows describing the agent's internal variables this episode (BM: ET, PT, stimulus, p…)."""

    def snapshot(self) -> dict:
        """Full state for the single-agent debug trace. Optional: subclasses extend it."""
        # Default for learners that don't override it. Must be a dict, not None:
        # run_training_BM unpacks it ({"episode": e, **agent.snapshot()}), and
        # **None would crash the training loop. The id is the only field the
        # base class knows, and it keeps each trace entry tied to its agent.
        # Subclasses extend it: {**super().snapshot(), "p": ..., ...}
        return {"id": self.id}