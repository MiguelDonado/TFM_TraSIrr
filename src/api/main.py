"""
API + endpoints.

  GET  /runs            list all jobs → [JobInfo, ...] (API key)
  POST /runs            launch a run (body: RunRequest) → 202 JobInfo (API key)
  GET  /runs/{job_id}   check a run → JobInfo, 404 if unknown
  DELETE /runs/{job_id} cancel a queued/running job → JobInfo (status
                        "cancelled"), 409 if already over, 404 if unknown (API key)
  GET  /                redirects to /docs

  JobInfo = {job_id, status, mlflow_run_id, final_rgap_pct,
  episodes_to_converge}; mlflow_run_id is set once the job starts running,
  the results once it is finished (null until then).

  (API key) = requires the X-API-Key header, see security.py. GET /runs is
  protected because it exposes every job_id; GET /runs/{job_id} stays open
  since a random job_id can't be guessed.

How to execute (from the repo root, with the thesis_master venv active):

  python3 -m uvicorn api.main:app --app-dir src --env-file .env

  - python3, not python: `python` resolves to SUMO's own Python, which has
    no uvicorn/fastapi.
  - api.main:app → the `app` variable in src/api/main.py (NOT main:app,
    that would be src/main.py, the simulation).
  - --app-dir src → puts src/ on the import path (api.*, config.paths).
  - --reload (optional, development) → restarts on every file save. Jobs
    survive (they are in api_db/jobs.db), but a job running at that moment
    is marked failed and its simulation killed on restart (see jobs.py).
  - Never add --workers (see the jobs.py docstring).
  - --env-file .env → Loads the environment variables into the uvicorn process.
    .env must define both (the API refuses to start otherwise):
      THESIS_API_KEY=<key>              (see security.py)
      MLFLOW_EXPERIMENT_NAME=api-runs   (MLflow experiment for API runs)

Then open http://127.0.0.1:8000/docs to try the endpoints from the browser
(Try it out → Execute). Simulation output appears in the uvicorn terminal;
runs land in the MLflow experiment named by MLFLOW_EXPERIMENT_NAME.
"""

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from api import jobs
from api.schemas import JobInfo, RunRequest
from api.security import require_api_key

app = FastAPI(title="Thesis runs API")

# Error responses shown in /docs. FastAPI adds the success code (response_model
# + status_code) and 422 by itself, but can't see `raise HTTPException` inside
# the functions, so those codes are declared with responses= on each endpoint
UNAUTHORIZED = {401: {"description": "Missing or invalid API key"}}
NOT_FOUND = {404: {"description": "Job not found"}}
CONFLICT = {409: {"description": "Job already over (finished, failed or cancelled)"}}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/runs", response_model=list[JobInfo], dependencies=[Depends(require_api_key)], responses={**UNAUTHORIZED})
def list_runs() -> list[JobInfo]:
    """List every job known to the API, oldest first.

    Requires the API key, since it exposes every job_id. Jobs are stored in
    SQLite, so the list survives a server restart.
    """
    return jobs.list_jobs()

# Depends(require_api_key) means before running this endpoint, run require_api_key first
@app.post("/runs", response_model=JobInfo, status_code=202, dependencies=[Depends(require_api_key)], responses={**UNAUTHORIZED})
def create_run(request: RunRequest, background_tasks: BackgroundTasks) -> JobInfo:
    """Launch a simulation run with the given parameters.

    Returns immediately (202) with a `queued` job; the simulation runs in the
    background, one at a time. Follow it with `GET /runs/{job_id}`.
    """
    job = jobs.create_job()
    # After sending the response, call jobs.run_job(job_id, request)
    background_tasks.add_task(jobs.run_job, job.job_id, request)
    return job

@app.get("/runs/{job_id}", response_model=JobInfo, responses={**NOT_FOUND})
def read_run(job_id: str) -> JobInfo:
    """Check the status of a job.

    `mlflow_run_id` is set once the job starts running; `final_rgap_pct` and
    `episodes_to_converge` once it is `finished` (null until then).
    """
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.delete("/runs/{job_id}", response_model=JobInfo, dependencies=[Depends(require_api_key)], responses={**UNAUTHORIZED, **NOT_FOUND, **CONFLICT})
def cancel_run(job_id: str) -> JobInfo:
    """Cancel a queued or running job.

    A queued job never starts; a running one is stopped (simulation and SUMO
    killed, MLflow run marked KILLED). The job stays listed with status
    `cancelled`. Jobs already finished, failed or cancelled return 409.
    """
    try:
        job = jobs.cancel_job(job_id)
    except jobs.JobNotCancellable as e:
        raise HTTPException(status_code=409, detail=str(e))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job