"""
Execution of this script "python run_analysis.py RQ1"
"""

import os
import subprocess
import sys
from pathlib import Path

# Inserts the project's src/ directory into sys.path before imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR
from mlflow_tracking.analysis import log_analysis_run_MLflow


def run_analysis_rq():
    """Execute a research question analysis and log results to MLflow."""

    research_question = sys.argv[1]

    _render_analysis(research_question)
    log_analysis_run_MLflow(
        research_question=research_question,
        artifact_path=BASE_DIR / "r" / research_question,
    )

    os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")


def _render_analysis(research_question: str) -> None:
    """Render the Quarto report as well as plots for a research question."""
    qmd_file = BASE_DIR / f"r/{research_question}/{research_question}.qmd"

    subprocess.run(
        [
            "/usr/lib/rstudio/resources/app/bin/quarto/bin/quarto",
            "render",
            str(qmd_file),
        ],
        check=True,
    )


if __name__ == "__main__":
    run_analysis_rq()
