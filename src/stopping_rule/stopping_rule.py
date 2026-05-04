import numpy as np
from config.config import config
from collections import defaultdict

##########
# Performance stability
##########


def compute_avg_travel_time(agents, trips_info):
    """
    Computes avg travel time of post warm up vehicles
    """
    set_post_warm_up_agents = [
        agent["id"] for agent in agents if agent["departure_time"] > config.warm_up_time
    ]

    travel_time_post_warm_up_agents = [
        float(agent["duration"])
        for agent in trips_info
        if agent["vehicle_id"] in set_post_warm_up_agents
    ]

    avg_travel_time = float(round(np.mean(travel_time_post_warm_up_agents), 2))

    return avg_travel_time


def is_performance_stable(window_performance, threshold=config.threshold_performance):
    # If window is not full
    if len(window_performance) < window_performance.maxlen:
        return False

    w = np.array(window_performance)

    sorted_w = np.sort(w)

    trimmed = sorted_w[3:-3]

    normalized_range = round(float((trimmed.max() - trimmed.min()) / trimmed.mean()), 3)

    # Log
    print(f"Normalized range (travel times window): {normalized_range}")

    return normalized_range < threshold


def performance_stability(agents, trips_info, window):
    avg_travel_time = compute_avg_travel_time(agents, trips_info)
    window.append(avg_travel_time)


##########
# Policy stability
##########


def create_policy_dict(BM_agents):
    policy_dict = {bm.id: bm.p for bm in BM_agents.values()}
    return policy_dict


def attach_policies_to_agents(agents, policy_dict):
    # Merge with agents
    agents_with_policy = [
        {
            "id": agent["id"],
            "od": (agent["origin"], agent["destination"]),
            "policy": policy_dict[agent["id"]],
        }
        for agent in agents
    ]
    return agents_with_policy


# Step: Aggregate per OD: Compute mean policy
# defaultdict: Is a special dict with a big advantage (if you try to access a key that does not exist,
# you do not get an error, it creates a default value)
# > The default value on this case would be an empty list
def compute_avg_policy_per_od(agents):
    od_policies = defaultdict(list)

    for agent in agents:
        od_policies[agent["od"]].append(agent["policy"])

    aggregated = {}
    for od, policies in od_policies.items():
        # Averages column-wise
        aggregated[od] = np.mean(policies, axis=0)

    return aggregated


def policy_distance(od_policies, episode):
    # Skip warm-up episodes (uniform distrib)
    # +1: Because on the episode we start to learn, we still use uniform distrib
    if episode <= config.warm_up + 1:
        return None

    deltas = []
    policies_t = od_policies[-1]
    policies_prev = od_policies[-2]

    for od in policies_t:
        # R1-norm
        delta = np.linalg.norm(policies_t[od] - policies_prev[od], ord=1)
        deltas.append(delta)

    return np.mean(deltas)


def policy_stability(
    agents, policy_dict, avg_policies_per_od, episode, absence_change_count
):
    # Agents with attached policy
    agents_with_policy = attach_policies_to_agents(agents, policy_dict)
    # Avg policy per OD (avg of policy of all the agents per OD)  [current episode]
    avg_policy_per_od = compute_avg_policy_per_od(agents_with_policy)
    # List with Avg policy per OD of all episodes
    avg_policies_per_od.append(avg_policy_per_od)

    delta = policy_distance(avg_policies_per_od, episode)

    if not delta:
        absence_change_count = 0
    # If policy_t = policy_prev
    elif delta < config.epsilon_policy_convergence:
        absence_change_count += 1
    # If policy_t != policy_prev
    else:
        absence_change_count = 0

    return absence_change_count


##########
# Total Stability (performance + policy)
##########
def check_convergence(window, absence_change_count, episode):
    # Log
    if episode > config.warm_up + 1:
        print(f"Absence change count: {absence_change_count}")

    if (
        is_performance_stable(window)
        and absence_change_count >= config.k_absence_change
    ):
        print(f"Converged at episode {episode}")
        return True

    return False
