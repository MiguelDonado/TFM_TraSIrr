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

---

## 2. Run analysis manually
See module docstring /home/miguel/6.Projects/Thesis/scripts/run_analysis.py

## 3. Batch run (grid search)
See module docstring /home/miguel/6.Projects/Thesis/scripts/launcher.py