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

# Config file path of the experiment that will be run
path = sys.argv[1]
# Research question that will be analyzed
research_question = sys.argv[2] if len(sys.argv) > 2 else None

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

# 5. For each combination of parameters
for combination in product(*[values for _, _, values in param_specs]):
    # 6. Load base config file
    with open(base_config_path) as f:
        config = yaml.safe_load(f)

    # 7. Update config values with the actual grid combination
    for (section, param, _), value in zip(param_specs, combination):
        config[section][param] = value

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", dir=EXPERIMENTS_TMP, delete=False
    ) as tmp:
        yaml.dump(config, tmp, default_flow_style=False)
        tmp_path = tmp.name

    # 8. Run simulation code with YAML config tmp file
    subprocess.run(["python", "main.py", tmp_path], cwd=BASE_DIR / "src")

    # 9. (Optionally) Run analysis code
    if research_question:
        subprocess.run(
            ["python", str(BASE_DIR / "scripts" / "run_analysis.py"), research_question]
        )

    os.unlink(tmp_path)
