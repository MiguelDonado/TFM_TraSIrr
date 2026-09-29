"""
API + endpoints.

  POST /runs            launch a run (body: RunRequest) → 202 {job_id, status}
  GET  /runs/{job_id}   check a run → {job_id, status}, 404 if unknown
  GET  /                redirects to /docs

How to execute (from the repo root, with the thesis_master venv active):

  python3 -m uvicorn api.main:app --app-dir src --env-file .env

  - python3, not python: `python` resolves to SUMO's own Python, which has
    no uvicorn/fastapi.
  - api.main:app → the `app` variable in src/api/main.py (NOT main:app,
    that would be src/main.py, the simulation).
  - --app-dir src → puts src/ on the import path (api.*, config.paths).
  - --reload (optional, development) → restarts on every file save, which
    wipes the in-memory JOBS and may cut off a running simulation.
  - Never add --workers (see the jobs.py docstring).
  - --env-file .env → Loads the environment variables into the uvicorn process

Then open http://127.0.0.1:8000/docs to try the endpoints from the browser
(Try it out → Execute). Simulation output appears in the uvicorn terminal;
results land in the MLflow experiment "api-runs".
"""

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from api import jobs
from api.schemas import RunRequest, RunStatus
from api.security import require_api_key

app = FastAPI(title="Thesis runs API")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Depends(require_api_key) means before running this endpoint, run require_api_key first
@app.post("/runs", response_model=RunStatus, status_code=202, dependencies=[Depends(require_api_key)])
def create_run(request: RunRequest, background_tasks: BackgroundTasks) -> RunStatus:
    job_id = jobs.create_job()
    # After sending the response, call jobs.run_job(job_id, request)
    background_tasks.add_task(jobs.run_job, job_id, request)
    return RunStatus(job_id=job_id, status="queued")

@app.get("/runs/{job_id}", response_model=RunStatus)
def read_run(job_id: str) -> RunStatus:
    status = jobs.get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return RunStatus(job_id=job_id, status=status)