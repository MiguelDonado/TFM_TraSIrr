import mlflow
from config.config import config
import json
from tempfile import NamedTemporaryFile
import os
from paths import INTERNAL_DATA_DIR, PROCESSED_DATA_DIR, DUE_DATA_DIR
from pathlib import Path
from dataclasses import asdict


def config_to_mlflow_params(config):
    """
    Log only parameters that may vary across runs
    """
    return {
        # BM
        "learning_rate": config.learning_rate,
        "memory_level": config.memory_level,
        "warm_up": config.warm_up,
        # Demand calibration
        "target_congestion_ratio": (config.target_congestion_ratio),
        # Simulation
        "warm_up_time": config.warm_up_time,
        # OD space
        "max_size_od_space": config.max_size_od_space,
        # Routing
        "n_routes_per_OD": config.n_routes_per_OD,
        # Stopping rule
        "max_episodes": config.max_episodes,
        "tolerance_stopping_rule": (config.tolerance_stopping_rule),
        # dueIterate
        "dueIterate_max_iterations": (config.dueIterate_max_iterations),
        # Network
        "network": Path(config.network).stem,
    }


def log_simulation_mlflow():
    # Log important parameters
    mlflow.log_params(config_to_mlflow_params(config))

    # Log all parameters as artifcat
    config_dict = asdict(config)
    config_dict["mode"] = config.mode.value
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_dict, f, indent=4)

        temp_path = f.name

    mlflow.log_artifact(temp_path)

    os.remove(temp_path)

    # Log artifacts
    mlflow.log_artifact(INTERNAL_DATA_DIR)
    mlflow.log_artifact(PROCESSED_DATA_DIR)
    mlflow.log_artifact(DUE_DATA_DIR)
