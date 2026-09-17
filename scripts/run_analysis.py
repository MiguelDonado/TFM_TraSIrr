"""
Prepare data to be used in the research questions R analysis scripts.

Usage:
  python scripts/run_analysis.py <research_question>               data prep

Steps:
  1. Prepare data — pull simulation artifacts from MLflow across all runs
     for the given research question and write combined parquets to r/<RQ>/data/.
     Each artifact is downloaded from every matching run and concatenated into a
     single DataFrame. params_to_attach controls which MLflow params (e.g. seed,
     n_agents) are added as columns, so each row in the combined DataFrame can be
     identified by the run (combination) it came from. run_id is always added automatically.

----- Evaluation runs analyzed -----
Only runs tagged status = "active" are analyzed. A simulation run's status
tag goes through three states over its lifetime:

  (no tag)  — just performed by run_batch.py. Not yet analyzed: results
              haven't been checked in the MLflow UI yet, so they shouldn't
              be trusted into a report sight unseen.
  "active"  — manually promoted after reviewing the run's metrics in the
              MLflow UI and confirming they look right. Only active runs
              are pulled into analysis.
  "archived"— manually excluded, either because a newer sweep replaced it
              or because it was reviewed and rejected. Never analyzed.

The (no tag) -> "active" promotion is done by hand in the MLflow UI, on
purpose — it's the checkpoint where a run is actually looked at before
being trusted in a report. The (no tag) -> "archived" is also done by hand
in the MLflow UI.
The "active" -> "archived" and "archived" -> "no status" is bulk, via
scripts/manage_runs.py, since doing that one run at a time in the UI is
tedious for a full grid.

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
RQ9
RQ10
RQ11
RQ12
RQ13
"""

import re
import shutil
import sys
import tempfile
from pathlib import Path

import mlflow
from mlflow import MlflowClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR
from mlflow_tracking.load_mlflow_results import load_artifact_across_runs
from mlflow_tracking.utils import set_tracking_uri


def run_analysis_rq():

    research_question = sys.argv[1]
    if not re.match(r"^RQ\d+$", research_question):
        sys.exit(f"Invalid research question '{research_question}'. Expected format: RQ1, RQ2, ...")

    _prepare_data(research_question)

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
    elif research_question == "RQ9":
        _prepare_rq9_data()
    elif research_question == "RQ10":
        _prepare_rq10_data()
    elif research_question == "RQ11":
        _prepare_rq11_data()
    elif research_question == "RQ12":
        _prepare_rq12_data()
    elif research_question == "RQ13":
        _prepare_rq13_data()


