from pathlib import Path

import mlflow

from config.config import config
from paths import ARTIFACTS_STORAGE, BACKEND_DB


def set_up_mlflow():
    """
    We should explicitly control the location for both:
    1. backend database (mlflow.db) (metadata)
    2. artifact storage (mlruns/) (files)

    This function handles the setup for MLflow experiment tracking
    1. Set location for storage stuff
    2. Specify which experiment this run belongs to
    """
    experiment_name = config.experiment_name

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
