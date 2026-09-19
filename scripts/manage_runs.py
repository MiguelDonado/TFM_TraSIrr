"""
Bulk-archives or bulk-restores MLflow simulation runs for a given research
question.

Runs tagged status = "active" are the ones included in analysis (see
run_analysis.py). When new simulation data replaces an old sweep for a
research question, the old runs need to be --archive so they drop out of
the next analysis run; --restore reverses that (deletes the status tag), 
bringing archived runs back into the active set. Doing this one run at a 
time in the MLflow UI is tedious for a full grid (e.g. 15+ runs), 
so this script does it in bulk.

Usage:
  python scripts/manage_runs.py <research_question> --archive             dry run
  python scripts/manage_runs.py <research_question> --archive --apply     actually archive
  python scripts/manage_runs.py <research_question> --restore --apply     actually restore (remove status tag)

--archive/--restore are mutually exclusive and one is required.
--apply is required to write anything; without it the script only lists
which runs would be affected.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import mlflow
from mlflow import MlflowClient

from mlflow_tracking.utils import set_tracking_uri

MODES = {
    "archive": {
        "status_filter": "active",
        "verb": "archive",
        "past_participle": "Archived",
    },
    "restore": {
        "status_filter": "archived",
        "verb": "restore",
        "past_participle": "Restored",
    },
}


def manage_runs():
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    mode_flags = [m for m in MODES if f"--{m}" in sys.argv]

    if len(args) != 1 or len(mode_flags) != 1:
        sys.exit(
            "Usage: python scripts/manage_runs.py <research_question> "
            "--archive|--restore [--apply]"
        )

    research_question = args[0]
    if not re.match(r"^RQ\d+$", research_question):
        sys.exit(f"Invalid research question '{research_question}'. Expected format: RQ1, RQ2, ...")

    mode = MODES[mode_flags[0]]
    apply = "--apply" in sys.argv

    set_tracking_uri()

    filter_string = (
        f"tags.research_question = '{research_question}' "
        f"and tags.run_type = 'simulation' and tags.status = '{mode['status_filter']}'"
    )
    runs = mlflow.search_runs(experiment_names=["Thesis"], filter_string=filter_string)

    if runs.empty:
        print(f"No {mode['status_filter']} simulation runs found for {research_question}.")
        return

    name_col = "tags.mlflow.runName"
    print(f"{len(runs)} {mode['status_filter']} run(s) for {research_question}:")
    for _, run in runs.iterrows():
        name = run[name_col] if name_col in run.index else run["run_id"]
        print(f"  {run['run_id']}  {name}")

    if not apply:
        print(f"\nDry run — no changes made. Re-run with --apply to {mode['verb']} these runs.")
        return

    client = MlflowClient()
    for run_id in runs["run_id"]:
        if mode["verb"] == "archive":
            client.set_tag(run_id, "status", "archived")
        else:
            client.delete_tag(run_id, "status")

    print(f"\n{mode['past_participle']} {len(runs)} run(s) for {research_question}.")


if __name__ == "__main__":
    manage_runs()