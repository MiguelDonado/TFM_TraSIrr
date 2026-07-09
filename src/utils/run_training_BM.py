import numpy as np
import pandas as pd

from agents.factory import initialize_agents, select_actions
from config.config import config
from config.paths import POLICY_CHANGE_BM
from DUE_convergence.DUE_convergence import run_due_convergence_checks
from experiment import save_processed_data
from main import _run_training_loop
from simulation.environment import Environment
from simulation.scenario import Scenario


def run_full_training_BM(agents, unique_ods, k=None, due=True):

    # 0. Manage default arguments
    k = k if k is not None else config.n_routes_per_OD

    # 1. Reproducibility
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
    results, policy_change_history = _run_training_loop(env=env, agents=rl_agents)

    # -----------------------------
    # 5. SAVE OUTPUT
    # -----------------------------
    save_processed_data(results)
    df_policy_change = pd.DataFrame(policy_change_history)
    df_policy_change.to_parquet(POLICY_CHANGE_BM)
    # -----------------------------
    # 6. CHECK DUE convergence
    # -----------------------------
    if due:
        run_due_convergence_checks(
            scen=scen,
            end_time=config.end_time,
            time_interval=config.time_interval,
            duaIterate=False,
        )


def run_single_episode_BM(agents, unique_ods):

    # 1. Reproducibility
    rng = np.random.default_rng(config.seed)
    seeds = rng.integers(0, 100000, size=config.max_attempts)

    # 2. Create Scenario (files)
    scen = Scenario(
        map=config.network, agents=agents, unique_ods=unique_ods, seeds=seeds
    )

    # 2. Create environment
    env = Environment(scenario=scen)

    # 3. Initialize agents
    rl_agents = initialize_agents(scen=scen, seed=config.seed)

    # 4. Choose routes
    actions = select_actions(rl_agents)

    # 5. Run episode
    episode = 1
    env.run_episode(actions, episode)
