import sys

import numpy as np

from config.simulation import config_simulation
from config.training import config_training
from environment import Environment
from paths import MAP_FILE
from scenario import Scenario

# from agent import Agent


def main():

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = Scenario(
        map=MAP_FILE,
        n_agents=config_simulation.n_agents,
    )

    # -----------------------------
    # 2. CREATE ENVIRONMENT
    # -----------------------------
    env = Environment(scenario=scen, gui=True)

    #     # -----------------------------
    #     # 3. CREATE AGENT
    #     # -----------------------------
    #     agent = Agent(
    #         n_features=env.n_features, n_actions=env.max_n_actions, memory_size=MEMORY_SIZE
    #     )

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------

    for episode in range(config_simulation.n_episodes):

        print(f"\n--- Episode {episode + 1} ---")

        # -----------------------------
        # 1. RESET ENVIRONMENT
        # -----------------------------
        env.reset()

        # -----------------------------
        # 2. CHOOSE ACTION
        # -----------------------------
        actions = env.choose_action()

        # -----------------------------
        # 3. INSERT VEHICLES
        # -----------------------------
        env.insert_vehicles(actions)

        # -----------------------------
        # 4. RUN EPISODE
        # -----------------------------
        env.run_episode()

        # -----------------------------
        # 5. GET REWARDS
        # -----------------------------
        rewards = env.get_rewards()


if __name__ == "__main__":
    main()
