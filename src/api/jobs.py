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
"""

import os
import subprocess
import sys
import tempfile
import threading
import uuid

import yaml

from api.schemas import JobStatus, RunRequest
from config.paths import BASE_DIR, EXPERIMENTS_TMP, ensure_dirs

BASE_CONFIG = BASE_DIR / "experiments" / "base_dev.yaml"   # base.yaml once it works
MLFLOW_EXPERIMENT = "api-runs"

# In-memory job store
JOBS: dict[str, JobStatus] = {}
# To avoid executing in parallel POST requests (parallel simulations, because they reuse the same paths)
RUN_LOCK = threading.Lock()

ensure_dirs()


def create_job() -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = "queued"
    return job_id

def list_jobs() -> list[tuple[str, JobStatus]]:
    # list() - Creates a copy: Another thread may add a job (create_job) while we read
    # and raising an error
    return list(JOBS.items())

def get_job_status(job_id: str) -> JobStatus | None:
    # .get() Returns None if it doesn't exist
    return JOBS.get(job_id)

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
    with RUN_LOCK:          # Waits here while another run is going
        JOBS[job_id] = "running"
        path = None
        try:
            path = _write_config(request)
            result = subprocess.run(
                [sys.executable, "src/main.py", path], 
                cwd=BASE_DIR,
                # copy all the environment variables and add one more
                env={**os.environ, "MLFLOW_EXPERIMENT_NAME": MLFLOW_EXPERIMENT},
            )
            JOBS[job_id] = "finished" if result.returncode == 0 else "failed"
        except Exception:
            JOBS[job_id] = "failed"
        finally:
            if path:
                os.remove(path)