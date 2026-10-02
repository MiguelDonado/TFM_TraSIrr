"""
API key check for protected endpoints.

An API key is a password for programs: the server knows a secret string and
every protected request must carry the same string, or it is rejected
BEFORE the endpoint runs.

The two sides of the key (both must hold the same string):

  Server  — reads it from the environment variable THESIS_API_KEY, loaded
            into the uvicorn process with --env-file .env (.env is
            gitignored: the key never lives in the code or in git).
  Client  — sends it in the X-API-Key header of each request (in /docs:
            "Authorize" button, paste the key once).

Flow of a protected request (e.g. POST /runs):

  request arrives
    → FastAPI reads the X-API-Key header → calls require_api_key(key)
        ├─ missing or wrong key → raises 401, the endpoint never runs
        └─ correct key → returns nothing → FastAPI calls the endpoint

An endpoint is protected by adding the guard to its decorator:

  @app.post("/runs", ..., dependencies=[Depends(require_api_key)])

Generate a key once with:
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
"""

import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# 1. Read the key when the API starts (this module is imported by main.py).
# Fail at startup if no key is configured: never run unprotected
API_KEY = os.environ.get("THESIS_API_KEY")
if not API_KEY:
    raise RuntimeError("Set THESIS_API_KEY before starting the API")

# 2. Tells FastAPI to read the X-API-Key header (and adds an "Authorize"
# button to /docs). auto_error=False: a missing header gives None instead of
# FastAPI's own error, so require_api_key handles both cases the same way
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# If no key is provided or the wrong key, it raises an error
# Security(api_key_header): instruction to FastAPI: "before calling this function, fill key using api_key_header"
def require_api_key(key: str | None = Security(api_key_header)) -> None:
    if key is None or not secrets.compare_digest(key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")