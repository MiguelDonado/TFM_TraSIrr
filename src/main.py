import numpy as np
from collections import deque
from stopping_rule.stopping_rule import (
    policy_stability,
    performance_stability,
    create_policy_dict,
    check_convergence,
)
from agents.factory import initialize_agents, select_actions, update_agents
from config.config import RunMode, config
from demand_calibration.utils import demand_calibration
from environment import Environment
from experiment import (
    accumulate_results,
    log_run_mode,
    make_plots,
    prepare_data,
    run_final_simulation,
    save_processed_data,
)
from paths import MAP
from scenario import Scenario
from DUE_convergence.utils import (
    get_avg_path_travel_time_per_odtp_k,
    get_flows_path_per_odtp_k,
    get_avg_link_travel_time_per_t_k,
)

# Reproducibility
rng = np.random.default_rng(config.seed)
seeds = rng.integers(0, 100000, size=config.max_attempts)


def main2():
    get_avg_link_travel_time_per_t_k()


def main():

    # -----------------------------
    # 0. DEMAND CALIBRATION
    # -----------------------------
    demand = demand_calibration(last_iteration_gui=False)
    demand_warmup = int(demand * config.warm_up_time / config.end_time)
    demand_post_warmup = demand - demand_warmup

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = Scenario(
        map=MAP,
        n_agents_warmup=demand_warmup,
        n_agents_post_warmup=demand_post_warmup,
        seeds=seeds,
        rng=rng,
    )

    # -----------------------------
    # 2. CREATE ENVIRONMENT
    # -----------------------------
    env = Environment(scenario=scen)

    # -----------------------------
    # 3. CREATE AGENTS
    # -----------------------------
    agents = initialize_agents(scen=scen, seed=config.seed)

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------
    # > Performance stability (deque: List with max size and LIFO logic)
    window = deque(maxlen=config.window_size)

    # > Policy stability
    absence_change_count = 0  # Counter consecutive times with equal policies
    avg_policies_per_od = []  # Stores all episodes

    # > Data
    results = {
        "aggregated": [],
        "vehroute": [],
        "trips_info": [],
        "fcd": [],
        "edgedata": [],
        "actions": [],
        "rewards": [],
        "BM_results": [],  # ET (scalar), stimulus (scalar), PT (array)
    }

    for episode in range(1, config.max_episodes + 1):

        print(f"\n--- Episode {episode} ---")

        # -----------------------------
        # 1. AGENTS CHOOSE ACTIONS
        # -----------------------------
        # actions is a single dictionary {agent_1: 0, agent_2: 3, ...}
        actions = select_actions(agents)

        # -----------------------------
        # 2. RUN EPISODE
        # -----------------------------
        env.run_episode(actions, episode)

        # -----------------------------
        # 3. GET REWARDS
        # -----------------------------
        rewards = env.get_rewards()

        # -----------------------------
        # 4. UPDATE AGENTS
        # -----------------------------
        # Save policy used in THIS EPISODE (For checking policy convergence)
        # After updating agents, they store the policy for NEXT EPISODE
        policy_dict = create_policy_dict(agents)

        update_agents(
            actions=actions,
            agents=agents,
            episode=episode,
            rewards=rewards,
            warm_up=config.warm_up,
        )

        # -----------------------------
        # 5. PREPARE GENERATED DATA
        # -----------------------------
        result = prepare_data(episode, actions, rewards, agents)
        accumulate_results(results, result)

        # -----------------------------
        # 6. STOPPING RULE
        # -----------------------------
        input_policy_stability = {
            "agents": scen.agents,
            "policy_dict": policy_dict,
            "avg_policies_per_od": avg_policies_per_od,
            "episode": episode,
            "absence_change_count": absence_change_count,
        }
        input_performance_stability = {
            "agents": scen.agents,
            "trips_info": result["trips_info_result"],
            "window": window,
        }

        absence_change_count = policy_stability(**input_policy_stability)
        performance_stability(**input_performance_stability)
        should_stop = check_convergence(window, absence_change_count, episode)

        if should_stop:
            break

    run_final_simulation()
    # -----------------------------
    # 7. SAVE OUTPUT
    # -----------------------------
    save_processed_data(results)

    # -----------------------------
    # 8. PLOTS
    # -----------------------------
    make_plots()


def run():
    log_run_mode(config.mode, config.have_precomputed_routes, config.episodes_gui)

    if config.mode == RunMode.EVAL_GUI:
        run_final_simulation()

    main()


if __name__ == "__main__":
    # run()
    main2()
