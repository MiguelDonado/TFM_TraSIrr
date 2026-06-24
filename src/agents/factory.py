"""
Batch operations over the full agent fleet, called from main.py.

Three functions map the per-agent BMAgent methods onto all agents at once:

  initialize_agents  — instantiate one BMAgent per entry in scen.agents,
  select_actions     — called before each episode; returns {agent_id: route_idx}
  update_agents      — called after each episode; updates each agent's policy
                       from its observed reward
"""

from .agent import BMAgent


def initialize_agents(scen, seed):
    agents = {}
    for i, agent_info in enumerate(scen.agents):
        agent_id = agent_info["id"]
        od = (agent_info["origin"], agent_info["destination"])

        routes = scen.od_routes[od]

        agents[agent_id] = BMAgent(agent_id=agent_id, routes=routes, seed=seed + i)
    return agents


def select_actions(agents):
    actions = {agent_id: agent.select_action() for agent_id, agent in agents.items()}
    return actions


def update_agents(agents, actions, rewards, warm_up, episode):
    for agent_id, agent in agents.items():
        chosen_route = actions[agent_id]
        reward = rewards[agent_id]

        agent.update(chosen_route, reward, warm_up, episode)
