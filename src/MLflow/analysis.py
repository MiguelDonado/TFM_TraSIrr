import subprocess

import mlflow

from config.config import config
from MLflow.simulation import set_up_mlflow
from paths import MLFLOW


def log_analysis_run_MLflow(research_question, research_question_path):

    # 1. Initialize MLflow
    set_up_mlflow()

    # 2. Recover MLflow simulation run id
    source_run_id = (MLFLOW / "source_run_id.txt").read_text().strip()

    # 3. Start run and set name
    with mlflow.start_run(run_name=build_analysis_run_name(source_run_id)):

        # 4. Set tags
        set_analysis_tags(source_run_id, research_question)

        # 5. Log info
        _log_info(research_question_path)


def build_analysis_run_name(source_run_id):
    return f"BM_analysis_{config.config_name}_{source_run_id[:8]}"


def set_analysis_tags(source_run_id, research_question):
    mlflow.set_tag("source_run_id", source_run_id)
    mlflow.set_tag("run_type", "analysis")
    mlflow.set_tag("algorithm", "BM")
    mlflow.set_tag("research question", research_question)


##############
# HELPERS
##############


def _log_info(research_question_path):

    # Log git commit
    _log_git_commit()

    # Log plots
    _log_artifacts(research_question_path)


def _log_git_commit():
    # 1.2. Log hyperparameter related to git commit
    # Useful, because maybe in six months from now I wanna look which code produced a surprising good result
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    mlflow.log_param("git_commit", commit_hash)


def _log_artifacts(research_question_path):
    mlflow.log_artifact(research_question_path)
