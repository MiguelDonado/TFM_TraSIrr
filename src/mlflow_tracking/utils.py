"""
MLflow initialisation called once before any run is started.

Without explicit setup, MLflow defaults to storing everything in the
current working directory, which scatters files unpredictably across
the project. This module pins two storage locations:

  Backend (metadata)  — SQLite database at mlflow_db/mlflow.db
                        stores run parameters, metrics, and tags
  Artifact store      — file system directory at mlruns/mlruns/
                        stores files (artifacts) (parquet, JSON, plots)

Runs are grouped under the experiment named "Thesis" if no environment variable
is set when executing the program or under the value of the environment variable
MLFLOW_EXPERIMENT_NAME.
"""

import os

import mlflow

from config.paths import ARTIFACTS_STORAGE, BACKEND_DB


def set_tracking_uri():
    """
    Set location backend db
    """
    mlflow.set_tracking_uri(f"sqlite:///{BACKEND_DB}")


def set_up_mlflow():
    """
    We should explicitly control the location for both:
    1. backend database (mlflow.db) (metadata)
    2. artifact storage (mlruns/) (files)

    This function handles the setup for MLflow experiment tracking
    1. Set location for storage stuff
    2. Specify which experiment this run belongs to
    """

    # Two behaviours:
    # 1. No environment variable: Uses "Thesis"
    # 2. Environment variable: Uses whatever name we set when passing the environment variable
    # e.g. MLFLOW_EXPERIMENT_NAME=api-test python src/main.py <config.yaml>
    experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME","Thesis")

    # 1. Set location backend db
    set_tracking_uri()

    # 2. Check if experiment is already created.
    # If its not, create it
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(
            experiment_name, artifact_location=ARTIFACTS_STORAGE
        )

    # 3. Specify which experiment this run belongs to
    mlflow.set_experiment(experiment_name)
