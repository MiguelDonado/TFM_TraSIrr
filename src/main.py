import subprocess
import sys

import numpy as np
import pandas as pd

from agents.agent import BMAgent
from agents.factory import initialize_agents, select_actions, update_agents
from config.config import config
from environment import Environment
from experiment import parse_aggregated_data, parse_vehicle_level_data
from io_module.parser import Parser
from paths import (
    MAP,
    ROUTES,
    STATISTICS,
    STATISTICS_PROCESSED,
    SUMO_CONF,
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
    # Store parsed output of each episode
    aggregated_results = []
    vehicle_level_results = []

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
        # 3. PARSE GENERATED OUTPUT
        # -----------------------------
        aggregated_result = parse_aggregated_data(episode)
        aggregated_results.append(aggregated_result)

        vehicle_level_result = parse_vehicle_level_data(episode)
        # Extend: Instead of adding the dictionary, it adds the elements of the iterable
        vehicle_level_results.extend(vehicle_level_result)

        # -----------------------------
        # 4. GET REWARDS
        # -----------------------------
        rewards = env.get_rewards()

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
    # 6. OUTPUT
    # -----------------------------
    df_1 = pd.DataFrame(aggregated_results)
    df_1.to_parquet(STATISTICS_PROCESSED, engine="pyarrow")

    df_2 = pd.DataFrame(vehicle_level_results)
    df_2.to_parquet(VEHROUTE_PROCESSED, engine="pyarrow")


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
    if config.learning:
        main()

    if config.run_final_simul:
        run_final_simulation()
