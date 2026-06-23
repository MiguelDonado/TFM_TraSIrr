# Session Notes — 2026-06-23

## Topic
`src/` file organization — step-by-step refactor

---

## Decisions made

| Question | Decision |
|---|---|
| Move `paths.py` to `config/`? | Yes — done |
| Move `experiment.py` to `utils/`? | No — keep at `src/` root next to `main.py` |

---

## Work completed

### Moved `src/paths.py` → `src/config/paths.py`
- Fixed `BASE_DIR` anchor: `parent.parent` → `parent.parent.parent` (one level deeper after the move)
- Updated all 18 import sites across the codebase (`from paths import` → `from config.paths import`)
- Verified `BASE_DIR` and `YAML_CONF` resolve correctly at runtime
- Deleted original `src/paths.py`

---

## Agreed target structure (in progress)

```
src/
  main.py           ← entry point (stays)
  experiment.py     ← pipeline support for main (stays)

  simulation/       ← next: move environment.py + scenario.py here
  config/           ← done: paths.py + config.py
  mlflow_tracking/  ← pending: absorb load_mlflow_results.py + start_mlflow.py
  ../scripts/       ← pending: move launcher.py + run_analysis.py here
```

---

## Pending steps

1. Create `simulation/` package — move `environment.py` + `scenario.py`
2. Move `load_mlflow_results.py` + `start_mlflow.py` into `mlflow_tracking/`
3. Move `launcher.py` + `run_analysis.py` to `scripts/` at the project root