"""
MLflow logging for the analysis phase of the experiment.

The experiment has two run types in MLflow:
  simulation (when running the BM training loop)  — logged by mlflow_tracking/simulation.py
  analysis (when running R analysis scripts on the simulation outputs)  — logged here

Each analysis run is tagged with the source_run_id of the simulation run
it analyses, so the two can be linked in the MLflow UI without relying
on run names or timestamps.

Logs: git commit hash, research question tag, and the figures artifact
directory produced by the R script.
"""

import subprocess

import mlflow

from config.paths import MLFLOW_SOURCE_RUN_ID
from mlflow_tracking.utils import set_up_mlflow


def log_analysis_run_MLflow(research_question, artifact_path):

    # 1. Initialize MLflow
    set_up_mlflow()

    # 2. Recover MLflow simulation run id
    source_run_id = MLFLOW_SOURCE_RUN_ID.read_text().strip()

    # 3. Start run and set name
    with mlflow.start_run(
        run_name=_build_analysis_run_name(research_question, source_run_id)
    ):

        # 4. Set tags
        _set_analysis_tags(source_run_id, research_question)

        # 5. Log parameters
        _log_params

        # 6. Log artifacts
        _log_artifacts(artifact_path)


##############
# HELPERS
##############
def _build_analysis_run_name(research_question, source_run_id):
    return f"BM_analysis_{research_question}_{source_run_id[:6]}"


def _set_analysis_tags(source_run_id, research_question):
    mlflow.set_tag("source_run_id", source_run_id)
    mlflow.set_tag("run_type", "analysis")
    mlflow.set_tag("algorithm", "BM")
    mlflow.set_tag("research_question", research_question)


def _log_params():
    # Log git commit
    _log_git_commit()


def _log_git_commit():
    # 1.2. Log hyperparameter related to git commit
    # Useful, because maybe in six months from now I wanna look which code produced a surprising good result
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    mlflow.log_param("git_commit", commit_hash)


def _log_artifacts(research_question_path):
    mlflow.log_artifact(research_question_path)
