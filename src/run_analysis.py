"""
Execution of this script "python run_analysis.py RQ1"
"""

import os
import subprocess
import sys

from MLflow.analysis import log_analysis_run_MLflow
from paths import BASE_DIR


def run_analysis_script(research_question):
    print("cwd =", os.getcwd())

    qmd = BASE_DIR / f"r/{research_question}/{research_question}.qmd"

    subprocess.run(
        ["/usr/lib/rstudio/resources/app/bin/quarto/bin/quarto", "render", qmd],
        check=True,
    )


if __name__ == "__main__":
    research_question = sys.argv[1]
    research_question_path = BASE_DIR / "r" / research_question

    # 1. Execute R script
    run_analysis_script(research_question)

    # 2. Log to MLflow
    log_analysis_run_MLflow(research_question, research_question_path)
