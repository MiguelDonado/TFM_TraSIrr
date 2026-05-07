import numpy as np
from config.config import config

##########
# Policy stability (Stopping rule)
##########


def check_convergence(policies_history, episode, no_change_count):

    # Get the maximum policy change across all agents
    meam_policy_change = compute_mean_policy_change(policies_history, episode)

    # Skip warm-up
    if meam_policy_change is None:
        return False, no_change_count

    # Update counter
    if meam_policy_change < config.tolerance_stopping_rule:
        no_change_count += 1
    else:
        no_change_count = 0

    # Log
    print(f"Mean policy change: {meam_policy_change}")
    print(f"No change count: {no_change_count}")

    # Check convergence
    converged = no_change_count >= config.k_no_change

    if converged:
        print(f"Converged at episode {episode}")

    return converged, no_change_count


##################
# HELPER FUNCTIONS
##################


def create_policies_dict(BM_agents):
    """
    Creates a dictionary with the BM_agents ids as keys
    and their current policies as values
    """
    policies_dict = {bm.id: bm.p for bm in BM_agents.values()}
    return policies_dict


def compute_mean_policy_change(policies_history, episode):
    """
    Computes the mean L1 policy change
    between consecutive episodes across all agents.

    The L1 norm measures the total probability mass
    shift in the policy vector.
    """

    # Skip warm-up episodes (uniform distrib)
    # +1: Because on the episode we start to learn, we still use uniform distrib
    if episode <= config.warm_up + 1:
        return None

    current_policies = policies_history[-1]
    previous_policies = policies_history[-2]

    policy_changes = [
        np.linalg.norm(current_policies[agent] - previous_policies[agent], ord=1)
        for agent in current_policies
    ]
    return np.mean(policy_changes)