def _prepare_rq1_data() -> None:
    """Pull R-gap artifacts from all RQ1 simulation runs and save combined parquets."""
    filter_string = (
        "tags.research_question = 'RQ1' and tags.run_type = 'simulation' "
        "and tags.status = 'active' and params.config_name = 'production'"
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
        "and tags.status = 'active' and params.config_name = 'production'"
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
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "learning_rate", "n_agents", "warm_up"]

    artifacts = {
        "agents_od": "environment/agents_od.parquet",
        "bm_results": "agent_state/BM_results.parquet",
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
        "and tags.status = 'active' and params.config_name = 'production'"
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
        "agents_od": "environment/agents_od.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "bm_edgedata": "processed/edgedata.parquet",
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
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = [
        "seed",
        "n_agents",
        "warm_up",
        "memory_mean",
        "heterogeneous_memory"
    ]

    artifacts = {
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "dua_rgap": "DUE/duaIterate/R-gap/rgap.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "od_routes": "environment/od_routes.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "cost_paths": "DUE/BM/costs_paths_odtp_k.parquet",
        "bm_results": "agent_state/BM_results.parquet"
        # "bm_edgedata": "processed/edgedata.parquet",
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
        "and tags.status = 'active' and params.config_name = 'production'"
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
        "and tags.status = 'active' and params.config_name = 'production'"
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

def _prepare_rq9_data() -> None:
    '''
    It uses the same runs that were performed for RQ2.
    '''
    filter_string = (
        "tags.research_question = 'RQ2' and tags.run_type = 'simulation' "
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "memory_level", "n_agents"]

    artifacts = {
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "od_routes": "environment/od_routes.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
    }

    data_dir = BASE_DIR / "r" / "RQ9" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq10_data() -> None:
    '''
    Pull the information about the network, and routes, as well as 
    the debug trace for an agent from the RQ10 simulation run and save
    them into r/RQ10/data/
    '''
    filter_string = (
        "tags.research_question = 'RQ10' and tags.run_type = 'simulation' "
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["memory_level", "network", "warm_up"]

    artifacts = {
        # Contains the json file that tracks all the learning process
        # for one particular agent
        "agent_debug_trace": "agent_state/agent_debug_trace.json",
        # Contains to which OD is assigned that agent
        "agents_od": "environment/agents_od.parquet",
        # Contains the routes for each OD
        "od_routes_bm": "environment/od_routes.parquet",
    }

    data_dir = BASE_DIR / "r" / "RQ10" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq11_data() -> None:
    '''
    Pull the needed information and save them into r/RQ11/data/
    '''
    filter_string = (
        "tags.research_question = 'RQ11' and tags.run_type = 'simulation' "
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "warm_up", "reliability_sensitivity"]

    artifacts = {
        "bm_results": "agent_state/BM_results.parquet",
        "agents_od": "environment/agents_od.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "od_routes": "environment/od_routes.parquet",
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "actions": "agent_state/actions.parquet",
        "rewards": "agent_state/rewards.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ11" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq12_data() -> None:
    '''
    Pull the needed information and save them into r/RQ12/data/
    '''
    filter_string = (
        "tags.research_question = 'RQ12' and tags.run_type = 'simulation' "
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "warm_up", "waiting_time_sensitivity", "network"]

    artifacts = {
        "bm_results": "agent_state/BM_results.parquet",
        "agents_od": "environment/agents_od.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "od_routes": "environment/od_routes.parquet",
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "actions": "agent_state/actions.parquet",
        "rewards": "agent_state/rewards.parquet",
        "trips_info": "processed/trips_info.parquet"
    }

    data_dir = BASE_DIR / "r" / "RQ12" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

def _prepare_rq13_data() -> None:
    '''
    Pull the needed information and save them into r/RQ13/data/
    '''
    filter_string = (
        "tags.research_question = 'RQ13' and tags.run_type = 'simulation' "
        "and tags.status = 'active' and params.config_name = 'production'"
    )
    experiment_names = ["Thesis"]
    params_to_attach = ["seed", "warm_up", "stimulus_tau", "memory_level"]

    # Artifact indexed by episode: only the last training episode of each
    # run is needed, so drop the rest before concatenating across runs to
    # keep the merge from blowing up memory.
    artifacts_last_episode_only = {
        "bm_results": "agent_state/BM_results.parquet",
    }
    # Artifacts that are already per-run (no episode dimension)
    artifacts_full = {
        "agents_od": "environment/agents_od.parquet",
        "od_routes": "environment/od_routes.parquet",
        "demand_odt": "DUE/generic/demand_odt.parquet",
        "flow_paths": "DUE/BM/flows_paths_odtp_k.parquet",
        "bm_rgap": "DUE/BM/R-gap/rgap.parquet",
        "actions": "agent_state/actions.parquet",
        "rewards": "agent_state/rewards.parquet",
        # "bm_results": "agent_state/BM_results.parquet",
    }

    data_dir = BASE_DIR / "r" / "RQ13" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, artifact_path in artifacts_last_episode_only.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
            last_episode_only=True,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

    for name, artifact_path in artifacts_full.items():
        df = load_artifact_across_runs(
            artifact_path=artifact_path,
            filter_string=filter_string,
            experiment_names=experiment_names,
            params_to_attach=params_to_attach,
        )
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

if __name__ == "__main__":
    run_analysis_rq()
