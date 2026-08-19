## Pending
- Implement research question non linearity 
- Pendiente correr otro dia RQ3
- SUMO docker


## Improvements that won't be done
### Paralelization
- Don't parallelize combinations naively — I checked config/paths.py: every output path (data/DUE/BM/R-gap/rgap.parquet, etc.) is fixed, not per-run. Two main.py processes running concurrently would clobber each other's scratch files mid-simulation. Real parallelism would need those paths made run-scoped (e.g. per-PID temp dirs) — a nontrivial refactor, so only worth it if the nightly batch keeps growing and single-machine wall-clock becomes the actual bottleneck.
- That's a reasonable call — the risk isn't really about RAM headroom, it's that every output path in config/paths.py is fixed and shared, so two simulations running at once would overwrite each other's intermediate files mid-run in ways that could be hard to notice (wrong data silently mixed together) rather than a clean crash. Not worth that risk for a thesis where correctness of the numbers matters more than shaving off wall-clock time.
- If you ever want to revisit it, the lower-risk route isn't refactoring all those paths — it'd be running a second full copy of the repo (e.g. git worktree) so each process gets its own BASE_DIR and therefore its own isolated data/, mlruns/, etc. for free, no code changes. The catch is your local mlflow.db (SQLite) doesn't handle concurrent writers well, so you'd need a shared MLflow tracking server instead of the file-based DB — a separate piece of setup. Given the dev-config + --prepare-only caching we already have, I'd say leave it as sequential for now.
### Applying modern RL
- Important conversation about applying modern RL instead of Bush-Mosteller: https://chatgpt.com/c/69e5ffba-c078-8333-a234-3301f406e233








