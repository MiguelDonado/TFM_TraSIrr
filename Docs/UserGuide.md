# User Guide

## Overview

The program has two execution paths: a **single run** (one config, one simulation)
and a **batch run** (grid search over parameter combinations).

---

## 0. Start MLflow
```sh
cd /home/miguel/6.Projects/Thesis
python scripts/start_mlflow.py
```

## 1. Single run

```sh
cd /home/miguel/6.Projects/Thesis
python src/main.py <config.yaml>
```

**Config files (pick one):**

| File | Purpose |
|------|---------|
| `experiments/developer_modes/debug.yaml` | Fast run for development |
| `experiments/developer_modes/development.yaml` | Full dev run |
| `experiments/developer_modes/production.yaml` | Production settings |

**Optional `--mode` flag** (default: `train`):

```sh
python src/main.py <config.yaml> --mode compute_routes   # generate routes then exit
python src/main.py <config.yaml> --mode eval_gui         # replay last episode in SUMO GUI
python src/main.py <config.yaml> --mode train            # full training run (default)
```

---

## 2. Run analysis manually

```sh
cd /home/miguel/6.Projects/Thesis
python scripts/run_analysis.py RQ1
```

---

## 3. Batch run (grid search)

```sh
cd /home/miguel/6.Projects/Thesis
python scripts/launcher.py <design.yaml> [<research_question>]
```

The launcher iterates over every parameter combination defined in the design YAML,
writes a temp config, runs `main.py` for each, and optionally runs the analysis.

**Design files:**

| File | Research question |
|------|------------------|
| `experiments/rq1/design.yaml` | RQ1 |
| `experiments/rq2/design.yaml` | RQ2 |

Example with analysis:

```sh
python scripts/launcher.py experiments/rq1/design.yaml RQ1
```

## 4. Congestion metric plot
```sh
cd /home/miguel/6.Projects/Thesis
python src/tools/plot_congestion_metric.py <design.yaml>
```