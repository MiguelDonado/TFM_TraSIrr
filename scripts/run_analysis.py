"""
Renders the Quarto report for a research question and logs results to MLflow.

Usage:
  python run_analysis.py <research_question>              full pipeline
  python run_analysis.py <research_question> --prepare-only  data prep only

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
"""

import os
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


def _prepare_rq1_data() -> None:
    """Pull R-gap artifacts from all RQ1 simulation runs and save combined parquets."""
    filter_string = "params.research_question = 'RQ1' and tags.run_type = 'simulation'"
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "n_agents"]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "bm_rgap_by_od": "DUE/BM/R-gap/rgap_by_od.parquet",
        "bm_refined_rgap": "DUE/BM/R-gap/refined_rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "dua_rgap_by_od": "DUE/duaIterate/R-gap/rgap_by_od.parquet",
        "dua_refined_rgap": "DUE/duaIterate/R-gap/refined_rgap.parquet",
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
