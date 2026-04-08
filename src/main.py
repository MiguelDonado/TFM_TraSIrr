import sys

import numpy as np

from agents.agent import BMAgent
from agents.factory import initialize_agents, select_actions, update_agents
from config.config import config
from environment import Environment
from experiment import run_and_parse_output
from io_module.parser import Parser
from io_module.plots import ExperimentPlotter
from paths import MAP_FILE, STATISTICSINFO_OUTPUT_FILE
from scenario import Scenario

# Reproducibility
rng = np.random.default_rng(config.seed)
seeds = rng.integers(0, 100000, size=config.max_attempts)


def main():

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = Scenario(map=MAP_FILE, n_agents=config.n_agents, seeds=seeds)

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
    results = []

    for episode in range(1, config.n_episodes + 1):

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
        result = run_and_parse_output(env, episode)
        results.append(result)

        # return self.parser.parse_statistics_output(current_episode)
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
            warm_up=config.warm_up,
        )

    # -----------------------------
    # 7. OUTPUT
    # -----------------------------
    experimentPlotter = ExperimentPlotter()
    experimentPlotter.statistics_output(results)


if __name__ == "__main__":
    main()
