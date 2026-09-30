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
  4. On failure the run is marked FAILED (on cancel, KILLED), so it never
     stays RUNNING.

  The experiment comes from MLFLOW_EXPERIMENT_NAME (.env): set_up_mlflow()
  reads it here, and src/main.py inherits it through {**os.environ}.

  Getters (get_job, list_jobs, create_job) return copies (model_copy), never
  the live JobInfo objects that run_job keeps modifying in another thread:
  a response is always a consistent snapshot of one moment.

Cancelling a job (DELETE /runs/{job_id} → cancel_job):

  cancel_job runs in the DELETE request's thread; run_job in its own. The
  only signal between them is job.status = "cancelled", which run_job checks
  ("was I cancelled meanwhile?") at each point a cancel can land:

    queued ──► gets lock ──► "running" ──► Popen ──► wait() ──► done
      ▲           │                ▲                    ▲
      cancel      check 1:         cancel here: no      cancel here:
      here        return, never    process to kill yet  cancel_job kills it
                  run anything     → check 2 kills it   → check 3: KILLED,
                                   right after Popen    not "failed"

  - subprocess.Popen (not run): starts the simulation and returns at once,
    handing back the process object; it is stored in PROCESSES so
    cancel_job can kill it, then process.wait() waits as run() did.
  - Process group: src/main.py launches SUMO, duarouter... as its own
    children. start_new_session=True makes src/main.py lead a new process
    group, and _kill sends SIGTERM to the WHOLE group (os.killpg): killing
    only src/main.py would leave SUMO running, writing to the shared files
    while the next job starts.
  - A killed process has a non-zero return code, like a crash; check 3 goes
    before the returncode check so a cancel is never reported as "failed".
  - Finished/failed/cancelled jobs can't be cancelled: JobNotCancellable
    (main.py turns it into 409).
"""

import os
import signal
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

BASE_CONFIG = BASE_DIR / "experiments" / "base.yaml"   # base.yaml once it works
# Experiment name comes from .env (single source, also read by set_up_mlflow()
# and inherited by src/main.py). Fail at startup if missing: otherwise API runs
# would silently fall back to the "Thesis" experiment
MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT_NAME")
if not MLFLOW_EXPERIMENT:
    raise RuntimeError("Set MLFLOW_EXPERIMENT_NAME before starting the API")

# In-memory job store
JOBS: dict[str, JobInfo] = {}
# Running simulations: {job_id: process}, so cancel_job can kill them
# subprocess.Popen: start a subprocess and gives you control over it
PROCESSES: dict[str, subprocess.Popen] = {}

# To avoid executing in parallel POST requests (parallel simulations, because they reuse the same paths)
RUN_LOCK = threading.Lock()

ensure_dirs()
# Point at DB and create api-runs if needed
set_up_mlflow()
EXPERIMENT_ID = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT).experiment_id
CLIENT = mlflow.MlflowClient()

class JobNotCancellable(Exception):
    """Raised when cancelling a job that is already over"""
 
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

def cancel_job(job_id: str) -> JobInfo | None:
    job = JOBS.get(job_id)
    if job is None:
        return None
    if job.status not in ("queued", "running"):
        raise JobNotCancellable(f"Job already {job.status}, nothing to cancel")

    job.status = "cancelled"
    # Running → kill it now. Queued → run_job sees "cancelled" when it gets the lock
    process = PROCESSES.get(job_id)
    if process:
        _kill(process)
    return job.model_copy()


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
        if job.status == "cancelled":
            return
        job.status = "running"
        path = None
        try:
            # Create the MLflow run here, so we know its id from the start
            run = CLIENT.create_run(EXPERIMENT_ID, tags={"job_id":job_id})
            job.mlflow_run_id = run.info.run_id
            path = _write_config(request)

            # subprocess.Popen instead of subprocess.run to have more control
            # than with subprocess.run
            # Main difference:
            # > subprocess.run: Starts and wait, it does not move to the next line of code until execution finished
            # > subprocess.Popen: Starts but does not wait automatically, it moves to the next line
            # start_new_session=True: src/main.py leads its own process group
            process = subprocess.Popen(
                [sys.executable, "src/main.py", path], 
                cwd=BASE_DIR,
                # Copy all the environment variables (incl. MLFLOW_EXPERIMENT_NAME)
                # and add MLFLOW_RUN_ID: src/main.py's start_run() continues this run
                env={**os.environ, "MLFLOW_RUN_ID": job.mlflow_run_id},
                start_new_session=True
            )
            PROCESSES[job_id] = process

            # Cancelled before Popen
            if job.status == "cancelled":
                _kill(process)
            # Wait until processes finishes, crashes or is killed
            returncode = process.wait()

            # mark status of the run as killed (mlflow)
            if job.status == "cancelled":
                CLIENT.set_terminated(job.mlflow_run_id, "KILLED")
            # mark status of the run as finished (mlflow)
            elif returncode == 0:
                _read_results(job)
                job.status = "finished"
            # mark status of the run as failed (mlflow)
            else:
                CLIENT.set_terminated(job.mlflow_run_id, "FAILED")
                job.status = "failed"
        # Dont hide a cancel behind a failed
        except Exception:
            if job.status != "cancelled":
                job.status = "failed"
        finally:
            # No longer running 
            PROCESSES.pop(job_id, None) 
            if path:
                os.remove(path)

def _read_results(job: JobInfo) -> None:
    run = CLIENT.get_run(job.mlflow_run_id)
    # run.data.metrics: Returns the last value of each metric
    metrics = run.data.metrics
    job.final_rgap_pct = metrics["alg_rgap_pct"]
    job.episodes_to_converge = int(metrics["ep_to_conv"])

def _kill(process: subprocess.Popen) -> None:
    # Kill src/main.py AND its children (SUMO, duarouter...):
    # they share its process group
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass    # already dead


