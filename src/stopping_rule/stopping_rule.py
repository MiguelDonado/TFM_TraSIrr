"""
Stopping rule for the BM multi-agent training loop.

The loop terminates when either condition is met:
  1. max_episodes is reached.
  2. The mean L1 policy change across post-warm-up agents falls below
     tolerance_stopping_rule for k_no_change consecutive episodes.

Policy change metric
--------------------
At each episode, the L1 norm of (current_policy - previous_policy) is
computed per agent, then averaged across post-warm-up agents:

    mean_policy_change = mean( ||p_t - p_{t-1}||_1 )

L1 norm was chosen because it measures the total probability mass
redistributed across routes — a natural unit for a probability vector.
KL-divergence was considered but requires smoothing to handle zero
probabilities on unvisited routes.

Why mean, not max
-----------------
In a multi-agent setting taking the max across agents was too restrictive
and convergence was never declared. The mean tolerates a small number
of still-adapting agents while the majority have stabilised.

Warm-up (episodes)
-------------------
Policy change is not evaluated during the minimum warm-up period of agents. All agents
start with a uniform policy and do not learn yet, so the L1 change is
uninformative until after warm-up + 1 episodes.

Post-warm-up agents (simulation time)
--------------------------------------
Separately, only agents whose departure_time falls after config.warm_up_time
count towards mean_policy_change. Agents departing during that window exist
only to load traffic onto the network before the measurement period and are
not part of the demand being studied, so their (uninformative) policy shifts
would otherwise dilute the convergence signal. Each BMAgent carries a
post_warm_up flag (computed in utils.generate_agents.generate_agents when
the agent list is built, passed through by agents.factory.initialize_agents)
for this purpose; create_policies_dict() filters on it, so policies_history
only ever contains post-warm-up agents.
"""

import numpy as np

from config.config import config

##########
# Policy stability (Stopping rule)
##########


def check_convergence(policies_history, episode, no_change_count):

    # Get the mean policy change across post-warm-up agents
    mean_policy_change = _compute_mean_policy_change(policies_history, episode)

    # Skip warm-up
    if mean_policy_change is None:
        return False, no_change_count, None

    # Update counter
    if mean_policy_change < config.tolerance_stopping_rule:
        no_change_count += 1
    else:
        no_change_count = 0

    # Log
    print(f"Mean policy change: {mean_policy_change}")
    print(f"No change count: {no_change_count}")

    # Check convergence
    converged = no_change_count >= config.k_no_change

    if converged:
        print(f"Converged at episode {episode}")

    return (converged, no_change_count, mean_policy_change)


##################
# HELPER FUNCTIONS
##################


def create_policies_dict(BM_agents):
    """
    Creates a dictionary with the ids of post-warm-up BM_agents as keys
    and their current policies as values.

    Warm-up agents (bm.post_warm_up is False) are excluded here, which is
    what keeps them out of policies_history and therefore out of the
    stopping rule's convergence signal.
    """
    policies_dict = {bm.id: bm.p for bm in BM_agents.values() if bm.post_warm_up}
    return policies_dict


def _compute_mean_policy_change(policies_history, episode):
    """
    Computes the mean L1 policy change
    between consecutive episodes across post-warm-up agents.

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
