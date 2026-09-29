"""
Launching and tracking runs (no FastAPI, only Python).

Processes, threads and why the API must run with ONE worker:

  uvicorn
   └── worker = a PROCESS        (1 by default; more with --workers N)
        ├── its own memory: JOBS, RUN_LOCK
        ├── main thread: receives HTTP requests and hands them out
        └── thread pool (up to 40 threads)
             ├── thread 1: run_job(A)
             ├── thread 2: run_job(B)   (sleeping on RUN_LOCK)
             └── ...

  - Worker (process): a separate program. Processes do NOT share memory.
  - Thread: a line of work inside a process. Threads of the same process
    DO share memory, so they all see the same JOBS and RUN_LOCK.
  - Each POST's background task (run_job) gets its own thread from the pool.

  One worker, many threads (this design): all threads share JOBS and
  RUN_LOCK, so they coordinate — only one simulation runs at a time and a
  GET always finds the job.

  Several workers: each has its own JOBS and RUN_LOCK. Uvicorn sends each
  request to any worker, so two simulations can run at once (each worker's
  lock is free) and a GET can land on a worker that never saw the job (404).

  Multiple workers are for APIs whose requests are independent (state in a
  shared database). Here state is in memory and simulations share files, so
  NEVER start uvicorn with --workers.

How RUN_LOCK works:

  `with RUN_LOCK:` = acquire() ... finally release().
  acquire(): free → take it and continue; taken → the thread sleeps there.
  release(): always runs (even after a crash) and wakes one sleeping thread.
  A job is "queued" exactly while its thread sleeps on the lock, because
  "running" is set inside the with block. Order among waiting jobs is not
  guaranteed (the OS picks which thread wakes up).

Linking a job to its MLflow run (and reading its results):

  1. run_job creates the MLflow run itself (CLIENT.create_run, tagged with
     job_id), so the job knows its mlflow_run_id from the start.
  2. It launches src/main.py with MLFLOW_RUN_ID=<that id> in the env.
     mlflow.start_run() in src/main.py reads it and CONTINUES that run
     instead of creating a new one (built-in MLflow behaviour, so the
     simulation code does not change; without the var it creates a new run).
  3. On success, _read_results reads the run's last logged metrics
     (alg_rgap_pct, ep_to_conv) into the job, THEN sets "finished".
  4. On failure the run is marked FAILED, so it never stays RUNNING.

  The experiment comes from MLFLOW_EXPERIMENT_NAME (.env): set_up_mlflow()
  reads it here, and src/main.py inherits it through {**os.environ}.

  Getters (get_job, list_jobs, create_job) return copies (model_copy), never
  the live JobInfo objects that run_job keeps modifying in another thread:
  a response is always a consistent snapshot of one moment.
"""

import os
import subprocess
import sys
import tempfile
import threading
import uuid

import mlflow
import yaml

from api.schemas import JobInfo, RunRequest
from config.paths import BASE_DIR, EXPERIMENTS_TMP, ensure_dirs
from mlflow_tracking.utils import set_up_mlflow

BASE_CONFIG = BASE_DIR / "experiments" / "base_dev.yaml"   # base.yaml once it works
# Experiment name comes from .env (single source, also read by set_up_mlflow()
# and inherited by src/main.py). Fail at startup if missing: otherwise API runs
# would silently fall back to the "Thesis" experiment
MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT_NAME")
if not MLFLOW_EXPERIMENT:
    raise RuntimeError("Set MLFLOW_EXPERIMENT_NAME before starting the API")

# In-memory job store
JOBS: dict[str, JobInfo] = {}
# To avoid executing in parallel POST requests (parallel simulations, because they reuse the same paths)
RUN_LOCK = threading.Lock()

ensure_dirs()
# Point at DB and create api-runs if needed
set_up_mlflow()
EXPERIMENT_ID = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT).experiment_id
CLIENT = mlflow.MlflowClient()

 
def create_job() -> JobInfo:
    job = JobInfo(job_id=uuid.uuid4().hex, status="queued")
    JOBS[job.job_id] = job
    return job.model_copy()

def list_jobs() -> list[JobInfo]:
    # list() - Creates a copy: Another thread may add a job (create_job) while we read
    # and raising an error
    return [job.model_copy() for job in list(JOBS.values())]

def get_job(job_id: str) -> JobInfo | None:
    # .get() Returns None if it doesn't exist
    job = JOBS.get(job_id)
    return job.model_copy() if job else None

def _write_config(request: RunRequest) -> str:
    # safe_load() and model_dump() both give a Python dict

    # 1. Load base config file
    with open(BASE_CONFIG) as f:
        config = yaml.safe_load(f)

    # 2. Place the request values in their sections. Field names in
    # RunRequest match the YAML keys exactly, so everything except seed 
    # can be merged into learning in one go
    params = request.model_dump()
    config["randomness"]["seed"] = params.pop("seed")
    config["learning"].update(params)

    # 3. Write to a temp YAML (delete=False: src/main.py still needs to read it)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", dir=EXPERIMENTS_TMP, delete=False
    ) as tmp:
        yaml.dump(config, tmp, default_flow_style=False)
        return tmp.name
    
def run_job(job_id: str, request: RunRequest) -> None:
    job = JOBS[job_id]
    with RUN_LOCK:          # Waits here while another run is going
        job.status = "running"
        path = None
        try:
            # Create the MLflow run here, so we know its id from the start
            run = CLIENT.create_run(EXPERIMENT_ID, tags={"job_id":job_id})
            job.mlflow_run_id = run.info.run_id
            path = _write_config(request)
            result = subprocess.run(
                [sys.executable, "src/main.py", path], 
                cwd=BASE_DIR,
                # Copy all the environment variables (incl. MLFLOW_EXPERIMENT_NAME)
                # and add MLFLOW_RUN_ID: src/main.py's start_run() continues this run
                env={**os.environ, "MLFLOW_RUN_ID": job.mlflow_run_id},
            )
            if result.returncode == 0:
                _read_results(job)
                # After the results: a GET never sees "finished" with empty results
                job.status = "finished"
            else:
                # Close the MLflow run in case src/main.py crashed before start_run()
                # (otherwise it stays RUNNING forever; harmless if already FAILED)
                CLIENT.set_terminated(job.mlflow_run_id, "FAILED")
                job.status = "failed"
        except Exception:
            job.status = "failed"
        finally:
            if path:
                os.remove(path)

def _read_results(job: JobInfo) -> None:
    run = CLIENT.get_run(job.mlflow_run_id)
    # run.data.metrics: Returns the last value of each metric
    metrics = run.data.metrics
    job.final_rgap_pct = metrics["alg_rgap_pct"]
    job.episodes_to_converge = int(metrics["ep_to_conv"])

