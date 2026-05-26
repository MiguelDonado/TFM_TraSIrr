import os
import pandas as pd
import mlflow
import numpy as np
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
    prepare_data,
    run_final_simulation,
    save_processed_data,
)
from paths import MAP, POLICY_CHANGE_BM
from scenario import Scenario
from MLflow.mlflow_utils import log_simulation_mlflow
from DUE_convergence.DUE_convergence import run_DUE_convergence_checks

# Reproducibility
rng = np.random.default_rng(config.seed)
seeds = rng.integers(0, 100000, size=config.max_attempts)


def main2():
    pass


def main():

    mlflow.set_experiment("BM Thesis")
    with mlflow.start_run() as run:

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
        # > Policy stability
        no_change_count = 0  # Counter consecutive times without policy changes
        policies_history = []  # Stores policies of all agents for all episodes
        policy_change_history = []

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
            should_stop, no_change_count, mean_policy_change = check_convergence(
                policies_history=policies_history,
                episode=episode,
                no_change_count=no_change_count,
            )
            if mean_policy_change:
                policy_change_history.append(
                    {"episode": episode, "mean_policy_change": mean_policy_change}
                )

            if should_stop:
                break

        if config.last_episode_gui_BM:
            run_final_simulation()
        # -----------------------------
        # 7. SAVE OUTPUT
        # -----------------------------
        save_processed_data(results)
        df_policy_change = pd.DataFrame(policy_change_history)
        df_policy_change.to_parquet(POLICY_CHANGE_BM)
        # -----------------------------
        # 8. CHECK DUE convergence
        # -----------------------------
        run_DUE_convergence_checks(
            scen=scen, end_time=config.end_time, time_interval=config.time_interval
        )

        # -----------------------------
        # 9. MLflow (Artifact storage, Experiment tracking)
        # -----------------------------
        log_simulation_mlflow()

        # Play sound to signal end of script
        os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


def run():
    log_run_mode(config.mode, config.have_precomputed_routes, config.episodes_gui)

    if config.mode == RunMode.EVAL_GUI:
        run_final_simulation()

    main()


if __name__ == "__main__":
    run()
    # main2()
