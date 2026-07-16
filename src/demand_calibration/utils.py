"""
Calibrates the number of agents needed to achieve a target congestion
level on the network before starting the training with those agents in
the Multi Agent Reinforcement Learning setting.

Congestion metric
-----------------
    congestion_ratio = (1/N) * Σ( T_i / T_i_free ),  i = 1..N agents

    where T_i is the actual trip duration and T_i_free the free-flow trip
    duration (shortest path under empty network conditions). Equals 1.0
    under free flow and increases monotonically with congestion.

Two-phase procedure
-------------------
1. Initial guess
       n_agents = heuristic_veh_km_hour × total_length_km × hours
   Provides a starting point without running any simulation.

2. Calibration loop
   Runs SUMO iteratively, using as demand the current number of agents
   and adjusting n_agents after each simulation:

       error         = target_congestion_metric - observed_congestion_ratio
       update_factor = clip(1 + k × error, 0.7, 1.3)
       n_{t+1}       = (1 − α) × n_t  +  α × (n_t × update_factor),   α = 0.3

   Two mechanisms prevent oscillation around the target:

   Adaptive gain — k shrinks as |error| shrinks:
       |error| > 0.4  →  k = 0.6
       |error| > 0.15 →  k = 0.3
       otherwise      →  k = 0.1
   The correction is already proportional to the error, so it naturally
   decreases as the target is approached. Adaptive gain adds a second layer:
   the controller intentionally becomes less aggressive near the target,
   so the demand shrinks for two reasons — the error is smaller and the
   gain is smaller — reducing the risk of overshooting.

   Smoothing — only a fraction α of the recommended update is applied each
   iteration.

   Stops when |error| < tolerance_demand_calibration.

Returns
-------
Both functions return (agents, unique_ods) and set config.n_agents as a side effect.

demand_calibration() → (agents, unique_ods)
   Runs the calibration loop until the congestion metric matches
   config.target_congestion_metric within config.tolerance_demand_calibration.

demand_from_count(n_agents) → (agents, unique_ods)
   Skips calibration entirely; generates agents directly from a fixed count.
   agents      — list of dicts with keys: id, origin, destination, departure_time
   unique_ods  — unique (origin, dest) pairs in the OD pool, needed by
                 Scenario to compute k alternative routes
"""

import numpy as np

from config.config import config
from demand_calibration.demand_calibration import DemandCalibration
from utils.generate_agents import generate_agents
from utils.generate_free_flow_tt import generate_free_flow_tt_links
from utils.get_total_length_network import get_total_length_network


def demand_from_count(n_agents, seed=None):
    """Generate agents directly from a fixed agent count, skipping calibration."""

    seed = seed if seed is not None else config.seed

    generate_free_flow_tt_links()
    rng = np.random.default_rng(seed)
    demand_warmup = int(n_agents * config.warm_up_time / config.end_time)
    demand_post_warmup = n_agents - demand_warmup
    agents, unique_ods = generate_agents(demand_warmup, demand_post_warmup, rng)
    config.n_agents = len(agents)
    return agents, unique_ods


def demand_calibration(last_iteration_gui=True, seed=None):
    ################################################
    ################################################
    # Initial guess (using heuristic length network)
    ################################################
    ################################################

    seed = seed if seed is not None else config.seed

    rng = np.random.default_rng(seed)
    initial_demand = _compute_initial_guess()
    agents, unique_ods = _calibration_loop(initial_demand, last_iteration_gui, rng)
    config.n_agents = len(agents)
    return agents, unique_ods


def _compute_initial_guess():
    """
    Initial guess (using heuristic length network)
    """
    total_length_network = get_total_length_network(config.network)
    hours = (config.end_time / 60) / 60

    # Heuristic is basically to consider 100 vehicles per kilometer and hour
    demand = int(
        config.heuristic_veh_km_hour_initial_guess * total_length_network * hours
    )
    # To avoid having a very small demand
    min_vehicles = 100
    result = max(demand, min_vehicles)
    return result


def _calibration_loop(
    initial_demand,
    last_iteration_gui,
    rng,
):
    ################################################
    ################################################
    # Calibration loop
    ################################################
    ################################################
    demand = initial_demand

    # Counter number of iterations until convergence
    i = 0

    # Calibration loop
    while True:
        print("\n\n###############")
        print(f"Iteration {i}")
        print("###############")
        print(f"Demand (nº agents): {demand}")

        # Generate agents using the same OD distribution as training
        demand_warmup = int(demand * config.warm_up_time / config.end_time)
        demand_post_warmup = demand - demand_warmup
        print(f"Demand (nº post-warm up agents): {demand_post_warmup}")
        agents, unique_ods = generate_agents(demand_warmup, demand_post_warmup, rng)

        # Initialize necessary stuff to run the simulation
        demand_calibration = DemandCalibration(config.network, agents)
        congestion_metric = demand_calibration.compute_congestion_metric()

        error = config.target_congestion_metric - congestion_metric

        # Check convergence
        if abs(error) < config.tolerance_demand_calibration:
            return agents, unique_ods

        # Adaptive gain
        if abs(error) > 0.4:
            k = 0.6
        elif abs(error) > 0.15:
            k = 0.3
        else:
            k = 0.1

        update_factor = 1 + (k * error)
        update_factor = round(float(np.clip(update_factor, 0.7, 1.3)), 3)

        # Smoothing
        alpha = 0.3
        demand = int((1 - alpha) * demand + alpha * (demand * update_factor))

        # Increment cunter
        i += 1
