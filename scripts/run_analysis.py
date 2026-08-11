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
RQ5
RQ7
RQ8

"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import mlflow
from mlflow import MlflowClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR
from mlflow_tracking.analysis import log_analysis_run_MLflow
from mlflow_tracking.load_mlflow_results import load_artifact_across_runs
from mlflow_tracking.utils import set_tracking_uri


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
    elif research_question == "RQ5":
        _prepare_rq5_data()
    elif research_question == "RQ7":
        _prepare_rq7_data()
    elif research_question == "RQ8":
        _prepare_rq8_data()


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
        "warm_up",
        "memory_level"
    ]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "bm_edgedata": "processed/edgedata.parquet",
        # "od_routes": "DUE/duaIterate/od_routes.parquet",
        "od_routes": "environment/od_routes.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
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

def _prepare_rq5_data() -> None:
    """Pull R-gap artifacts from all RQ5 simulation runs and save combined parquets."""
    filter_string = (
        "tags.research_question = 'RQ5' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'development'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = [
        "seed",
        "n_agents",
        "network_degraded",
        "degradation_start_episode",
        "degradation_end_episode",
        "warm_up",
        "memory_mean",
        "heterogeneous_memory"
    ]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "bm_edgedata": "processed/edgedata.parquet",
        # "od_routes": "DUE/duaIterate/od_routes.parquet",
        "od_routes": "environment/od_routes.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "bm_results": "agent_state/BM_results.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ5" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq7_data() -> None:
    """
    Pull the edge-flow visualization inputs (BM/duaIterate edgedata,
    times_interval, and both algorithms' last-episode/iteration routes)
    from the single RQ7 simulation run and save them into r/RQ7/data/.

    Unlike RQ1-5, RQ7's design.yaml is a single combination (a qualitative
    sumo-gui case study, not a multi-seed statistical comparison), so this
    downloads one run's artifacts directly instead of concatenating across
    many runs with load_artifact_across_runs.
    """
    filter_string = (
        "tags.research_question = 'RQ7' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]

    set_tracking_uri()
    runs = mlflow.search_runs(
        experiment_names=experiment_names, filter_string=filter_string
    )
    if runs.empty:
        raise ValueError(f"No runs found for filter: '{filter_string}'")
    if len(runs) > 1:
        raise ValueError(
            f"Expected exactly one RQ7 run, found {len(runs)}. "
            "RQ7's design.yaml should define a single combination — "
            "archive the extra runs (tags.status = 'archived') before re-running."
        )
    run_id = runs.iloc[0]["run_id"]

    # Used in RQ7_part2 to build the geometry of the network and paths for the visualization 
    network_stem = runs.iloc[0]["params.network"]

    artifacts = {
        "bm_edgedata.parquet": "processed/edgedata.parquet",
        "dua_edgedata.parquet": "DUE/duaIterate/edgedata/edgedata.parquet",
        "times_interval.parquet": "environment/times_interval.parquet",
        "routes_bm.rou.xml": "DUE/BM/routes_last_episode.rou.xml",
        "routes_dua.rou.xml": "DUE/duaIterate/routes_last_iteration.rou.xml",
        # RQ7_part2 (OD/path-level route composition) inputs
        "demand_odt.parquet": "DUE/generic/demand_odt.parquet",
        "od_routes_bm.parquet": "environment/od_routes.parquet",
        "od_routes_dua.parquet": "DUE/duaIterate/od_routes.parquet",
        "flows_bm.parquet": "DUE/BM/flows_paths_odtp_k.parquet",
        "flows_dua.parquet": "DUE/duaIterate/flows_paths_odtp_k.parquet",
    }

    data_dir = BASE_DIR / "r" / "RQ7" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "network_stem.txt").write_text(network_stem)

    client = MlflowClient()
    with tempfile.TemporaryDirectory() as tmp_dir:
        for local_name, artifact_path in artifacts.items():
            downloaded_path = client.download_artifacts(
                run_id=run_id, path=artifact_path, dst_path=tmp_dir
            )
            shutil.copy2(downloaded_path, data_dir / local_name)


def _prepare_rq8_data() -> None:
    """
    Pull BM and duaIterate route/flow artifacts from every RQ8 run  
    and save combined parquets into r/RQ8/data/.

    duaIterate's routes/flows don't depend on BM's memory_level (only on
    seed), so the "od_routes_dua"/"flows_dua" artifacts end up with one
    duplicate copy per memory_level within each seed — harmless, in 
    R they will be dedupe
    """
    filter_string = (
        "tags.research_question = 'RQ8' and tags.run_type = 'simulation' "
        "and tags.status != 'archived' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "memory_level"]

    artifacts = {
        "od_routes_bm": "environment/od_routes.parquet",
        "flows_bm": "DUE/BM/flows_paths_odtp_k.parquet",
        "od_routes_dua": "DUE/duaIterate/od_routes.parquet",
        "flows_dua": "DUE/duaIterate/flows_paths_odtp_k.parquet",
    }

    data_dir = BASE_DIR / "r" / "RQ8" / "data"
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
    """Render the Quarto report(s) for a research question."""
    rq_dir = BASE_DIR / "r" / research_question

    if research_question in ("RQ4", "RQ7"):
        qmd_files = [rq_dir / f"{research_question}.qmd", rq_dir / f"{research_question}_part2.qmd"]
    else:
        qmd_files = [rq_dir / f"{research_question}.qmd"]

    for qmd_file in qmd_files:
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
