"""
Batch operations over the full agent fleet, called from main.py.

Three functions map the per-agent BMAgent methods onto all agents at once:

  initialize_agents  — instantiate one BMAgent per entry in scen.agents.
                       Also passes through each agent's post_warm_up flag
                       (computed in utils.generate_agents when the agent
                       list is built), consumed by the stopping rule to
                       exclude warm-up agents from the convergence signal.
  select_actions     — called before each episode; returns {agent_id: route_idx}
  update_agents      — called after each episode; updates each agent's policy
                       from its observed reward

RQ5 heterogeneous memory
-------------------------
When config.heterogeneous_memory is true, each agent's γ (memory_level) is
drawn independently from Beta(a, b) instead of all agents sharing
config.memory_level, using the mean/concentration reparametrization:
  a = memory_mean * memory_concentration
  b = (1 - memory_mean) * memory_concentration
Sampling uses a Generator seeded from initialize_agents' own `seed` param
(not the global config.seed directly), so it stays reproducible under the
same seed the per-agent action-selection RNGs are derived from.
"""

import numpy as np

from config.config import config

from .agent import BMAgent


def initialize_agents(scen, seed=None):

    seed = seed if seed is not None else config.seed

    # To ensure reproducibility when we are executing simulation with heteregeneous memory,
    # in particular to ensure reproducibility of the draws from the beta distribution
    rng = np.random.default_rng(seed)

    agents = {}
    for i, agent_info in enumerate(scen.agents):
        agent_id = agent_info["id"]
        od = (agent_info["origin"], agent_info["destination"])

        routes = scen.od_routes[od]

        # post_warm_up (computed in utils.generate_agents.generate_agents,
        # just passed through here): departs after the SUMO network warm-up
        # window, as opposed to only loading traffic during it. Consumed by
        # the stopping rule (stopping_rule.create_policies_dict) to exclude
        # warm-up agents from the convergence signal.
        departure_time = agent_info["departure_time"]
        post_warm_up = agent_info["post_warm_up"]

        if config.heterogeneous_memory:
            a = config.memory_mean * config.memory_concentration
            b = config.memory_concentration*(1-config.memory_mean)
            gamma = rng.beta(a, b)
        else:
            gamma = config.memory_level

        # Distinct seed per agent (factory.py passes seed+i) so each agent's
        # select_action draws are independent, not correlated across agents.
        agents[agent_id] = BMAgent(
            agent_id=agent_id,
            routes=routes,
            seed=seed + i,
            beta=config.learning_rate,
            gamma=gamma,
            epsilon=config.epsilon,
            departure_time=departure_time,
            post_warm_up=post_warm_up
        )
    return agents


def select_actions(agents):
    actions = {agent_id: agent.select_action() for agent_id, agent in agents.items()}
    return actions


def update_agents(agents, actions, rewards, warm_up, episode):
    for agent_id, agent in agents.items():
        chosen_route = actions[agent_id]
        reward = rewards[agent_id]

        agent.update(chosen_route, reward, warm_up, episode)
