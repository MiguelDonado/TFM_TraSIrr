"""
Renders the Quarto report for a research question and logs results to MLflow.

Usage:
  python scripts/run_analysis.py <research_question>              full pipeline
  python scripts/run_analysis.py <research_question> --prepare-only  data prep only

Steps:
  1. Prepare data — pull simulation artifacts from MLflow across all runs
     for the given research question and write combined parquets to r/<RQ>/data/.
     Each artifact is downloaded from every matching run and concatenated into a
     single DataFrame. params_to_attach controls which MLflow params (e.g. seed,
     n_agents) are added as columns, so each row in the combined DataFrame can be
     identified by the run (combination) it came from. run_id is always added automatically.
  2. Render      — run quarto render on r/<RQ>/<RQ>.qmd.  (skipped with --prepare-only)
  3. Log         — log the rendered report and figures as an MLflow analysis run.  (skipped with --prepare-only)

--prepare-only is useful when developing R scripts

----- Evaluation runs analyzed -----
Analysis will be performed for runs tagged with status = "active".
Runs tagged with status = "archived" will not be analyzed.
Runs logged with config_name = "development" (e.g. from a design_dev.yaml
sweep) are also excluded, so dev-scale runs never mix into the report.

----- Valid Research Questions arguments -----
RQ1
RQ2
RQ3
RQ4

"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR
from mlflow_tracking.analysis import log_analysis_run_MLflow
from mlflow_tracking.load_mlflow_results import load_artifact_across_runs


def run_analysis_rq():
    """Execute a research question analysis and log results to MLflow."""

    research_question = sys.argv[1]
    if not re.match(r"^RQ\d+$", research_question):
        sys.exit(f"Invalid research question '{research_question}'. Expected format: RQ1, RQ2, ...")
    prepare_only = "--prepare-only" in sys.argv

    _prepare_data(research_question)

    if prepare_only:
        return

    _render_analysis(research_question)
    log_analysis_run_MLflow(
        research_question=research_question,
        artifact_path=BASE_DIR / "r" / research_question,
    )

    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


def _prepare_data(research_question: str) -> None:
    """Download and combine MLflow artifacts for the given research question."""
    if research_question == "RQ1":
        _prepare_rq1_data()
    elif research_question == "RQ2":
        _prepare_rq2_data()
    elif research_question == "RQ3":
        _prepare_rq3_data()
    elif research_question == "RQ4":
        _prepare_rq4_data()


def _prepare_rq1_data() -> None:
    """Pull R-gap artifacts from all RQ1 simulation runs and save combined parquets."""
    filter_string = (
        "tags.research_question = 'RQ1' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "n_agents", "warm_up"]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "bm_rgap_by_od": "DUE/BM/R-gap/rgap_by_od.parquet",
        "bm_refined_rgap": "DUE/BM/R-gap/refined_rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "dua_rgap_by_od": "DUE/duaIterate/R-gap/rgap_by_od.parquet",
        "dua_refined_rgap": "DUE/duaIterate/R-gap/refined_rgap.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ1" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq2_data() -> None:
    """Pull R-gap artifacts from all RQ2 simulation runs and save combined parquets."""
    filter_string = (
        "tags.research_question = 'RQ2' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "memory_level", "n_agents", "warm_up"]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "od_routes": "environment/od_routes.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "cost_paths": "DUE/BM/costs_paths_odtp_k.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ2" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq3_data() -> None:
    """Pull R-gap artifacts from all RQ3 simulation runs and save combined parquets."""
    filter_string = (
        "tags.research_question = 'RQ3' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "learning_rate", "n_agents", "warm_up"]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "bm_policy_change": "agent_state/policy_change_BM.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "od_routes": "environment/od_routes.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "cost_paths": "DUE/BM/costs_paths_odtp_k.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ3" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq4_data() -> None:
    """Pull R-gap artifacts from all RQ4 simulation runs and save combined parquets."""
    filter_string = (
        "tags.research_question = 'RQ4' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = [
        "seed",
        "n_agents",
        "network_degraded",
        "degradation_start_episode",
        "degradation_end_episode",
        "warm_up"
    ]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "bm_edgedata": "processed/edgedata.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ4" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _render_analysis(research_question: str) -> None:
    """Render the Quarto report for a research question."""
    qmd_file = BASE_DIR / f"r/{research_question}/{research_question}.qmd"

    subprocess.run(
        [
            "/usr/lib/rstudio/resources/app/bin/quarto/bin/quarto",
            "render",
            str(qmd_file),
        ],
        check=True,
    )


if __name__ == "__main__":
    run_analysis_rq()
