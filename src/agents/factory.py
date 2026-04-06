# This file is regarding the process of creating multiple agents.
# The function initialize_agents does not go in main.py because it is not relative to app control flow,
# and it does not go in agent.py because it is not relative to agent logic

from .agent import BMAgent


def initialize_agents(n, scen, seed):
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
