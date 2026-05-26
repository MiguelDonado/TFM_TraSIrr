import mlflow
from config.config import config
import json
from tempfile import NamedTemporaryFile
import os
from paths import (
    INTERNAL_DATA_DIR,
    PROCESSED_DATA_DIR,
    DUE_DATA_DIR,
    RGAP,
    RGAP_DUEITERATE,
    STATISTICS_PARQUET,
    POLICY_CHANGE_BM,
)
from pathlib import Path
from dataclasses import asdict
import pandas as pd


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

    # Log metrics
    log_mlflow_metrics()

    # Log artifacts
    mlflow.log_artifact(INTERNAL_DATA_DIR)
    mlflow.log_artifact(PROCESSED_DATA_DIR)
    mlflow.log_artifact(DUE_DATA_DIR)


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


def log_mlflow_metrics():
    # 1. Log BM rgap related metrics
    df_rgap_BM = pd.read_parquet(RGAP)
    # 1.1. Log rgap metric overtime (series)
    __log_metric_over_time(
        df=df_rgap_BM, metric_name="bm_rgap", col_metric="rgap", col_step="episode"
    )
    # 1.2. Log final episode rgap (scalar)
    last_row_BM = df_rgap_BM.iloc[-1]
    bm_final_rgap = last_row_BM["rgap"]
    # 1.3. Log episodes to converge (scalar)
    bm_convergence_episodes = last_row_BM["episode"]

    # 2. Log BM mean travel time related metrics
    df_mean_tt_BM = pd.read_parquet(STATISTICS_PARQUET)
    # 2.1. Log BM mean travel time over time (series)
    __log_metric_over_time(
        df=df_mean_tt_BM,
        metric_name="bm_mean_travel_time",
        col_metric="mean_travel_time",
        col_step="episode",
    )
    # 2.2. Log final episode mean travel time (scalar)
    last_row_statistics_BM = df_mean_tt_BM.iloc[-1]
    bm_final_mean_tt = last_row_statistics_BM["mean_travel_time"]

    # 3. Log dueIterate final iteration rgap (scalar)
    df_rgap_dueIterate = pd.read_parquet(RGAP_DUEITERATE)
    dueiterate_final_rgap = df_rgap_dueIterate["rgap"]

    # 4. Log BM policy change
    df_policy_change_BM = pd.read_parquet(POLICY_CHANGE_BM)
    __log_metric_over_time(
        df=df_policy_change_BM,
        metric_name="bm_mean_policy_change",
        col_metric="mean_policy_change",
        col_step="episode",
    )

    # Log metrics
    mlflow_metrics = {
        "bm_final_rgap": round(bm_final_rgap, 5),
        "dueiterate_final_rgap": round(dueiterate_final_rgap, 5),
        "bm_convergence_episodes": bm_convergence_episodes,
        "bm_final_mean_travel_time": round(bm_final_mean_tt, 5),
    }
    mlflow.log_metrics(mlflow_metrics)


def __log_metric_over_time(df, metric_name, col_metric, col_step):
    df = df.copy()
    for _, row in df.iterrows():
        mlflow.log_metric(metric_name, row[col_metric], step=int(row[col_step]))
