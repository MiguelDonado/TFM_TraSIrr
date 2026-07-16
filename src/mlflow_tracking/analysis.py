"""
MLflow logging for the analysis phase of the experiment.

The experiment has two run types in MLflow:
  simulation (when running the BM training loop)  — logged by mlflow_tracking/simulation.py
  analysis (when running R analysis scripts on the simulation outputs)  — logged here

Analysis runs are tagged with the research question they cover. The link to
the underlying simulation runs is established via the shared
params.research_question value — any simulation run with that param set to
the same value belongs to this analysis.

Logs: git commit hash, research question tag, and the figures artifact
directory produced by the R script.
"""

import subprocess
from datetime import datetime

import mlflow

from mlflow_tracking.utils import set_up_mlflow


def log_analysis_run_MLflow(research_question, artifact_path):

    # 1. Initialize MLflow
    set_up_mlflow()

    # 2. Start run and set name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with mlflow.start_run(run_name=f"BM_analysis_{research_question}_{timestamp}"):

        # 3. Set tags
        _set_analysis_tags(research_question)

        # 4. Log parameters
        _log_params()

        # 5. Log artifacts
        _log_artifacts(artifact_path)


##############
# HELPERS
##############
def _set_analysis_tags(research_question):
    mlflow.set_tag("run_type", "analysis")
    mlflow.set_tag("algorithm", "BM")
    mlflow.set_tag("research_question", research_question)


def _log_params():
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    mlflow.log_param("git_commit", commit_hash)


def _log_artifacts(research_question_path):
    mlflow.log_artifact(research_question_path)