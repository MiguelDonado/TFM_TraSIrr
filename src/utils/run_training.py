"""
Entry points for running Bush-Mosteller agent training and single episodes.

orchestrate_training() drives the full multi-episode training loop and
optionally checks DUE convergence afterwards. run_single_episode_BM() runs
one episode with fixed actions, useful for debugging outside training.

RQ4 network degradation
-------------------------
When config.degradation_start_episode > 0, _run_training_loop swaps the
live network file (config.network) at two points: config.network_degraded
is copied in at episode == degradation_start_episode, and
config.network_normal is copied back at episode == degradation_end_episode.
(generate_agents() has already reset config.network to normal before the
loop starts — see utils/generate_agents.py.) Routes are computed once,
before training, off the network's topology, which the degradation does
not change (only one edge's speed), so route sets stay valid across all
three phases.
"""

import json
import shutil

import numpy as np
import pandas as pd

from agents.factory import initialize_agents, select_actions, update_agents
from config.config import config
from config.paths import BM_STATE_PATHS
from DUE_convergence.DUE_convergence import check_due_state_convergence
from experiment import accumulate_results, prepare_data, save_processed_data
from simulation.environment import Environment
from simulation.scenario import Scenario
from stopping_rule.stopping_rule import stopping_rule

from .helper_run_training import initialize_variables, marl_convergence_storage

# Debug: dump this agent's full state (history, p, ET, PT, stimulus) after
# every episode to AGENT_DEBUG_TRACE, viewable in VS Code as a folding JSON
# tree like the debugger's Locals/Watch panel. Set to None to disable.
DEBUG_AGENT_ID = 'agent_1010' if config.n_agents == 2000 else 'agent_5'


def _run_training_loop(
    env,
    agents,
):

    debug_trace, results_dict, marl_convergence_dict = initialize_variables()  

    degradation_enabled = config.degradation_start_episode > 0

    for episode in range(1, config.max_episodes + 1):

        print(f"\n--- Episode {episode} ---")

        if degradation_enabled:
            if episode == config.degradation_start_episode:
                print(f"--- Degrading network at episode {episode} ---")
                shutil.copy(config.network_degraded, config.network)
            elif episode == config.degradation_end_episode:
                print(f"--- Restoring network at episode {episode} ---")
                shutil.copy(config.network_normal, config.network)

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
        waiting_times = env.get_waiting_times()

        # -----------------------------
        # 4. UPDATE AGENTS
        # -----------------------------
        marl_convergence_storage(agents, marl_convergence_dict)

        update_agents(
            actions=actions,
            agents=agents,
            episode=episode,
            rewards=rewards,
            waiting_times=waiting_times,
        )

        if DEBUG_AGENT_ID is not None:
            debug_trace.append(
                {"episode": episode, **agents[DEBUG_AGENT_ID].snapshot()}
            )

        # -----------------------------
        # 5. PREPARE GENERATED DATA
        # -----------------------------
        result = prepare_data(episode, actions, rewards, agents)
        accumulate_results(results_dict, result)

        # -----------------------------
        # 6. STOPPING RULE
        # -----------------------------
        should_stop = stopping_rule(marl_convergence_dict, episode)
        if should_stop:
            break

    if DEBUG_AGENT_ID is not None:
        with open(BM_STATE_PATHS.agent_debug_trace, "w") as f:
            json.dump(debug_trace, f, indent=2)

    return results_dict


def orchestrate_training(
    agents, unique_ods, k=None, due=True, duaIterate=False
):

    # 0. Manage default arguments
    k = k if k is not None else config.n_routes_per_OD

    # 1. Reproducibility
    # rng: This object is only used to sample the seeds below
    # seeds: These are only used when computing k routes for each OD pair, as a way to alter the edge costs.
    rng = np.random.default_rng(config.seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    # 2. Create Scenario (files)
    scen = Scenario(
        map=config.network, agents=agents, unique_ods=unique_ods, seeds=seeds, k=k
    )

    # 2. Create environment
    env = Environment(scenario=scen)

    # 3. Initialize agents
    rl_agents = initialize_agents(scen=scen, seed=config.seed)

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------
    results = _run_training_loop(env=env, agents=rl_agents)

    # -----------------------------
    # 5. SAVE OUTPUT
    # -----------------------------
    save_processed_data(results)

    # -----------------------------
    # 6. CHECK DUE convergence
    # -----------------------------
    if due:
        check_due_state_convergence(
            scen=scen,
            duaIterate=duaIterate,
        )


def run_single_episode_BM(agents, unique_ods, seed=None):

    seed = seed if seed is not None else config.seed

    # 1. Reproducibility
    rng = np.random.default_rng(seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    # 2. Create Scenario (files)
    scen = Scenario(
        map=config.network, agents=agents, unique_ods=unique_ods, seeds=seeds
    )

    # 2. Create environment
    env = Environment(scenario=scen)

    # 3. Initialize agents
    rl_agents = initialize_agents(scen=scen, seed=seed)

    # 4. Choose routes
    actions = select_actions(rl_agents)

    # 5. Run episode
    episode = 1
    env.run_episode(actions, episode)
