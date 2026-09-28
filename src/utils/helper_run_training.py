from config.config import config
from stopping_rule.stopping_rule import create_policies_dict


def initialize_variables():
    # Two variables will be created:
    # 0. debug_trace
    # 1. convergence_dict
    # 2. results_dict

    # 1. Agnostic
    debug_trace = []  # DEBUG_AGENT_ID's full state, one entry per episode
    results_dict = {
        "aggregated": [],
        "vehroute": [],
        "trips_info": [],
        "fcd": [],
        "edgedata": [],
        "actions": [],
        "rewards": [],
    }

    # 2. Algorithm-specific
    # Bush-Mosteller
    # (MARL CONVERGENCE)
    if config.algorithm == "BM":
        # Constants
        marl_convergence_dict = {
            "no_change_count":0,  # Counter consecutive times without policy changes
            "policies_history":[],  # Stores policies of all agents for all episodes
            "policy_change_history":[]
        }

        # Add key to results 
        results_dict["algorithm_results"] = []  # ET (scalar), stimulus (scalar), PT (array), p (array)

    return debug_trace, results_dict, marl_convergence_dict

def marl_convergence_storage(agents, marl_convergence_dict):
    
    if config.algorithm == "BM":
        # Save policy used in THIS EPISODE (For checking policy convergence in the stopping rule)
        # Only post-warm-up agents are included (see stopping_rule.create_policies_dict)
        # After updating agents, they store the policy for NEXT EPISODE
        current_policies = create_policies_dict(agents)
        # Store current policies in history
        marl_convergence_dict["policies_history"].append(current_policies)