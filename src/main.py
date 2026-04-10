import subprocess
import sys

import numpy as np
import pandas as pd

from agents.agent import BMAgent
from agents.factory import initialize_agents, select_actions, update_agents
from config.config import config
from environment import Environment
from experiment import accumulate_results, make_plots, prepare_data, save_processed_data
from parsing.parser import Parser
from paths import (
    FCD_PROCESSED,
    MAP,
    ROUTES,
    STATISTICS,
    STATISTICS_PROCESSED,
    SUMO_CONF,
    TRIPS_INFO_PROCESSED,
    VEHROUTE_PROCESSED,
)
from scenario import Scenario

# Reproducibility
rng = np.random.default_rng(config.seed)
seeds = rng.integers(0, 100000, size=config.max_attempts)


def main():

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = Scenario(map=MAP, n_agents=config.n_agents, seeds=seeds)

    # -----------------------------
    # 2. CREATE ENVIRONMENT
    # -----------------------------
    env = Environment(scenario=scen, episode_with_gui=config.episode_with_gui)

    # -----------------------------
    # 3. CREATE AGENTS
    # -----------------------------
    agents = initialize_agents(n=config.n_agents, scen=scen, seed=config.seed)

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------
    results = {
        "aggregated": [],
        "vehroute": [],
        "trips_info": [],
        "fcd": [],
        "actions": [],
        "rewards": [],
    }
    for episode in range(1, config.n_episodes + 1):

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
        # 4. PREPARE GENERATED DATA
        # -----------------------------
        result = prepare_data(episode, actions, rewards)
        accumulate_results(results, result)

        # -----------------------------
        # 5. UPDATE AGENTS
        # -----------------------------
        update_agents(
            actions=actions,
            agents=agents,
            episode=episode,
            rewards=rewards,
            warm_up=config.warm_up,
        )

    # -----------------------------
    # 6. SAVE OUTPUT
    # -----------------------------
    save_processed_data(results)

    # -----------------------------
    # 7. PLOTS
    # -----------------------------
    make_plots()


####################################
# Helper functions to execute script
####################################
# This logic is introduced JUST FOR being able TO RUN IN GUI
# the simulation from previous execution


def run():
    if config.learning:
        main()

    if config.run_final_simul:
        run_final_simulation()


def run_final_simulation():
    cmd = [
        "sumo-gui",
        "-c",
        SUMO_CONF,
        "--route-files",  # Add the route-files through CLI (for simplicity, avoids having modify config file again)
        ROUTES,
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    run()
