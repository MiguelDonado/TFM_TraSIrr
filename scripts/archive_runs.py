"""
Bulk-archives MLflow simulation runs by setting tags.status from "active" to
"archived" for a given research question.

Runs tagged status = "active" are the ones included in analysis (see
run_analysis.py). When new simulation data replaces an old sweep for a
research question, the old runs need to be archived so they drop out of
the next analysis run. Doing this one run at a time in the MLflow UI is
tedious for a full grid (e.g. 15+ runs), so this script does it in bulk.

Usage:
  python scripts/archive_runs.py <research_question>            dry run (default)
  python scripts/archive_runs.py <research_question> --apply    actually archive

--apply is required to write anything; without it the script only lists
which runs would be archived.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import mlflow
from mlflow import MlflowClient

from mlflow_tracking.utils import set_tracking_uri


def archive_runs():
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(args) != 1:
        sys.exit("Usage: python scripts/archive_runs.py <research_question> [--apply]")

    research_question = args[0]
    if not re.match(r"^RQ\d+$", research_question):
        sys.exit(f"Invalid research question '{research_question}'. Expected format: RQ1, RQ2, ...")

    apply = "--apply" in sys.argv

    set_tracking_uri()

    filter_string = (
        f"tags.research_question = '{research_question}' "
        "and tags.run_type = 'simulation' and tags.status = 'active'"
    )
    runs = mlflow.search_runs(experiment_names=["Thesis"], filter_string=filter_string)

    if runs.empty:
        print(f"No active simulation runs found for {research_question}.")
        return

    name_col = "tags.mlflow.runName"
    print(f"{len(runs)} active run(s) for {research_question}:")
    for _, run in runs.iterrows():
        name = run[name_col] if name_col in run.index else run["run_id"]
        print(f"  {run['run_id']}  {name}")

    if not apply:
        print("\nDry run — no changes made. Re-run with --apply to archive these runs.")
        return

    client = MlflowClient()
    for run_id in runs["run_id"]:
        client.set_tag(run_id, "status", "archived")

    print(f"\nArchived {len(runs)} run(s) for {research_question}.")


if __name__ == "__main__":
    archive_runs()
