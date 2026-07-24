"""
Generates the agent list for a fixed, pre-determined agent count.

demand_from_count(n_agents) → (agents, unique_ods)
   agents      — list of dicts with keys: id, origin, destination, departure_time
   unique_ods  — unique (origin, dest) pairs in the OD pool, needed by
                 Scenario to compute k alternative routes
"""
from config.config import config
from utils.generate_agents import generate_agents


def demand_from_count(n_agents):
    """Generate agents directly from a fixed agent count, skipping calibration."""

    demand_warmup = int(n_agents * config.warm_up_time / config.end_time)
    demand_post_warmup = n_agents - demand_warmup
    agents, unique_ods = generate_agents(demand_warmup, demand_post_warmup)
    return agents, unique_ods
