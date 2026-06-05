"""
This script ensures MLflow starts properly.
That is that the MLflow UI reads the correct Backend DB path
"""

import subprocess

from paths import BACKEND_DB

cmd = ["mlflow", "ui", "--backend-store-uri", f"sqlite:///{BACKEND_DB}"]
subprocess.run(cmd)
