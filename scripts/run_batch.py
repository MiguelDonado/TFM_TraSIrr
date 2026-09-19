"""
Batch runner: runs the grid search for one or more research questions back
to back, so a full sweep (e.g. RQ1-RQ4) can be kicked off before going to
bed and checked on in the morning.

The research questions to run are given as CLI arguments; the design YAML
for each is assumed to live at experiments/<rq, lowercased>/design.yaml
(or design_dev.yaml with --dev). For each research question, every
combination in its design YAML's grid is written to a temp config and run
through src/main.py.

Progress and subprocess output are logged (with timestamps) to both the
console and experiments/logs/<timestamp>.log. If a research question fails,
it's recorded and the batch moves on to the next one rather than aborting
the whole night.

Usage:
  python scripts/run_batch.py RQ1 RQ2 RQ3 [--dev] [--shutdown]
                                                          simulations only

Dev vs production configs
--------------------------
Each research question has up to two design YAMLs under experiments/rqN/:

  design.yaml      — points at experiments/base.yaml (production scale:
                      simulation_time=3600, warm_up_time=300, n_agents=2000).
                      Used by default, for the real, overnight runs.

  design_dev.yaml  — points at experiments/base_dev.yaml, a copy of
                      base.yaml with simulation_time, warm_up_time and
                      n_agents scaled down ~10x. Same grid as design.yaml.
                      Used (pass --dev) to get a fast (minutes, not hours)
                      run during the day, just to build/debug the RQ's
                      analysis script (plot types, colors, axis ranges)
                      against real-shaped data before waiting on the
                      overnight production run. Not every research question
                      has one — those are SKIPPED when --dev is passed.

  Note: dev-scale R-gap magnitude and convergence timing will differ
  somewhat from production (fewer agents, shorter horizon), so treat
  anything tuned against --dev output (axis ranges, thresholds) as
  provisional until re-checked against a production run.

Multi-seed evaluation
---------------------
For each research question, every hyperparameter combination is evaluated across
multiple random seeds by including ``seed`` as an axis in the grid. This is
necessary because the simulation has several independent sources of randomness
— demand generation (randomTrips), RL exploration and action selection, and
SUMO's internal stochasticity — so a single seed can produce results that are
unusually good or bad purely by chance.
In particular, the experiments will be evaluated using 5 different seeds.

Results are summarised as mean ± standard deviation over seeds.
"""

import logging
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from itertools import product
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR, EXPERIMENTS_TMP

# 1. One timestamped log file per batch run
logs_dir = BASE_DIR / "experiments" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
log_path = logs_dir / f"{datetime.now():%Y%m%d_%H%M%S}.log"

# 2. Log to console and file simultaneously, timestamped per line
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
)
log = logging.getLogger("run_batch")


def _load_design(path):
    # 1. Load YAML containing the grid of parameters
    with open(path) as f:
        design = yaml.safe_load(f)

    # 2. Store the path of the base config file. Resolved against BASE_DIR
    # so a path relative to the repo root works both natively and inside
    # the container (BASE_DIR / already-absolute-path just ignores BASE_DIR,
    # so this stays backward-compatible with any still-absolute entries).
    base_config_path = BASE_DIR / design["base_config"]

    # 3. From the design YAML select the grid of parameters
    grid = design["grid"]

    # 4. Flatten nested grid: [(section, param, [values]), ...]
    param_specs = [
        (section, param, values)
        for section, params in grid.items()
        for param, values in params.items()
    ]
    return base_config_path, param_specs


def _write_temp_config(base_config_path, param_specs, combination, research_question):
    # 1. Load base config file
    with open(base_config_path) as f:
        config = yaml.safe_load(f)

    # 2. Update config values with the actual grid combination
    for (section, param, _), value in zip(param_specs, combination):
        config[section][param] = value

    # 3. Inject research question so it is logged as an MLflow param
    config["mode_and_flags"]["research_question"] = research_question

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", dir=EXPERIMENTS_TMP, delete=False
    ) as tmp:
        yaml.dump(config, tmp, default_flow_style=False)
        tmp_path = tmp.name
    return tmp_path


def _run_combination(tmp_path):
    # Stream src/main.py's output through the logger (console + file) rather
    # than letting it inherit the terminal directly, so every line lands in
    # the timestamped batch log.
    process = subprocess.Popen(
        [sys.executable, "src/main.py", tmp_path],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in process.stdout:
        log.info(line.rstrip())
    process.wait()
    return process.returncode


def _run_research_question(research_question, design_path):
    # 1. Extract grid combinations
    base_config_path, param_specs = _load_design(design_path)
    combinations = list(product(*[values for _, _, values in param_specs]))
    total = len(combinations)

    # 2. For each combination of parameters, run the simulation. Individual
    # combination failures don't abort the research question — move on to
    # the next combination, same as before.
    for i, combination in enumerate(combinations, start=1):
        combo_str = " | ".join(
            f"{section}.{param}={value}"
            for (section, param, _), value in zip(param_specs, combination)
        )
        log.info("--- [%d/%d] %s ---", i, total, combo_str)

        tmp_path = _write_temp_config(base_config_path, param_specs, combination, research_question)
        _run_combination(tmp_path)
        Path(tmp_path).unlink()


def main():
    # 1. Research questions to run tonight are passed as CLI args, e.g.
    # `python scripts/run_batch.py RQ1 RQ2 RQ3`
    research_questions = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if not research_questions:
        sys.exit("Usage: python scripts/run_batch.py RQ1 RQ2 ... [--dev] [--shutdown]")
    for research_question in research_questions:
        if not re.match(r"^RQ\d+$", research_question):
            sys.exit(f"Invalid research question '{research_question}'. Expected format: RQ1, RQ2, ...")

    dev = "--dev" in sys.argv

    # 2. Track outcome of each research question to print a summary at the end
    results = []

    for research_question in research_questions:
        design_name = "design_dev.yaml" if dev else "design.yaml"
        design_path = BASE_DIR / "experiments" / research_question.lower() / design_name
        log.info("=== %s ===", research_question)

        # 3. Skip research questions whose design YAML hasn't been written yet
        if not design_path.exists():
            log.info("SKIPPED: %s not found", design_path)
            results.append((research_question, "SKIPPED"))
            continue

        try:
            _run_research_question(research_question, design_path)
            status = "OK"
        except Exception as e:
            log.exception("FAILED: %s", research_question)
            status = f"FAILED ({e})"

        # 4. Record outcome and move on to the next research question,
        # even on failure, so one bad run doesn't block the rest of the batch
        log.info("%s: %s", research_question, status)
        results.append((research_question, status))

    # 5. Final summary of the whole batch
    log.info("=== Batch summary ===")
    for research_question, status in results:
        log.info("%s: %s", research_question, status)

    # 6. Shutdown computer
    if "--shutdown" in sys.argv:
        log.info("Batch complete. Shutting down computer in 1 minute...")
        subprocess.run(["shutdown", "-h", "+1"])


if __name__ == "__main__":
    main()