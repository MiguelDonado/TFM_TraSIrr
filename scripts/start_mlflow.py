"""
This script ensures MLflow starts properly.
That is that the MLflow UI reads the correct Backend DB path
"""

import subprocess
import sys
from pathlib import Path

# Inserts the project's src/ directory into sys.path before imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BACKEND_DB

cmd = ["mlflow", "ui", "--backend-store-uri", f"sqlite:///{BACKEND_DB}"]
subprocess.run(cmd)
