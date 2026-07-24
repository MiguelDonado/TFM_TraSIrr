"""
Entry point for the simulation.

'Simulation' here means the full multi-episode training run, not a single
SUMO episode. One call to run() executes demand calibration, BM agent
training over up to config.max_episodes days, DUE convergence checks
(BM and duaIterate benchmark), and MLflow logging.

Execution order
---------------
0. Generate agents      — sample OD pairs and departure times for config.n_agents
1. Scenario             — generate OD pairs, k routes, SUMO config files
2. Environment          — SUMO subprocess wrapper (file-based, no TraCI)
3. Agents               — initialise BMAgent probability vectors
4. Training loop        — episodes until policy convergence or max_episodes
5. Save outputs         — parquet files for all agent and SUMO data
6. DUE convergence      — R-gap for BM and duaIterate benchmark
7. MLflow               — log parameters, metrics, and artifacts

Entry points
------------
run()               called by __main__ or by scripts/launcher.py
                    (launcher runs grid-search experiments in batch)
"""

import os

import mlflow
import numpy as np
import pandas as pd

from agents.factory import initialize_agents, select_actions, update_agents
from config.config import config
from config.paths import POLICY_CHANGE_BM, ensure_dirs
from demand_calibration.utils import demand_from_count
from DUE_convergence.DUE_convergence import run_due_convergence_checks
from experiment import (
    accumulate_results,
    prepare_data,
    run_final_simulation,
    save_processed_data,
)
from mlflow_tracking.simulation import log_simulation_mlflow
from mlflow_tracking.utils import set_up_mlflow
from simulation.environment import Environment
from simulation.scenario import Scenario
from stopping_rule.stopping_rule import (
    check_convergence,
    create_policies_dict,
)
from utils.generate_free_flow_tt import generate_free_flow_tt_links


def _run_training_loop(
    env,
    agents,
):
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
    return results, policy_change_history


def main():
    # 1. Make sure all necessary directories exist
    ensure_dirs()

    # 2. Reproducibility
    rng = np.random.default_rng(config.seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    set_up_mlflow()
    with mlflow.start_run() as run:
        # -----------------------------
        # 0. GENERATE AGENTS
        # -----------------------------
        agents, unique_ods = demand_from_count(config.n_agents)

        # -----------------------------
        # 1. CREATE SCENARIO (files)
        # -----------------------------
        scen = Scenario(
            map=config.network,
            agents=agents,
            unique_ods=unique_ods,
            seeds=seeds,
        )

        # -----------------------------
        # 2. CREATE ENVIRONMENT
        # -----------------------------
        env = Environment(scenario=scen)

        # -----------------------------
        # 3. CREATE AGENTS
        # -----------------------------
        agents = initialize_agents(scen=scen)

        # -----------------------------
        # 4. TRAINING LOOP
        # -----------------------------
        results, policy_change_history = _run_training_loop(env=env, agents=agents)

        if config.last_episode_gui_BM:
            run_final_simulation()
        # -----------------------------
        # 5. SAVE OUTPUT
        # -----------------------------
        save_processed_data(results)
        df_policy_change = pd.DataFrame(policy_change_history)
        df_policy_change.to_parquet(POLICY_CHANGE_BM)

        # -----------------------------
        # 6. CHECK DUE convergence
        # -----------------------------
        generate_free_flow_tt_links()
        run_due_convergence_checks(
            scen=scen, end_time=config.end_time, time_interval=config.time_interval
        )

        # -----------------------------
        # 7. MLflow (Artifact storage, Experiment tracking)
        # -----------------------------
        log_simulation_mlflow(run_id=run.info.run_id)

    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


if __name__ == "__main__":
    main()
