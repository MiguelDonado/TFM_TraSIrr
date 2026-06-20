import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import mlflow
import pandas as pd

from config.config import config
from paths import (
    DUE_DATA_DIR,
    INTERNAL_DATA_DIR,
    MLFLOW,
    POLICY_CHANGE_BM,
    PROCESSED_DATA_DIR,
    RGAP,
    STATISTICS_PARQUET,
    RGAP_duaIterate,
)

from .utils import set_up_mlflow


def log_simulation_mlflow():

    # 1. Log RELEVANT hyperparameters
    mlflow.log_params(_extract_mlflow_hyperparams(config))

    # 1.2. Log hyperparameter related to git commit
    # Useful, because maybe in six months from now I wanna look which code produced a surprising good result
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    mlflow.log_param("git_commit", commit_hash)

    # 2. Log ALL hyperparameters as artifact
    _log_config_artifact()

    # 3. Log metrics
    _log_mlflow_metrics()

    # Log artifacts
    _log_mlflow_artifacts()


def save_simulation_run_id(run_id):
    path = MLFLOW / "source_run_id.txt"
    with open(path, "w") as f:
        f.write(run_id)


def set_simulation_tags(run_id):
    mlflow.set_tag("source_run_id", run_id)
    mlflow.set_tag("run_type", "simulation")
    mlflow.set_tag("algorithm", "BM")


def build_simulation_run_name():
    return f"BM_simulation_{config.config_name}"


##########
# HELPERS
##########
def _extract_mlflow_hyperparams(config):
    """
    Log only hyperparameters that may vary across runs
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
        # duaIterate
        "duaIterate_max_iterations": (config.duaIterate_max_iterations),
        # Network
        "network": Path(config.network).stem,
        # Configuration YAML used
        "config_name": config.config_name,
    }


def _log_config_artifact():
    config_dict = asdict(config)
    config_dict["mode"] = config.mode.value
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_dict, f, indent=4)

        temp_path = f.name

    mlflow.log_artifact(temp_path)

    os.remove(temp_path)


def _log_mlflow_metrics():

    # 1. Log Rgap related metrics
    _log_rgap_metrics()

    # 2. Log additional BM metrics
    _log_bm_metrics()


def _log_rgap_metrics():
    # 1. Log Rgap metrics related to BM algorithm
    _log_bm_rgap_metric()

    # 2. Log Rgap metrics related to duaIterate
    _log_duaIterate_rgap_metric()


def _log_bm_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_bm = pd.read_parquet(RGAP)
    # 2. Log time series of the Rgap metric
    metric_name = "bm_rgap"
    col_metric = "rgap"
    col_step = "episode"

    _log_metric_over_time(
        df=df_rgap_bm, metric_name=metric_name, col_metric=col_metric, col_step=col_step
    )


def _log_duaIterate_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for duaIterate algorithm
    # Right now, in duaIterate we are only keeping track of rgap of last episode
    df_rgap_duaIterate = pd.read_parquet(RGAP_duaIterate)

    # 2. Log time series of the Rgap metric
    # (right now duaIterate only contains one timestep, so its a scalar)
    duaIterate_final_rgap = float(df_rgap_duaIterate["rgap"].iloc[-1])
    rgap_metric = {"duaIterate_final_rgap": round(duaIterate_final_rgap, 5)}
    mlflow.log_metrics(rgap_metric)


def _log_bm_metrics():
    # 1. Episodes required for convergence
    _log_bm_episode_convergence()

    # 2. Mean travel time (time series)
    _log_bm_mean_travel_time()

    # 3. Policy change (time series)
    _log_bm_policy_change()


def _log_bm_episode_convergence():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_bm = pd.read_parquet(RGAP)
    # 2. Get last episode
    last_row_rgap_bm = df_rgap_bm.iloc[-1]
    bm_episode_convergence = last_row_rgap_bm["episode"]

    # Log metrics
    metric = {
        "BM_episodes_to_convergence": bm_episode_convergence,
    }
    mlflow.log_metrics(metric)


def _log_bm_mean_travel_time():
    # 1. Read parquet file that contains "episode | mean_travel_time" for BM algorithm
    df_mean_tt_bm = pd.read_parquet(STATISTICS_PARQUET)
    # 2. Log BM mean travel time over time (series)
    metric_name = "bm_mean_travel_time"
    col_metric = "mean_travel_time"
    col_step = "episode"
    _log_metric_over_time(
        df=df_mean_tt_bm,
        metric_name=metric_name,
        col_metric=col_metric,
        col_step=col_step,
    )


def _log_bm_policy_change():
    # 1. Read parquet file that contains "episode | mean_policy_change"
    df_policy_change_bm = pd.read_parquet(POLICY_CHANGE_BM)

    # 2. Log BM mean_policy_change over time
    metric_name = "bm_mean_policy_change"
    col_metric = "mean_policy_change"
    col_step = "episode"
    _log_metric_over_time(
        df=df_policy_change_bm,
        metric_name=metric_name,
        col_metric=col_metric,
        col_step=col_step,
    )


def _log_mlflow_artifacts():
    mlflow.log_artifact(INTERNAL_DATA_DIR)
    mlflow.log_artifact(PROCESSED_DATA_DIR)
    mlflow.log_artifact(DUE_DATA_DIR)


def _log_metric_over_time(df, metric_name, col_metric, col_step):
    """
    This function gets as input a df containing a time series of a metric.
    And it logs to MLflow the metric over time.
    This way, we can have in MLflow UI, plots visualizing the time series
    of the metric.

    Arguments explanation:
    df: It contains the timesteps and the metric value for each timestep
    col_metric: Name of the column in the dataframe that corresponds to the metric value
    col_step: Name of the column in the dataframe that corresponds to the timestep
    """

    # 1. Copy df to prevent modifying original object
    df = df.copy()
    # 2. Log metric at each timesteps
    for _, row in df.iterrows():
        mlflow.log_metric(metric_name, row[col_metric], step=int(row[col_step]))
