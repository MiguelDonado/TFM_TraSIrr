"""
MLflow logging for the simulation phase of the experiment.

The experiment has two run types in MLflow:
  simulation (when running the BM training loop)  — logged here
  analysis (when running R analysis scripts on the simulation outputs)  — logged by mlflow_tracking/analysis.py

Simulation runs are linked to their analysis run via the shared
params.research_question value.

Logs
----
Parameters  — full config (seed, n_agents, learning_rate, memory_level,
              network name, git commit hash, ...)
Metrics     — bm_rgap_pct (time series), mean_tt (time series),
              mean_pol_change (time series), ep_to_conv (scalar),
              duaIterate_final_rgap_pct (scalar)
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

from config.config import config
from config.paths import (
    AGENT_STATE_DIR,
    BM_PATHS,
    DUA_PATHS,
    DUE_DATA_DIR,
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


def set_simulation_tags(run_id):
    mlflow.set_tag("run_type", "simulation")
    mlflow.set_tag("algorithm", "BM")
    if config.research_question:
        mlflow.set_tag("research_question", config.research_question)
    run_name = f"BM_s{config.seed}_n{config.n_agents}_mem{config.memory_level}_l{config.learning_rate}_{run_id[:6]}"
    mlflow.set_tag("mlflow.runName", run_name)


##########
# HELPERS
##########
def _log_mlflow_params():
    config_dict = asdict(config)
    config_dict["network"] = Path(config.network).stem
    config_dict["episodes_gui"] = list(config.episodes_gui)

    # 2. Log hyperparameter related to git commit
    # Useful, because maybe in six months from now I wanna look which code produced a surprising good result
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    config_dict["git_commit"] = commit_hash

    mlflow.log_params(config_dict)


def _log_config_artifact():
    config_dict = asdict(config)
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

    # 2. Mean travel time (time series)
    _log_bm_mean_travel_time()

    # 3. Policy change (time series)
    _log_bm_policy_change()


def _log_bm_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for BM algorithm
    df_rgap_bm = pd.read_parquet(BM_PATHS.rgap)
    # 2. Log time series of the Rgap metric
    metric_name = "bm_rgap_pct"
    col_metric = "rgap"
    col_step = "episode"

    _log_metric_over_time(
        df=df_rgap_bm, metric_name=metric_name, col_metric=col_metric, col_step=col_step
    )
    mlflow.log_metric("ep_to_conv", int(df_rgap_bm["episode"].iloc[-1]))


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
    _log_duaIterate_rgap_metric()


def _log_duaIterate_rgap_metric():
    # 1. Read parquet file that contains "episode | rgap" for duaIterate algorithm
    df_rgap_duaIterate = pd.read_parquet(DUA_PATHS.rgap)

    # 2. Log time series of the Rgap metric
    # (it only contains one value correspondent to the last episode) so its a scalar
    duaIterate_final_rgap = float(df_rgap_duaIterate["rgap"].iloc[-1])
    rgap_metric = {"duaIterate_final_rgap_pct": round(duaIterate_final_rgap, 5)}
    mlflow.log_metrics(rgap_metric)


def _log_mlflow_artifacts():
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
