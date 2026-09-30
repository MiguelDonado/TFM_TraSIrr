"""
Shared setup for the API tests (pytest loads this file automatically,
before test_api.py, so its fixtures are available to every test there).

The API can't be imported as-is in a test: at import time it needs env vars
(security.py, jobs.py) and connects to the real MLflow DB (jobs.py calls
set_up_mlflow()). So this file, IN THIS ORDER:

  1. sets fake env vars (THESIS_API_KEY=test-key, never the real key)
  2. points MLflow at a throwaway DB in a temp folder
  3. only then imports the API

Fixtures (a test gets one by naming it as a parameter):

  client        TestClient(app): sends requests straight into the app,
                no uvicorn/server needed
  clean_jobs    autouse: empties JOBS before and after every test, so
                tests never see each other's jobs
  fake_run_job  replaces jobs.run_job with a recorder, so a POST never
                launches a real simulation (TestClient runs background
                tasks before client.post returns); returns the list of
                recorded calls for the test to check

Not covered here (needs a real run, checked by hand): the simulation itself,
killing SUMO on cancel, results written to MLflow.
"""
import os
import tempfile
from pathlib import Path

import pytest

# 1. Env vars the API needs at import time (fake-values)
os.environ["THESIS_API_KEY"] = "test-key"
os.environ["MLFLOW_EXPERIMENT_NAME"] = "api-tests"

# 2. Point MLflow at a throwaway DB before importing the API
# (jobs.py calls set_up_mlflow() on import)
'''
Rule 1: a module's code runs only once

The first time anything imports mlflow_tracking.utils, Python runs its top-level code, including from config.paths import BACKEND_DB. It then stores the module (in sys.modules). Every later import reuses that stored module without running it again.

conftest:  import mlflow_tracking.utils      → runs utils.py: BACKEND_DB = real path
conftest:  mlflow_utils.BACKEND_DB = temp    → replaces the name inside that module
conftest:  from api.main import app
             └─ jobs.py: from mlflow_tracking.utils import set_up_mlflow
                          → utils already loaded → NOT run again → temp path survives ✔
'''
import mlflow_tracking.utils as mlflow_utils

mlflow_utils.BACKEND_DB = Path(tempfile.mkdtemp()) / "mlflow.db"

# 3. Import the API
from fastapi.testclient import TestClient

from api import jobs
from api.main import app


# Fixture called "client"
# Fixture: Preparation code that pytest runs for you before a test. 
# You write it once, and any test can use it
# The connection happens through the parameter name
# Example: def test_unknown_job_returns_404(client):
# When pytest runs this test, it sees the parameter client, looks for a 
# fixture with that same name, calls it, and passes what it returned
@pytest.fixture
def client():
    return TestClient(app)

'''
The problem it solves: JOBS is a module-level dict, 
so it survives from one test to the next. If test_A 
creates 2 jobs, test_B would start with those 2 still there. 
Then test_list_returns_all_jobs would find 4 jobs instead 
of 2 and fail, depending on which tests happened to run first. 
Tests must not affect each other.

autouse=True means "run this fixture for every test, even those 
that doesn't name it
'''
@pytest.fixture(autouse=True)
def clean_jobs():
    jobs.JOBS.clear()   # Before the test
    yield               # the test runs here
    jobs.JOBS.clear()   # After the test


'''
The problem it solves: TestClient runs background tasks 
before client.post(...) returns. A POST in a test would 
run the real run_job, which means a real simulation 
lasting many minutes.

monkeypatch is a fixture that pytest provides itself

monkeypatch.setattr(jobs, "run_job", <fake>)
                    ↑ in this module, ↑ replace this name, ↑ with this
'''

@pytest.fixture
def fake_run_job(monkeypatch):
    calls = []
    monkeypatch.setattr(
        jobs, 
        "run_job", 
        # job_id and request are the parameters used when calling run_job
        lambda job_id, request: calls.append((job_id, request)))
    return calls