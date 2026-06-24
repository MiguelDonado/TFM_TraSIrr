"""
MLflow logging for the simulation phase of the experiment.

The experiment has two run types in MLflow:
  simulation (when running the BM training loop)  — logged here
  analysis (when running R analysis scripts on the simulation outputs)  — logged by mlflow_tracking/analysis.py

Each simulation run is tagged with its own run_id so it can be linked
to its corresponding analysis run in the MLflow UI without relying on
run names or timestamps.

Logs
----
Parameters  — learning_rate, memory_level, target_congestion_ratio,
              network name, git commit hash
Metrics     — bm_rgap (time series), BM mean_tt (time series),
              BM mean_pol_change (time series), BM ep_to_conv (scalar),
              duaIterate_final_rgap (scalar)
Artifacts   — full config JSON, agent_state/, processed/, DUE/ directories
"""

import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import mlflow
import pandas as pd

from config.config import config, path
from config.paths import (
    AGENT_STATE_DIR,
    BM_PATHS,
    DUA_EXTRA,
    DUA_PATHS,
    DUE_DATA_DIR,
    EXPERIMENTS_TMP,
    MLFLOW_SOURCE_RUN_ID,
    POLICY_CHANGE_BM,
    PROCESSED_DATA_DIR,
    STATISTICS_PARQUET,
)


def log_simulation_mlflow(run_id):

    # 1. Log relevant parameters
    _log_mlflow_params()

    # 2. Log ALL hyperparameters as artifact
    _log_config_artifact()

    # 3. Log metrics
    _log_mlflow_metrics()

    # 4. Log artifacts
    _log_mlflow_artifacts()

    # 5. Set tags
    set_simulation_tags(run_id)


def save_simulation_run_id(run_id):
    """
    This function saves the run_id of the simulation run, so that
    following analysis run can identify the simulation run id, and
    use it to identify the simulation run is analysing
    """
    with open(MLFLOW_SOURCE_RUN_ID, "w") as f:
        f.write(run_id)


def set_simulation_tags(run_id):
    mlflow.set_tag("source_run_id", run_id)
    mlflow.set_tag("run_type", "simulation")
    mlflow.set_tag("algorithm", "BM")
    run_name = (
        f"BM_simulation_mem{config.memory_level}_l{config.learning_rate}_{run_id[:6]}"
    )
    mlflow.set_tag("mlflow.runName", run_name)


def build_simulation_run_name():
    config_path = Path(path).stem
    return f"BM_simulation_mem{config.memory_level}_l{config.learning_rate}"


##########
# HELPERS
##########
def _log_mlflow_params():
    # 1. Log RELEVANT hyperparameters
    mlflow.log_params(_extract_mlflow_hyperparams(config))

    # 2. Log hyperparameter related to git commit
    # Useful, because maybe in six months from now I wanna look which code produced a surprising good result
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    mlflow.log_param("git_commit", commit_hash)

    # 3. Log YAML config file used
    # mlflow.log_param("config_YAML", path)

    # 4. Log seed
    mlflow.log_param("seed", config.seed)


def _extract_mlflow_hyperparams(config):
    """
    Log only hyperparameters that may vary across runs
    """

    return {
        # BM
        "learning_rate": config.learning_rate,
        "memory_level": config.memory_level,
        # "warm_up": config.warm_up,
        # Demand calibration
        "target_congestion_ratio": (config.target_congestion_ratio),
        # # Simulation
        # "warm_up_time": config.warm_up_time,
        # # OD space
        # "max_size_od_space": config.max_size_od_space,
        # # Routing
        # "n_routes_per_OD": config.n_routes_per_OD,
        # # Stopping rule
        # "max_episodes": config.max_episodes,
        # "tolerance_stopping_rule": (config.tolerance_stopping_rule),
        # # duaIterate
        # "duaIterate_max_iterations": (config.duaIterate_max_iterations),
        # Network
        "network": Path(config.network).stem,
        # # Configuration YAML used
        # "config_name": config.config_name,
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
    # 1. Log BM metrics
    _log_bm_metrics()

    # 2. Log duaIterate metrics
    _log_duaIterate_metrics()


def _log_bm_metrics():
    # 0. Log Rgap metric related to BM algorithm (all episodes) :  Series
    _log_bm_rgap_metric()

    # 1. Episodes required for convergence
    _log_bm_episode_convergence()

    # 2. Mean travel time (time series)
    _log_bm_mean_travel_time()

    # 3. Policy change (time series)
    _log_bm_policy_change()


def _log_bm_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_bm = pd.read_parquet(BM_PATHS.rgap)
    # 2. Log time series of the Rgap metric
    metric_name = "bm_rgap"
    col_metric = "rgap"
    col_step = "episode"

    _log_metric_over_time(
        df=df_rgap_bm, metric_name=metric_name, col_metric=col_metric, col_step=col_step
    )


def _log_bm_episode_convergence():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_bm = pd.read_parquet(BM_PATHS.rgap)
    # 2. Get last episode
    last_row_rgap_bm = df_rgap_bm.iloc[-1]
    bm_episode_convergence = last_row_rgap_bm["episode"]

    # Log metrics
    metric = {
        "ep_to_conv": bm_episode_convergence,
    }
    mlflow.log_metrics(metric)


def _log_bm_mean_travel_time():
    # 1. Read parquet file that contains "episode | mean_travel_time" for BM algorithm
    df_mean_tt_bm = pd.read_parquet(STATISTICS_PARQUET)
    # 2. Log BM mean travel time over time (series)
    metric_name = "mean_tt"
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
    metric_name = "mean_pol_change"
    col_metric = "mean_policy_change"
    col_step = "episode"
    _log_metric_over_time(
        df=df_policy_change_bm,
        metric_name=metric_name,
        col_metric=col_metric,
        col_step=col_step,
    )


def _log_duaIterate_metrics():
    # 1. Log Rgap metrics related to duaIterate (only last episode)
    _log_duaIterate_rgap_metric()

    # 2. Mean travel time (time series)
    # _log_duaIterate_mean_travel_time()


def _log_duaIterate_mean_travel_time():
    # 1. Read parquet file that contains "Iteration | Mean_travel_time"
    df_mean_tt_duaIterate = pd.read_parquet(DUA_EXTRA.mean_tt)

    # 2. Log duaIterate mean travel time over time (series)
    metric_name = "duaIterate_mean_travel_time"
    col_metric = "Mean_travel_time"
    col_step = "Iteration"
    _log_metric_over_time(
        df=df_mean_tt_duaIterate,
        metric_name=metric_name,
        col_metric=col_metric,
        col_step=col_step,
    )


def _log_duaIterate_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for duaIterate algorithm
    df_rgap_duaIterate = pd.read_parquet(DUA_PATHS.rgap)

    # 2. Log time series of the Rgap metric
    # (it only contains one value correspondent to the last episode) so its a scalar
    duaIterate_final_rgap = float(df_rgap_duaIterate["rgap"].iloc[-1])
    rgap_metric = {"duaIterate_final_rgap": round(duaIterate_final_rgap, 5)}
    mlflow.log_metrics(rgap_metric)


def _log_mlflow_artifacts():
    mlflow.log_artifact(EXPERIMENTS_TMP)
    mlflow.log_artifact(AGENT_STATE_DIR)
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
