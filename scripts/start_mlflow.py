"""
Launches the MLflow UI pointed at the project's SQLite backend store.

Without this, mlflow ui defaults to ./mlruns/ and misses all logged runs.
BACKEND_DB is defined in src/config/paths.py.
"""

import subprocess
import sys
from pathlib import Path

# Inserts the project's src/ directory into sys.path before imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BACKEND_DB

cmd = ["mlflow", "ui", "--backend-store-uri", f"sqlite:///{BACKEND_DB}"]
subprocess.run(cmd)
