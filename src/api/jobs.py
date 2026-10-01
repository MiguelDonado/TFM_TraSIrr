"""
Launching and tracking runs (no FastAPI, only Python).

Processes, threads and why the API must run with ONE worker:

  uvicorn
   └── worker = a PROCESS        (1 by default; more with --workers N)
        ├── its own memory: PROCESSES, RUN_LOCK
        ├── main thread: receives HTTP requests and hands them out
        └── thread pool (up to 40 threads)
             ├── thread 1: run_job(A)
             ├── thread 2: run_job(B)   (sleeping on RUN_LOCK)
             └── ...
   (jobs themselves are in api_db/jobs.db, a file: see "Where jobs live")

  - Worker (process): a separate program. Processes do NOT share memory.
  - Thread: a line of work inside a process. Threads of the same process
    DO share memory, so they all see the same PROCESSES and RUN_LOCK.
  - Each POST's background task (run_job) gets its own thread from the pool.

  One worker, many threads (this design): all threads share PROCESSES and
  RUN_LOCK, so they coordinate — only one simulation runs at a time and a
  DELETE always finds the process to kill.

  Several workers: each has its own PROCESSES and RUN_LOCK. Uvicorn sends
  each request to any worker, so two simulations can run at once (each
  worker's lock is free) and a DELETE can land on a worker that never
  started the simulation (nothing to kill). The jobs DB would be shared,
  but that does not fix the lock or the process handles.

  Multiple workers are for APIs whose requests are independent (all state
  in a shared database). Here the lock and processes are in memory and
  simulations share files, so NEVER start uvicorn with --workers.

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
     (alg_rgap_pct, ep_to_conv) and saves them in the job's row, THEN sets
     "finished" (a client that sees "finished" always finds the results).
  4. On failure the run is marked FAILED (on cancel, KILLED), so it never
     stays RUNNING.

  The experiment comes from MLFLOW_EXPERIMENT_NAME (.env): set_up_mlflow()
  reads it here, and src/main.py inherits it through {**os.environ}.

Where jobs live (SQLite, api_db/jobs.db):

  One row per job, so jobs survive a server restart. Columns = the JobInfo
  fields + pid (src/main.py's process id, internal: never returned by the
  API) + created_at (for "oldest first" in GET /runs).

  - Every function opens its own connection (_connect) and closes it: a
    connection can't be shared between threads, and each run_job and each
    request runs in its own thread.
  - Status changes are conditional (_set_status): "UPDATE ... SET status = X
    WHERE status IN (...)" checks and changes in ONE step, so run_job and
    cancel_job (different threads) can't overwrite each other. rowcount
    says whether it happened (1) or the condition failed (0).
  - Other columns (mlflow_run_id, pid, results) are written with _update_job.
  - Every read builds a new JobInfo from the row: a response is always a
    consistent snapshot of one moment.

Restart recovery (_recover_jobs, once at startup):

  A job left queued/running by a previous server can never finish: its
  thread died with the server. Worse, its simulation does NOT: because of
  start_new_session=True (see below) it is outside the server's process
  group, so neither Ctrl+C nor a crash reaches it, and it would keep
  writing to the shared files. On a clean stop uvicorn also waits for the
  running job before shutting down, so cleaning up "on the way down" is not
  reliable either. So the NEXT startup cleans up:

    1. leftover queued/running jobs → "failed"
    2. those with a pid → kill their process group (_kill)
    3. those whose MLflow run is still RUNNING → FAILED (a run that already
       FINISHED, e.g. server died just before writing "finished", is kept)

  Between the server going down and the next start, an orphaned simulation
  keeps running; it is killed before any new job can start.

Cancelling a job (DELETE /runs/{job_id} → cancel_job):

  cancel_job runs in the DELETE request's thread; run_job in its own. The
  only signal between them is the job's status in the DB: cancel_job sets
  it to "cancelled" (only if queued/running), and run_job checks it ("was I
  cancelled meanwhile?") at each point a cancel can land:

    queued ──► gets lock ──► "running" ──► Popen ──► wait() ──► done
      ▲           │                ▲                    ▲
      cancel      check 1:         cancel here: no      cancel here:
      here        queued→running   process to kill yet  cancel_job kills it
                  fails → return,  → check 2 kills it   → check 3: KILLED,
                  never run        right after Popen    not "failed"
                  anything

  - subprocess.Popen (not run): starts the simulation and returns at once,
    handing back the process object; it is stored in PROCESSES so
    cancel_job can kill it (and its pid in the DB, for restart recovery),
    then process.wait() waits as run() did.
  - Process group: src/main.py launches SUMO, duarouter... as its own
    children. start_new_session=True makes src/main.py lead a new process
    group, and _kill sends SIGTERM to the WHOLE group (os.killpg): killing
    only src/main.py would leave SUMO running, writing to the shared files
    while the next job starts.
  - A killed process has a non-zero return code, like a crash; check 3 goes
    before the returncode check so a cancel is never reported as "failed"
    (and "finished"/"failed" are only set if the job is still "running").
  - Finished/failed/cancelled jobs can't be cancelled: JobNotCancellable
    (main.py turns it into 409).
"""

