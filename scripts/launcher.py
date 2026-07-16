"""
Grid-search launcher. Runs src/main.py for every parameter combination defined
in a design YAML, then optionally renders the Quarto analysis for a given RQ.

Usage: python launcher.py <design.yaml> [<research_question>]

The design YAML must have two keys:
  base_config: path to the base config.yaml
  grid:        {section: {param: [values]}}

Each combination is written to a temp file in EXPERIMENTS_TMP, passed to
main.py, then deleted. Pass a research question (e.g. RQ1) to also invoke
run_analysis.py after each simulation run.

Multi-seed evaluation
---------------------
For each research question, every hyperparameter combination is evaluated across
multiple random seeds by including ``seed`` as an axis in the grid. This is
necessary because the simulation has several independent sources of randomness
— demand generation (randomTrips), RL exploration and action selection, and
SUMO's internal stochasticity — so a single seed can produce results that are
unusually good or bad purely by chance.

Results are summarised as mean ± standard deviation over seeds.
For example, when studying the effect of the memory parameter (RQ2) (fake data):

  +---------+---------+----------+----------+-----------+-----------+-----------+
  | Memory  | Seed 42 | Seed 123 | Seed 999 | Seed 1999 | Seed 2026 | Mean R-gap|
  +---------+---------+----------+----------+-----------+-----------+-----------+
  | 1.00    | 0.004   | 0.006    | 0.005    | 0.005     | 0.004     | 0.0048    |
  | 0.75    | 0.007   | 0.008    | 0.006    | 0.007     | 0.009     | 0.0074    |
  | 0.50    | 0.015   | 0.018    | 0.014    | 0.017     | 0.016     | 0.0160    |
  | 0.25    | 0.045   | 0.051    | 0.039    | 0.048     | 0.043     | 0.0452    |
  +---------+---------+----------+----------+-----------+-----------+-----------+

  +---------+----------------+
  | Memory  | Mean ± SD      |
  +---------+----------------+
  | 1.00    | 0.005 ± 0.001  |
  | 0.75    | 0.007 ± 0.002  |
  | 0.50    | 0.016 ± 0.003  |
  | 0.25    | 0.045 ± 0.015  |
  +---------+----------------+

  Conclusion: across all evaluated seeds, reducing the memory level consistently
  increased the final R-gap.

The corresponding plot shows the hyperparameter on the x-axis, mean R-gap on
the y-axis, error bars (standard deviation or 95 % CI), and optionally a faint
line per seed to visualise individual variability.
"""

import os
import subprocess
import sys
import tempfile
import time
from itertools import product
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR, EXPERIMENTS_TMP


def _load_design(path):
    # 1. Load YAML containing the grid of parameters
    with open(path) as f:
        design = yaml.safe_load(f)

    # 2. Store the path of the base config file
    base_config_path = design["base_config"]

    # 3. From the design YAML select the grid of parameters
    grid = design["grid"]

    # 4. Flatten nested grid: [(section, param, [values]), ...]
    param_specs = [
        (section, param, values)
        for section, params in grid.items()
        for param, values in params.items()
    ]
    return base_config_path, param_specs


def _write_temp_config(base_config_path, param_specs, combination):
    # 1. Load base config file
    with open(base_config_path) as f:
        config = yaml.safe_load(f)

    # 2. Update config values with the actual grid combination
    for (section, param, _), value in zip(param_specs, combination):
        config[section][param] = value

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", dir=EXPERIMENTS_TMP, delete=False
    ) as tmp:
        yaml.dump(config, tmp, default_flow_style=False)
        tmp_path = tmp.name
    return tmp_path


def main():
    # 1. Config file path of the experiment that will be run
    path = sys.argv[1]
    # 2. Research question that will be analyzed
    research_question = sys.argv[2] if len(sys.argv) > 2 else None

    # 3. Extract grid combinations
    base_config_path, param_specs = _load_design(path)

    # 4. For each combination of parameters
    for combination in product(*[values for _, _, values in param_specs]):

        # 5. Write a temporary config YAML file containing the combination of
        # hyperparameters to try
        tmp_path = _write_temp_config(base_config_path, param_specs, combination)

        # 6. Run simulation code with YAML config tmp file
        subprocess.run(["python", "main.py", tmp_path], cwd=BASE_DIR / "src")

        # 7. (Optionally) Run analysis code
        if research_question:
            subprocess.run(
                [
                    "python",
                    str(BASE_DIR / "scripts" / "run_analysis.py"),
                    research_question,
                ]
            )

        os.unlink(tmp_path)
