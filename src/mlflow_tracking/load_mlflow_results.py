"""
Utilities for programmatically recovering artifact data from multiple MLflow runs.

Typical workflow
----------------
1. Run batch experiments via scripts/launcher.py (many simulation runs,
   each with different hyperparameters).
2. Use load_artifact_across_runs() to pull one artifact file from every
   matching run into a single concatenated DataFrame.
3. Feed that DataFrame into the R analysis scripts to answer a research question
   across the full parameter space.

MLflow API layers used
----------------------
mlflow (high-level)    — search_runs() returns a DataFrame of run metadata
MlflowClient (low-level) — download_artifacts() retrieves the actual files
                           from the artifact store
"""

import tempfile

import mlflow
import pandas as pd
from mlflow import MlflowClient

from mlflow_tracking.utils import set_tracking_uri

"""
Two layers of MLflow:
    - High-level API (mlflow): Returns pandas DataFrames
    - Low-level API (MlflowClient): You get access to the underlying tracking store

"""


def load_artifact_across_runs(
    artifact_path: str,
    filter_string: str,
    experiment_names: list[str],
    params_to_attach: list[str],
) -> pd.DataFrame:
    """
    Download one artifact file from every matching MLflow run and return
    all of them concatenated, with the run's relevant params as columns

    Parameters
    -----------
    artifact_path : str
        Path of the artifact *within* the run's artifact store, e.g.
        "DUE/BM/R-gap/refined_rgap.parquet".
        (Mirrors the directory structure logged by _log_mlflow_artifacts.)
    filter_string : str
        MLflow search filter, e.g. "tags.run_type = 'simulation'" or "tags.research_question = 'RQ2'"
    experiment_name : str
        Experiment to search
    params_to_attach: list[str]
        Which logged params to add as columns to the returned DataFrame.

    Returns
    -----------
    pd.DataFrame with all rows from all matched runs, plus a "run_id" column
    and one column per entry in params_to_attach.
    """
    # It is necessary, to tell Mlflow the location of our database
    # where it should search the runs
    set_tracking_uri()

    runs = mlflow.search_runs(
        experiment_names=experiment_names, filter_string=filter_string
    )

    if runs.empty:
        raise ValueError(f"No runs found for filter: '{filter_string}'")

    # Create the MLflow client needed to download artifacts
    client = MlflowClient()

    # Store dataframes
    frames = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Iterate over runs
        for _, run in runs.iterrows():
            run_id = run["run_id"]

            # Download and save desired file
            local_path = client.download_artifacts(
                run_id=run_id,
                path=artifact_path,
                # destination path
                dst_path=tmp_dir,
            )

            # Read file
            df = pd.read_parquet(local_path)

            # Add run_id column
            df["run_id"] = run_id

            # Add columns for each of the params to attach
            for param in params_to_attach:
                """
                In search_runs() MLflow stores parameters in the next way:
                col = "params.memory_level"
                So, here we are creating that, to recover the parameter value for current run
                """
                col = f"params.{param}"
                # Return if it exists the parameter value for the current run
                df[param] = run[col] if col in run.index else None
            frames.append(df)
        return pd.concat(frames, ignore_index=True)
