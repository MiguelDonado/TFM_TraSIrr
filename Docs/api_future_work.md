# API — Future Work

The API (`src/api/`) is complete for local use: launch a run, follow it, list
jobs, cancel them and get the results back, protected by an API key and
covered by tests (`tests/api/`). Everything below only matters to run it
somewhere other than your own machine.

Suggested order: **1 → 2 → 3 → 4**.

---

## 1. API in Docker

**Why:** today the API only runs in a local Python environment with SUMO
installed. The rest of the project already runs in Docker, and the README
setup for the API was left out on purpose until this is done. It is also the
first step towards deployment (4).

**What it involves:**

- Add an `api` service to `docker-compose.yml`, like the `mlflow` one
  (same image, repo bind-mounted, same `user`).
- Expose the port: `ports: - "8000:8000"`.
- Start uvicorn with `--host 0.0.0.0`, for the same reason as in the `mlflow`
  service (by default uvicorn only listens on the container's own loopback,
  so the host couldn't reach it).
- Load `.env` (`env_file: .env` or `--env-file .env`): the API refuses to
  start without `THESIS_API_KEY` and `MLFLOW_EXPERIMENT_NAME`.
- Single worker, never `--workers` (see the `src/api/jobs.py` docstring).
- Rebuild and push the image to Docker Hub: `requirements.txt` changed
  (FastAPI, pytest, httpx).
- Fix step 9 of the Docker setup in the README: it creates `.env` with `>`,
  which would wipe the API variables if run after them (use `>>`).
- Then write the README launch instructions (the "Setup and launch" and
  "Example" subsections removed from "Getting Started (API)").

---

## 2. Logs per job

**Why:** when a job ends as `failed`, the only way to know why is the
terminal where uvicorn runs. On a server (4) that terminal isn't visible.

**What it involves:**

- In `run_job`, send the output of `src/main.py` to a file per job
  (e.g. `experiments/logs/api/<job_id>.log`) instead of the terminal.
- New endpoint `GET /runs/{job_id}/logs` returning that file (or its last N
  lines), protected with the API key.

---

## 3. Persistent jobs

**Why:** `JOBS` lives in memory, so every restart (deploy, crash, reboot)
forgets all jobs; `GET /runs/{job_id}` then returns 404 for jobs whose runs
are still in MLflow. A job running during a restart is lost.

**What it involves:**

- Store jobs in a small SQLite table instead of the `JOBS` dict. Only the
  inside of `jobs.py` changes; `main.py` and `schemas.py` stay the same.
- On startup, mark jobs left as `queued`/`running` by a previous server as
  `failed` (their thread no longer exists).

---

## 4. Deployment + HTTPS

**Why:** to use the API from outside your laptop (remotely, or to show it to
the thesis jury / recruiters).

**What it involves:**

- Choose where to host it (a VPS or a cloud provider; runs take minutes of
  CPU, so the machine size matters).
- HTTPS is required: without it the API key travels in plain text. Usually
  done with a reverse proxy (e.g. Caddy or Nginx) in front of uvicorn.
- Decide whether to expose the MLflow UI too (read-only, behind
  authentication).
