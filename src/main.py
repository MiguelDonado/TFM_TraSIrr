import numpy as np
from collections import deque
from stopping_rule.stopping_rule import (
    create_policies_dict,
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
from paths import (
    MAP,
    SUMO_CONF,
    SUMO_CONF_AGGREGATED,
    GUI_SETTINGS,
    GUI_SETTINGS_AGGREGATED,
    EDGEDATA_PROCESSED,
    EDGEDATA_DUEITERATE_PROCESSED,
    ROUTES,
    MEANDATA,
    MEANDATA_AGGREGATED,
    ROUTES_DUEITERATE,
)
from scenario import Scenario

from DUE_convergence.DUE_convergence import (
    check_DUE_convergence_BM,
    check_DUE_convergence_dueIterate,
    generate_generic_files_DUE_convergence,
)

from analysis.sumo_edges_visualization import run_episode_color_edges

# Reproducibility
rng = np.random.default_rng(config.seed)
seeds = rng.integers(0, 100000, size=config.max_attempts)


def main2():
    routes = [ROUTES, ROUTES_DUEITERATE]
    for route in routes:
        run_episode_color_edges(
            aggregated=False,
            config_visualization=SUMO_CONF_AGGREGATED,
            generic_config=SUMO_CONF,
            generic_gui_settings=GUI_SETTINGS,
            gui_settings_visualization=GUI_SETTINGS_AGGREGATED,
            edgedata_BM_file=EDGEDATA_PROCESSED,
            edgedata_dueIterate_file=EDGEDATA_DUEITERATE_PROCESSED,
            generic_meandata=MEANDATA,
            meandata_visualization=MEANDATA_AGGREGATED,
            routes_file=route,
            period=900,
            metric="entered",
        )


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
    # 2. CHECK DUEIERATE RGAP (DUE)
    # -----------------------------
    generate_generic_files_DUE_convergence()
    check_DUE_convergence_dueIterate(
        scen, end_time=config.end_time, time_interval=config.time_interval
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
    # > Policy stability
    no_change_count = 0  # Counter consecutive times without policy changes
    policies_history = []  # Stores policies of all agents for all episodes

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
        # Save policy used in THIS EPISODE (For checking policy convergence in the stopping rule)
        # After updating agents, they store the policy for NEXT EPISODE
        current_policies = create_policies_dict(agents)
        # Store current policies in history
        policies_history.append(current_policies)

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
        should_stop, no_change_count = check_convergence(
            policies_history=policies_history,
            episode=episode,
            no_change_count=no_change_count,
        )

        if should_stop:
            break

    run_final_simulation()
    # -----------------------------
    # 7. SAVE OUTPUT
    # -----------------------------
    save_processed_data(results)

    # -----------------------------
    # 8. CHECK DUE convergence
    # -----------------------------
    check_DUE_convergence_BM(
        end_time=config.end_time, time_interval=config.time_interval
    )

    # -----------------------------
    # 9. PLOTS
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
