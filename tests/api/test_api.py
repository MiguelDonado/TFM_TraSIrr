"""
API tests: auth, validation, status codes. No real simulation is run.

Each test uses the API through TestClient and checks one behaviour, named
after it (a failing test's name says what broke). Setup and fixtures
(client, fake_run_job, clean_jobs) live in conftest.py.

  POST   /runs            401 without/wrong key, 422 out-of-range value or
                          unknown field, 202 + queued job handed to run_job
  GET    /runs/{job_id}   200 existing job (incl. results once finished), 404 unknown
  GET    /runs            401 without key, lists every job
  DELETE /runs/{job_id}   cancels a queued job, 409 if already over,
                          404 unknown, 401 without key
  _write_config           request values land in the right YAML sections

"Finished" jobs are simulated by editing jobs.JOBS directly, so results
and 409 can be tested without running anything.

Usage (from the repo root): python3 -m pytest -v

How pytest finds these tests (no list of tests exists anywhere):

  1. Reads pytest.ini at the repo root:
       testpaths = tests   → search tests/ (and every subfolder)
       pythonpath = src    → add src/ to the import path, so
                             `from api import jobs` works (like --app-dir src)
  2. Walks tests/ and keeps files named test_*.py:
       tests/golden/bm_golden.py   ✘ ignored (name)
       tests/api/test_api.py       ✔ collected
     (Files outside tests/, e.g. in src/api/, are never looked at.)
  3. Loads conftest.py automatically (never imported by hand): its fixtures
     are available to every test in its folder and subfolders.
  4. Inside test_api.py, runs every function named test_*; anything else
     (AUTH, VALID_BODY, helpers) is ignored.
"""

import os

import yaml

from api import jobs
from api.schemas import RunRequest

AUTH = {"X-API-Key": "test-key"}
VALID_BODY = {"seed": 42, "learning_rate": 0.3, "memory_level": 1.0}


# ---------- POST /runs ----------

def test_post_without_key_is_rejected(client, fake_run_job):
    response = client.post("/runs", json=VALID_BODY)
    assert response.status_code == 401

def test_post_with_wrong_key_is_rejected(client, fake_run_job):
    response = client.post("/runs", json=VALID_BODY, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401

def test_post_out_of_range_value_is_rejected(client, fake_run_job):
    response = client.post("/runs", json={**VALID_BODY, "learning_rate": 5}, headers=AUTH)
    assert response.status_code == 422

def test_post_unknown_field_is_rejected(client, fake_run_job):
    # typo
    response = client.post("/runs", json={**VALID_BODY, "reliabilty_sensitivity": 10}, headers=AUTH)
    assert response.status_code == 422

def test_post_valid_creates_queued_job(client, fake_run_job):
    response = client.post("/runs", json=VALID_BODY, headers=AUTH)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"

    # run_job was handed exactly this job and request
    job_id, request = fake_run_job[0]
    assert job_id == body["job_id"]
    assert request.reliability_sensitivity == 0.0

# ---------- GET /runs/{job_id} ----------

def test_get_existing_job(client, fake_run_job):
    job_id = client.post("/runs", json=VALID_BODY, headers=AUTH).json()["job_id"]
    response = client.get(f"/runs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

def test_get_unknown_job_returns_404(client):
    assert client.get("/runs/doesnotexist").status_code == 404

def test_get_finished_job_shows_results(client):
    # Simulate what run_job does on success
    job = jobs.JOBS[jobs.create_job().job_id]
    job.status = "finished"
    job.final_rgap_pct = 0.84
    job.episodes_to_converge = 63

    body = client.get(f"/runs/{job.job_id}").json()
    assert body["final_rgap_pct"] == 0.84
    assert body["episodes_to_converge"] == 63


# ---------- GET /runs ----------

def test_list_requires_key(client):
    assert client.get("/runs").status_code == 401

def test_list_returns_all_jobs(client):
    ids = {jobs.create_job().job_id, jobs.create_job().job_id}
    response = client.get("/runs", headers=AUTH)
    assert response.status_code == 200
    assert {job["job_id"] for job in response.json()} == ids

# ---------- DELETE /runs/{job_id} ----------

def test_cancel_queued_job(client, fake_run_job):
    job_id = client.post("/runs", json=VALID_BODY, headers=AUTH).json()["job_id"]
    response = client.delete(f"/runs/{job_id}", headers=AUTH)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

def test_cancel_twice_conflicts(client, fake_run_job):
    job_id = client.post("/runs", json=VALID_BODY, headers=AUTH).json()["job_id"]
    client.delete(f"/runs/{job_id}", headers=AUTH)
    assert client.delete(f"/runs/{job_id}", headers=AUTH).status_code == 409

def test_cancel_finished_job_conflicts(client):
    job = jobs.JOBS[jobs.create_job().job_id]
    job.status = "finished"
    assert client.delete(f"/runs/{job.job_id}", headers=AUTH).status_code == 409

def test_cancel_unknown_job_returns_404(client):
    assert client.delete("/runs/doesnotexist", headers=AUTH).status_code == 404

def test_cancel_requires_key(client, fake_run_job):
    job_id = client.post("/runs", json=VALID_BODY, headers=AUTH).json()["job_id"]
    assert client.delete(f"/runs/{job_id}").status_code == 401

# ---------- _write_config ----------

def test_write_config_places_values_in_their_sections():
    path = jobs._write_config(
        RunRequest(seed=7, learning_rate=0.5, memory_level=0.9,reliability_sensitivity=10)
    )
    try:
        with open(path) as f:
            config = yaml.safe_load(f)
        assert config["randomness"]["seed"] == 7
        assert config["learning"]["learning_rate"] == 0.5
        assert config["learning"]["reliability_sensitivity"] == 10
        assert config["learning"]["waiting_time_sensitivity"] == 0.0
    finally:
        os.remove(path)