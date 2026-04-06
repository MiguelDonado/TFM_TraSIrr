# This file is regarding the process of creating multiple agents.
# The function initialize_agents does not go in main.py because it is not relative to app control flow,
# and it does not go in agent.py because it is not relative to agent logic

from .agent import BMAgent


def initialize_agents(n, scen, rng):
    agents = {}
    for agent_info in scen.agents:
        agent_id = agent_info["id"]
        od = (agent_info["origin"], agent_info["destination"])

        routes = scen.od_routes[od]

        agents[agent_id] = BMAgent(agent_id=agent_id, routes=routes, rng=rng)
    return agents


def agents_select_actions(agents):
    actions = {agent_id: agent.select_action() for agent_id, agent in agents.items()}
    return actions
