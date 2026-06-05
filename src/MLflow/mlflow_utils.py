import json
import os
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import mlflow
import pandas as pd

from config.config import config
from paths import (
    ARTIFACTS_STORAGE,
    BACKEND_DB,
    DUE_DATA_DIR,
    INTERNAL_DATA_DIR,
    POLICY_CHANGE_BM,
    PROCESSED_DATA_DIR,
    RGAP,
    RGAP_DUEITERATE,
    STATISTICS_PARQUET,
)


def set_up_mlflow():
    """
    We should explicitly control the location for both:
    1. backend database (mlflow.db) (metadata)
    2. artifact storage (mlruns/) (files)

    This function handles the setup for MLflow experiment tracking
    1. Set location for storage stuff
    2. Specify which experiment this run belongs to
    """
    experiment_name = "BM Thesis"

    # 1. Set location backend db
    mlflow.set_tracking_uri(f"sqlite:///{BACKEND_DB}")

    # 2. Check if experiment is already created.
    # If its not, create it
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(
            experiment_name, artifact_location=f"file://{ARTIFACTS_STORAGE}"
        )

    # 3. Specify which experiment this run belongs to
    mlflow.set_experiment(experiment_name)


def log_simulation_mlflow():

    # 1. Log RELEVANT hyperparameters
    mlflow.log_params(extract_mlflow_hyperparams(config))

    # 2. Log ALL hyperparameters as artifact
    log_config_artifact()

    # 3. Log metrics
    log_mlflow_metrics()

    # Log artifacts
    log_mlflow_artifacts()


##########
# HELPERS
##########
def extract_mlflow_hyperparams(config):
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
        # dueIterate
        "dueIterate_max_iterations": (config.dueIterate_max_iterations),
        # Network
        "network": Path(config.network).stem,
    }


def log_config_artifact():
    config_dict = asdict(config)
    config_dict["mode"] = config.mode.value
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_dict, f, indent=4)

        temp_path = f.name

    mlflow.log_artifact(temp_path)

    os.remove(temp_path)


def log_mlflow_metrics():

    # 1. Log Rgap related metrics
    log_rgap_metrics()

    # 2. Log additional BM metrics
    log_BM_metrics()


def log_rgap_metrics():
    # 1. Log Rgap metrics related to BM algorithm
    log_BM_rgap_metric()

    # 2. Log Rgap metrics related to dueIterate
    log_dueIterate_rgap_metric()


def log_BM_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_BM = pd.read_parquet(RGAP)
    # 2. Log time series of the Rgap metric
    metric_name = "bm_rgap"
    col_metric = "rgap"
    col_step = "episode"

    __log_metric_over_time(
        df=df_rgap_BM, metric_name=metric_name, col_metric=col_metric, col_step=col_step
    )


def log_dueIterate_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for dueIterate algorithm
    # Right now, in dueIterate we are only keeping track of rgap of last episode
    df_rgap_dueIterate = pd.read_parquet(RGAP_DUEITERATE)

    # 2. Log time series of the Rgap metric
    # (right now dueIterate only contains one timestep, so its a scalar)
    dueiterate_final_rgap = float(df_rgap_dueIterate["rgap"].iloc[-1])
    rgap_metric = {"dueiterate_final_rgap": round(dueiterate_final_rgap, 5)}
    mlflow.log_metrics(rgap_metric)


def log_BM_metrics():
    # 1. Episodes required for convergence
    log_BM_episode_convergence()

    # 2. Mean travel time (time series)
    log_BM_mean_travel_time()

    # 3. Policy change (time series)
    log_BM_policy_change()


def log_BM_episode_convergence():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_BM = pd.read_parquet(RGAP)
    # 2. Get last episode
    last_row_rgap_BM = df_rgap_BM.iloc[-1]
    bm_episode_convergence = last_row_rgap_BM["episode"]

    # Log metrics
    metric = {
        "BM_episodes_to_convergence": bm_episode_convergence,
    }
    mlflow.log_metrics(metric)


def log_BM_mean_travel_time():
    # 1. Read parquet file that contains "episode | mean_travel_time" for BM algorithm
    df_mean_tt_BM = pd.read_parquet(STATISTICS_PARQUET)
    # 2. Log BM mean travel time over time (series)
    metric_name = "bm_mean_travel_time"
    col_metric = "mean_travel_time"
    col_step = "episode"
    __log_metric_over_time(
        df=df_mean_tt_BM,
        metric_name=metric_name,
        col_metric=col_metric,
        col_step=col_step,
    )


def log_BM_policy_change():
    # 1. Read parquet file that contains "episode | mean_policy_change"
    df_policy_change_BM = pd.read_parquet(POLICY_CHANGE_BM)

    # 2. Log BM mean_policy_change over time
    metric_name = "bm_mean_policy_change"
    col_metric = "mean_policy_change"
    col_step = "episode"
    __log_metric_over_time(
        df=df_policy_change_BM,
        metric_name=metric_name,
        col_metric=col_metric,
        col_step=col_step,
    )


def log_mlflow_artifacts():
    mlflow.log_artifact(INTERNAL_DATA_DIR)
    mlflow.log_artifact(PROCESSED_DATA_DIR)
    mlflow.log_artifact(DUE_DATA_DIR)


def __log_metric_over_time(df, metric_name, col_metric, col_step):
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
