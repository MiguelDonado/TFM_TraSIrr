import sys

import numpy as np

from agents.agent import BMAgent
from agents.factory import initialize_agents, select_actions, update_agents
from config.constants import config_constants
from config.simulation import config_simulation
from config.training import config_training
from environment import Environment
from paths import MAP_FILE
from scenario import Scenario

# Reproducibility
rng = np.random.default_rng(config_constants.seed)
seeds = rng.integers(0, 100000, size=config_constants.max_attempts)


def main():

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = Scenario(map=MAP_FILE, n_agents=config_simulation.n_agents, seeds=seeds)

    # -----------------------------
    # 2. CREATE ENVIRONMENT
    # -----------------------------
    env = Environment(scenario=scen, episode_with_gui=config_constants.episode_with_gui)

    # -----------------------------
    # 3. CREATE AGENTS
    # -----------------------------
    agents = initialize_agents(
        n=config_simulation.n_agents, scen=scen, seed=config_constants.seed
    )

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------

    for episode in range(1, config_simulation.n_episodes):

        print(f"\n--- Episode {episode} ---")

        # -----------------------------
        # 1. RESET ENVIRONMENT
        # -----------------------------
        env.reset(current_episode=episode)

        # -----------------------------
        # 2. AGENTS CHOOSE ACTIONS
        # -----------------------------
        # actions is a single dictionary {agent_1: 0, agent_2: 3, ...}
        actions = select_actions(agents)

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

        # -----------------------------
        # 6. UPDATE AGENTS
        # -----------------------------
        update_agents(
            actions=actions,
            agents=agents,
            episode=episode,
            rewards=rewards,
            warm_up=config_simulation.warm_up,
        )


if __name__ == "__main__":
    main()
