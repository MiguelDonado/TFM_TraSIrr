import numpy as np

from agents.factory import initialize_agents, select_actions, update_agents
from config.config import RunMode, config
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

# Reproducibility
rng = np.random.default_rng(config.seed)
seeds = rng.integers(0, 100000, size=config.max_attempts)


def main():

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = Scenario(map=MAP, n_agents=config.n_agents, seeds=seeds, rng=rng)

    # -----------------------------
    # 2. CREATE ENVIRONMENT
    # -----------------------------
    env = Environment(scenario=scen)

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
        "BM_results": [],  # ET (scalar), stimulus (scalar), PT (array)
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
        # 4. UPDATE AGENTS
        # -----------------------------
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
    # 6. SAVE OUTPUT
    # -----------------------------
    save_processed_data(results)

    # -----------------------------
    # 7. PLOTS
    # -----------------------------
    make_plots()


def run():
    log_run_mode(config.mode, config.have_precomputed_routes, config.episodes_gui)

    if config.mode == RunMode.EVAL_GUI:
        run_final_simulation()

    main()


if __name__ == "__main__":
    run()