import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime, timezone

import mlflow
import yaml

from api.schemas import JobInfo, RunRequest
from config.paths import BASE_DIR, EXPERIMENTS_TMP, JOBS_DB, ensure_dirs
from mlflow_tracking.utils import set_up_mlflow

BASE_CONFIG = BASE_DIR / "experiments" / "base.yaml"   # base.yaml once it works
# Experiment name comes from .env (single source, also read by set_up_mlflow()
# and inherited by src/main.py). Fail at startup if missing: otherwise API runs
# would silently fall back to the "Thesis" experiment
MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT_NAME")
if not MLFLOW_EXPERIMENT:
    raise RuntimeError("Set MLFLOW_EXPERIMENT_NAME before starting the API")

# Running simulations: {job_id: process}, so cancel_job can kill them
# subprocess.Popen: start a subprocess and gives you control over it
PROCESSES: dict[str, subprocess.Popen] = {}

# To avoid executing in parallel POST requests (parallel simulations, because they reuse the same paths)
RUN_LOCK = threading.Lock()

def _connect() -> sqlite3.Connection:
    """Creates and return a connection to SQLite db"""
    # 1. Opens a connection to the db
    # timeout = 10 (SQLite will wait up to 10 seconds if db is locked)
    # SQLite is good for applications with lots of reads and few concurrent writing
    conn = sqlite3.connect(JOBS_DB, timeout = 10)
    # 2. Configure how query results behave. This way we can access columns by name
    # e.g. print(row["role"])
    conn.row_factory = sqlite3.Row
    return conn

def _init_db() -> None:
    """Create the jobs table if it doesn't exist; called once at startup"""
    conn = _connect()

    # Possible erros: SQL syntax error, database locked...
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                mlflow_run_id TEXT,
                pid INTEGER,
                final_rgap_pct REAL,
                episodes_to_converge INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        # Confirm/save db changes
        conn.commit()
    finally:
        conn.close()

def _kill(pid: int) -> None:
    # Kill src/main.py AND its children (SUMO, duarouter...):
    # they share its process group (its id = src/main.py's pid)
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass    # already dead


def _recover_jobs() -> None:
    """Mark jobs left queued/running by a previous server as failed and kill their simulations; called once at startup.
    1. Find the jobs that were left queued or running.
    2. Mark them failed.
    3. Kill their simulation, if it had started (a queued job has no pid, so it's skipped).
    4. Mark their MLflow run FAILED, if it was still RUNNING.
    """

    conn = _connect()
    try:
        # 1. Which jobs were left unfinished?
        rows = conn.execute(
            "SELECT pid, mlflow_run_id FROM jobs WHERE status IN ('queued','running')"
        ).fetchall()
        # 2. Mark them all as failed
        conn.execute(
            "UPDATE jobs SET status = 'failed' WHERE status IN ('queued', 'running')"
        )
        conn.commit()
    finally: 
        conn.close()
    for row in rows:
        # 3. If its simulation had started → kill it
        if row["pid"]:
            _kill(row["pid"])
        # 4. If its MLflow run still has status RUNNING → mark it as FAILED
        if row["mlflow_run_id"] and CLIENT.get_run(row["mlflow_run_id"]).info.status == "RUNNING":
            CLIENT.set_terminated(row["mlflow_run_id"], "FAILED")

ensure_dirs()
_init_db()

# Point at DB and create api-runs if needed
set_up_mlflow()
EXPERIMENT_ID = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT).experiment_id
CLIENT = mlflow.MlflowClient()
_recover_jobs()

class JobNotCancellable(Exception):
    """Raised when cancelling a job that is already over"""
 
