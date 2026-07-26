"""
Entry point for the simulation.

'Simulation' here means the full multi-episode training run, not a single
SUMO episode. One call to main() generates demand, delegates scenario setup,
training, output saving, and DUE convergence checks to
utils/run_training_BM.py, logs everything to MLflow, and optionally replays
the last episode in the SUMO GUI.

Execution order
---------------
0. Generate agents      — sample OD pairs and departure times for config.n_agents
1. Training             — scenario/environment/agent setup, training loop,
                           save outputs, DUE convergence checks
                           (BM and duaIterate benchmark)
2. MLflow               — log parameters, metrics, and artifacts
3. GUI replay           — optional, replays the last episode then exits

Entry points
------------
main()              called by __main__ or by scripts/launcher.py
                    (launcher runs grid-search experiments in batch)
"""

import os

import mlflow

from config.config import config
from config.paths import ensure_dirs
from experiment import run_final_simulation
from mlflow_tracking.simulation import log_simulation_mlflow
from mlflow_tracking.utils import set_up_mlflow
from utils.generate_agents import demand_from_count
from utils.run_training_BM import run_full_training_BM


def main():
    # 1. Make sure all necessary directories exist
    ensure_dirs()

    set_up_mlflow()
    with mlflow.start_run() as run:
        # -----------------------------
        # 0. GENERATE AGENTS
        # -----------------------------
        agents, unique_ods = demand_from_count(config.n_agents)

        # -----------------------------
        # 1. TRAINING (scenario, environment, agents, training loop,
        #    save output, DUE convergence)
        # -----------------------------
        run_full_training_BM(
            agents=agents, unique_ods=unique_ods, due=True, duaIterate=True
        )

        # -----------------------------
        # 2. MLflow (Artifact storage, Experiment tracking)
        # -----------------------------
        log_simulation_mlflow(run_id=run.info.run_id)

        # -----------------------------
        # 3. GUI replay (optional, replays the last episode then exits)
        # -----------------------------
        if config.last_episode_gui_BM:
            run_final_simulation()

    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


if __name__ == "__main__":
    main()
