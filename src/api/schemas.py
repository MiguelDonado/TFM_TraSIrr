"""
Pydantic models: the shape of the data going in and out of the API.

Job vs run — two different things, each with its own ID:

  Job   — the API's ticket for a request. Created by the API the moment
          POST /runs arrives, identified by job_id. It exists before any
          simulation starts (status "queued" while waiting its turn), can
          fail without a simulation ever starting (e.g. src/main.py crashes
          on import), and lives only in the API's memory (lost on restart).

  Run   — the actual simulation, identified by MLflow's run_id. Created by
          the API when the job starts running (see jobs.py) and filled by
          src/main.py. Stored permanently in the backend DB together with
          its params, metrics and artifacts.

          POST /runs ──► job (queued) ──► job (running) ──► job (finished/failed/cancelled)
                                               │                  │
                                               │                  └─ results read from the run
                                               └─ MLflow run (created here, persists)

The URL says /runs because that is what the client wants (a run); job_id
is the ticket to follow it. JobInfo carries both IDs (job_id and
mlflow_run_id), so keeping two names avoids ambiguity.

A DELETE /runs/{job_id} can cancel a job while queued or running; the job
stays listed with status "cancelled" (and its MLflow run, if any, is KILLED).
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

JobStatus = Literal["queued", "running", "finished", "failed", "cancelled"]


class RunRequest(BaseModel):
    """Parameters of a single run (body of POST /runs)."""

    # Unknown keys (e.g. typos) raise 422 instead of being silently ignored
    model_config = ConfigDict(extra="forbid")

    seed: Annotated[
        int,
        Field(ge=0, description="Random seed, for reproducibility", examples=[42]),
    ]
    learning_rate: Annotated[
        float,
        Field(gt=0, lt=1, description="β: how fast agents learn (Bush-Mosteller)", examples=[0.3]),
    ]
    memory_level: Annotated[
        float,
        Field(ge=0, le=1, description="γ: how much agents weight past experiences (Bush-Mosteller)", examples=[1.0]),
    ]
    reliability_sensitivity: Annotated[
        float,
        Field(ge=0, description="θ: extra perceived seconds per second of travel-time variability (0 = risk-neutral)", examples=[5.0]),
    ] = 0.0
    waiting_time_sensitivity: Annotated[
        float,
        Field(ge=0, description="φ: extra perceived seconds per second spent stopped (0 = neutral)", examples=[5.0]),
    ] = 0.0


class JobInfo(BaseModel):
    """State of a job (returned by POST /runs, GET /runs and GET /runs/{job_id})."""

    job_id: Annotated[str, Field(description="Id of the job")]
    status: Annotated[JobStatus, Field(description="Current state of the job")]
    mlflow_run_id: Annotated[str | None, Field(description="Id of the MLflow run (set once the job starts running)"),] = None
    final_rgap_pct: Annotated[float | None, Field(description="R-gap (%) of the last episode (set once finished)"),] = None
    episodes_to_converge: Annotated[int | None, Field(description="Last episode run: when MARL algorithm converged or max_episodes"),] = None