def create_job() -> JobInfo:
    job = JobInfo(job_id=uuid.uuid4().hex, status="queued")
    conn = _connect()
    try:
        # ?: Parameterized query. Easier and it also prevents SQL injection
        conn.execute(
            "INSERT INTO jobs (job_id, status, created_at) VALUES (?, ?, ?)",
            (job.job_id, job.status, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return job

def list_jobs() -> list[JobInfo]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * from jobs ORDER BY created_at"
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_job(row) for row in rows]

def get_job(job_id: str) -> JobInfo | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,) # (job_id,): Comma is to make it a one element tuple
        ).fetchone()
    finally:
        conn.close()
    return _row_to_job(row) if row else None

def cancel_job(job_id: str) -> JobInfo | None:
    # Try to cancel: only succeeds if the job is queued or running
    if _set_status(job_id, "cancelled", only_if=("queued", "running")):
        # If it was running → kill it now.
        process = PROCESSES.get(job_id)
        if process:
            _kill(process.pid)
        return get_job(job_id)

    # Nothing changed: job doesnt exist (404) or is already over (409)
    job = get_job(job_id)
    if job is None:
        return None
    raise JobNotCancellable(f"Job already {job.status}, nothing to cancel")

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
        # Check 1: queued → running, only if still queued (else cancelled while waiting)
        if not _set_status(job_id, "running", only_if=("queued",)):
            return
        path = None
        try:
            # Create the MLflow run here, so we know its id from the start
            run = CLIENT.create_run(EXPERIMENT_ID, tags={"job_id":job_id})
            mlflow_run_id = run.info.run_id
            _update_job(job_id, mlflow_run_id=mlflow_run_id)
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
                env={**os.environ, "MLFLOW_RUN_ID": mlflow_run_id},
                start_new_session=True
            )
            PROCESSES[job_id] = process
            _update_job(job_id, pid=process.pid)

            # Check 2: cancelled between "running" and Popen
            if _get_status(job_id) == "cancelled":
                _kill(process.pid)
            # Wait until processes finishes, crashes or is killed
            returncode = process.wait()

            # Check 3: cancelled while running 
            if _get_status(job_id) == "cancelled":
                CLIENT.set_terminated(mlflow_run_id, "KILLED")
            # mark status of the run as finished (mlflow)
            elif returncode == 0:
                _update_job(job_id, **_read_results(mlflow_run_id))
                _set_status(job_id, "finished", only_if=("running",))
            # mark status of the run as failed (mlflow)
            else:
                CLIENT.set_terminated(mlflow_run_id, "FAILED")
                _set_status(job_id, "failed", only_if=("running",))
        # Dont hide a cancel behind a failed
        except Exception:
            _set_status(job_id, "failed", only_if=("running",))
        finally:
            # No longer running 
            PROCESSES.pop(job_id, None) 
            if path:
                os.remove(path)

def _read_results(mlflow_run_id: str) -> dict:
    """Read the run's final results from MLflow, as {column: value}"""
    run = CLIENT.get_run(mlflow_run_id)
    # run.data.metrics: Returns the last value of each metric
    metrics = run.data.metrics
    return {
        "final_rgap_pct": metrics["alg_rgap_pct"],
        "episodes_to_converge": int(metrics["ep_to_conv"])
    }


def _row_to_job(row: sqlite3.Row) -> JobInfo:
    """Converts a database row into a JobInfo object"""
    return JobInfo(**{field: row[field] for field in JobInfo.model_fields})

def _set_status(job_id: str, new_status: str, only_if: tuple[str, ...]) -> bool:
    """Change status only if the current one is in only_if; True if it changed"""
    # only_if: ("queued","running")
    placeholders = ", ".join("?" * len(only_if))  # ("queued","running") → "?, ?"
    conn = _connect()
    try:
        cursor = conn.execute(
            f"UPDATE jobs SET status = ? WHERE job_id = ? AND status IN ({placeholders})",
            (new_status, job_id, *only_if)
        )
        conn.commit()
        # Check how many rows were affected by the SQL operation
        changed = cursor.rowcount == 1
    finally:
        conn.close()
    return changed

def _update_job(job_id: str, **fields) -> None:
    """Writes any other column (mlflow_run_id, the results)"""
    # **fields: Accept any keyword arguments and put them under a dict called fields
    # for name in fields: Loop over the keys of the dictionary
    columns = ", ".join(f"{name} = ?" for name in fields)   # "mlflow_run_id = ?"
    conn = _connect()
    # f-string only builds column names, the values still go through ?
    # column names cant be passed as ?
    try:
        conn.execute(
            f"UPDATE jobs SET {columns} WHERE job_id = ?",
            (*fields.values(), job_id)
        )
        conn.commit()
    finally: 
        conn.close()

def _get_status(job_id: str) -> str | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT status FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
    finally:
        conn.close()
    return row["status"] if row else None


        