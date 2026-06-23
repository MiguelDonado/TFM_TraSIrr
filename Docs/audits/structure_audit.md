# Repository Structure Audit

**Date:** 2026-06-22
**Scope:** Full repository (excluding `renv/`)
**Focus:** Folder hierarchy, naming, scalability, maintainability

---

## Metrics at a Glance

| Metric | Value |
|---|---|
| Total Python source lines | 4,697 |
| Top-level directories | 15 |
| Deepest nesting (code) | 5 levels (`sumo/config/edge_visualization/`) |
| Empty directories | 5 confirmed |
| Duplicate data files | 8+ casing-variant pairs in `data/DUE/duaIterate/` |
| **Maintainability score** | **5 / 10** |

---

## Largest Folders (by file count, excluding `renv/`)

| Folder | Files | Notes |
|---|---|---|
| `Docs/research/Papers/assets/` | 55 | Paper screenshot images |
| `Walkthrough/Images/` | 16 | Demo walkthrough PNGs |
| `data/DUE/duaIterate/` | 15 (direct) | Includes duplicate-casing pairs |
| `Docs/meetings/` | 12 | Meeting notes |
| `output/figures/` | 11 | Generated figures |
| `src/` (root, no subdirs) | 10 | Loose orchestration files |
| `src/DUE_convergence/` | 5 py files | Core algorithm |

## Largest Files (non-`renv/`)

| File | Size | Problem |
|---|---|---|
| `Examples/visualization/plot_trajectories/DEMO.mp4` | 53 MB | Binary in git |
| `Examples/Decal/CenteringDecal.mp4` | 46 MB | Binary in git |
| `Examples/gridDistricts/BarcelonaNetworkDesRUTGE.net.xml` | 34 MB | Binary in git |
| `src/scripts/map.osm` | 12 MB | Data file inside `src/` |
| `src/scripts/net.net.xml` | 5.7 MB | Data file inside `src/` |
| `src/scenario.py` | 490 lines | Largest Python file |
| `src/paths.py` | 225 lines | God path registry |

## Dependency Hotspots

Files imported by the most other modules:

1. **`src/paths.py`** — imported by `scenario.py`, `experiment.py`, all of `DUE_convergence/`, `MLflow/`, `parsing/sumo_outputs.py`, `analysis/sumo_edge_analysis.py`, `demand_calibration/`, `stopping_rule/stopping_rule.py`, `agents/agent.py`, `launcher.py`, `run_analysis.py`. Every module touches it.
2. **`src/config/config.py`** — imported by nearly all modules.
3. **`src/parsing/`** — consumed by `experiment.py`, `DUE_convergence/duaiterate.py`, `scenario.py`.
4. **`src/utils/`** — consumed by `scenario.py`, `demand_calibration/`, `DUE_convergence/`.

---

## Folder Complexity Score

```
src/              ████████░░  7/10  (too many loose files at root, junk-drawer scripts/)
data/             ████████░░  7/10  (mirrored DUE structure, vague internal/, stale dupes)
Docs/             ███░░░░░░░  3/10  (flat, readable)
sumo/             ████░░░░░░  4/10  (growing net/ taxonomy, demand_calibration duplication)
r/                █████░░░░░  5/10  (mixed root files + RQ subdir pattern)
experiments/      ██░░░░░░░░  2/10  (clean now, but no run-id in paths is a latent risk)
Examples/         ████░░░░░░  4/10  (educational, not code — separate concern entirely)
thesis_document/  ███░░░░░░░  3/10  (personal workspace, low impact on code)
```

---

## Current Structure Weaknesses

### 1. `src/scripts/` — Junk Drawer

Contains three completely different categories with no separation:

- **Computation helpers** (imported by `demand_calibration/`): `get_avg_speed.py`, `get_free_flow_speed.py`, `get_total_length_network.py`
- **One-off network tools** (standalone CLI): `modify_speed_lanes.py`, `netconvert.py`, `network_stats.py`, `network_stats_edges_len.py`
- **Large data files**: `map.osm` (12 MB), `net.net.xml` (5.7 MB) — SUMO network files that belong in `sumo/net/`
- **Output artifacts**: `src/scripts/output/*.csv` — CSV files from analysis runs, not source code

The helpers are imported from `demand_calibration/`, making `scripts/` a de-facto internal library with no clear boundary between importable code and CLI tools.

### 2. `data/internal/` — Vague Name, Mixed Concerns

"Internal" communicates nothing. The directory holds three distinct domains:
- **Agent state**: `agents_od.parquet`, `agents_history.parquet`, `od_routes.parquet`
- **BM results**: `BM_results.parquet`, `policy_change_BM.parquet`, `rewards.parquet`, `actions.parquet`
- **Environment data**: `free_flow_travel_times.parquet`, `times_interval.parquet`

### 3. `data/DUE/` — Mirrored Structure That Will Keep Doubling

`data/DUE/BM/` and `data/DUE/duaIterate/` are near-identical mirrors:

```
BM/                        duaIterate/
├── R-gap/                 ├── R-gap/
├── TDSP/                  ├── TDSP/
│   ├── trips/             │   ├── trips/        (empty)
│   ├── weights/           │   ├── weights/       (empty)
│   └── shortest_paths/    │   └── shortest_paths/ (empty)
└── missingness/           └── missingness/
```

Every new algorithm adds another full mirror. `paths.py` already has a `BM` block and an identical `duaIterate` block (~50 lines each). Adding a third algorithm adds another ~50-line block.

### 4. Case/Spelling Chaos in `data/DUE/duaIterate/`

8+ side-by-side file pairs with different casing — a refactoring that was never completed:

```
actions_duaIterate.parquet             ← canonical
actions_dueiterate.parquet             ← stale duplicate

costs_paths_odtp_k_duaIterate.parquet
costs_paths_odtp_k_dueIterate.parquet  ← note "dueIterate"

missingness_duaIterate_by_edge.parquet
missingness_dueiterate_by_edge.parquet
... (×4 more)
```

Same problem in `sumo/routes/`: `routes_duaIterate.rou.xml` and `routes_dueiterate.rou.xml` coexist.

### 5. `paths.py` — God File Destined to Break

225 lines of flat path constants with no structure. The `duaIterate` half is a near-verbatim copy of the `BM` half with `_duaIterate` appended to every name. At 2x the file will be ~450 lines; at 5x, over 1,000 lines. This is a structural signal: paths should be parameterized, not enumerated.

### 6. Misplaced Files

| File | Current location | Should be |
|---|---|---|
| `map.osm` | `src/scripts/` | `sumo/net/` |
| `net.net.xml` | `src/scripts/` | `sumo/net/` |
| `src/scripts/output/*.csv` | `src/scripts/output/` | `output/` or `data/` |
| `src/mlflow.db` | `src/` | `mlflow_db/` (or gitignored entirely) |

### 7. `audits/` — Orphaned at Root

The four audit markdown files live at the project root while all other documentation is in `Docs/`. They belong at `Docs/audits/`.

### 8. Empty Directories

Five confirmed empty directories:

- `data/DUE/BM/TDSP/shortest_paths/`
- `data/DUE/BM/TDSP/weights/`
- `data/DUE/duaIterate/TDSP/shortest_paths/`
- `data/DUE/duaIterate/TDSP/weights/`
- `data/DUE/duaIterate/TDSP/trips/`
- `experiments/tmp/`

### 9. Capitalization Inconsistency at Root

`Docs/`, `Examples/`, `Walkthrough/` use PascalCase while `src/`, `r/`, `data/`, `sumo/`, `experiments/`, `output/` use lowercase. No convention is enforced.

### 10. R Analysis Not Organized to Scale

`r/` has `r/RQ1/` as a subdir but also `plots.R`, `helper_plots.R`, `theme.R` at its root with no clear RQ association. When RQ2 analysis is added as `r/RQ2/`, the root R files remain ambiguous.

### 11. Dual Figure Output Locations

- `output/figures/` — general figures
- `r/RQ1/figures/` — RQ1-specific figures

A developer looking for "the plot from the analysis" has two places to check.

### 12. `mlruns/mlruns/` Double Nesting

`ARTIFACTS_STORAGE = BASE_DIR / "mlruns" / "mlruns"` creates a `mlruns/mlruns/` path. This is an MLflow configuration quirk but is opaque — a new developer will not know where artifacts actually land.

---

## Proposed Target Structure

### For 2x Current Size

Cosmetic cleanups and splitting `scripts/` properly. No major surgery.

```
Thesis/
├── src/
│   ├── agents/
│   ├── analysis/
│   ├── config/
│   ├── demand_calibration/
│   ├── DUE_convergence/
│   ├── mlflow_tracking/          ← rename from MLflow/ (lowercase, descriptive)
│   ├── parsing/
│   ├── stopping_rule/
│   ├── utils/
│   │   ├── network.py
│   │   ├── od_routes.py
│   │   ├── sumo_xml.py
│   │   └── network_helpers.py    ← absorb get_avg_speed, get_free_flow_speed,
│   │                                get_total_length_network (were imported helpers)
│   ├── tools/                    ← rename from scripts/ (standalone CLI only)
│   │   ├── modify_speed_lanes.py
│   │   ├── netconvert.py
│   │   ├── network_stats.py
│   │   └── network_stats_edges_len.py
│   ├── environment.py
│   ├── experiment.py
│   ├── launcher.py
│   ├── load_mlflow_results.py
│   ├── main.py
│   ├── paths.py
│   ├── run_analysis.py
│   ├── scenario.py
│   └── start_mlflow.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── od_matrix/
│   ├── agent_state/              ← rename from internal/
│   │   ├── agents_od.parquet
│   │   ├── agents_history.parquet
│   │   ├── od_routes.parquet
│   │   ├── actions.parquet
│   │   ├── rewards.parquet
│   │   └── BM_results.parquet
│   ├── environment/              ← split out from internal/
│   │   ├── free_flow_travel_times.parquet
│   │   └── times_interval.parquet
│   ├── DUE/
│   │   ├── BM/                   (stale empty dirs removed)
│   │   └── duaIterate/           (stale duplicate files removed, one casing enforced)
│   └── mlflow_metadata/          ← rename from MLflow/
│
├── sumo/
│   ├── config/
│   ├── demand_calibration/
│   ├── net/
│   │   ├── koh/
│   │   │   ├── 1st.net.xml
│   │   │   └── 2nd.net.xml
│   │   ├── day_to_day/
│   │   │   ├── 2nd.net.xml
│   │   │   └── 3rd_nguyen_dupuis.net.xml
│   │   ├── popular/
│   │   │   ├── Sioux_Falls.net.xml
│   │   │   └── benchmark_demands/
│   │   └── scratch/              ← receives map.osm and net.net.xml from src/scripts/
│   │       ├── map.osm
│   │       └── net.net.xml
│   └── routes/                   (one file per algorithm, duplicates removed)
│
├── experiments/
│   ├── developer_modes/
│   ├── rq1/
│   └── rq2/
│
├── r/
│   ├── shared/                   ← root R files moved here
│   │   ├── theme.R
│   │   ├── helper_plots.R
│   │   └── plots.R
│   └── RQ1/
│       ├── RQ1.qmd
│       └── figures/
│
├── output/
│   └── figures/                  (single figures destination)
│
├── docs/                         ← lowercase
│   ├── audits/                   ← move from root audits/
│   ├── meetings/
│   ├── research/
│   ├── design.md
│   ├── theory.md
│   ├── heuristics.md
│   ├── UserGuide.md
│   └── DUE_convergence_gotchas.md
│
├── mlflow_db/
├── mlruns/
├── Examples/                     (unchanged — educational, low churn)
├── thesis_document/              (unchanged — personal workspace)
└── Walkthrough/                  (unchanged — media)
```

### For 5x Current Size

At 5x the main pain points are: multiple algorithms × multiple networks × multiple runs needing separate data namespaces, and `paths.py` becoming unmanageable.

```
src/
├── due/                          ← merge DUE_convergence/ (algorithm implementations)
│   ├── bm/
│   │   ├── bm.py
│   │   ├── rgap.py
│   │   ├── tdsp.py
│   │   └── aggregation.py
│   ├── duaiterate/
│   │   └── duaiterate.py
│   └── convergence.py            ← shared DUE loop logic
│
├── simulation/                   ← break up scenario.py (490 lines)
│   ├── scenario.py               ← trimmed to orchestration only
│   ├── environment.py
│   └── demand_calibration/
│
│   paths.py                      ← REPLACED by a path factory:
│                                    def get_due_paths(algorithm: str) -> DuePaths
│                                    instead of duplicating every path per algorithm

data/
└── DUE/
    └── {algorithm}/              ← bm, duaiterate (one casing, enforced)
        └── {network}/            ← koh_1st, sioux_falls, nguyen_dupuis
            ├── R-gap/
            ├── TDSP/
            └── missingness/

experiments/
└── {rq}/
    └── {network}/
        └── {run_id}.yaml         ← once multi-network experiments are needed
```

---

## Concrete File Moves and Refactorings

### Priority 1 — Cleanup (no code changes)

| Action | From | To |
|---|---|---|
| Move | `audits/*.md` | `Docs/audits/` |
| Move | `src/scripts/map.osm` | `sumo/net/scratch/` |
| Move | `src/scripts/net.net.xml` | `sumo/net/scratch/` |
| Move | `src/scripts/output/*.csv` | `output/data/` |
| Delete | `src/mlflow.db` | (stale, already gitignored) |
| Delete | 6 empty directories | (listed above) |
| Delete | Duplicate-casing `dueiterate` files in `data/DUE/duaIterate/` | Keep `duaIterate` variants only |
| Delete | `routes_dueiterate.rou.xml` in `sumo/routes/` | Keep `routes_duaIterate.rou.xml` only |

### Priority 2 — Rename/Reorganize (requires import updates)

| Action | Detail |
|---|---|
| Rename `src/MLflow/` → `src/mlflow_tracking/` | Update all imports (`from MLflow.X` → `from mlflow_tracking.X`) |
| Move `get_avg_speed.py`, `get_free_flow_speed.py`, `get_total_length_network.py` to `src/utils/` | Update `demand_calibration/` imports |
| Rename remaining `src/scripts/` → `src/tools/` | No import changes needed (these are standalone) |
| Rename `data/internal/` → `data/agent_state/` + `data/environment/` | Update `paths.py` constants |
| Create `r/shared/` and move root R files there | |

### Priority 3 — Refactor (code changes, when pain is felt)

| Action | Detail |
|---|---|
| Parameterize `paths.py` | Replace duplicated BM/duaIterate blocks with `get_due_paths(algo: str)` returning a dataclass |
| Split `scenario.py` | 490 lines; extract SUMO runner, output parser, and agent loop into separate files |
| Add `{network}` dimension to `data/DUE/` | Before a third network is benchmarked |

---

## Migration Plan

```
Phase 1 (no-risk, ~1 hour)
  ✓ Move data files out of src/scripts/
  ✓ Delete stale casing-duplicate files in data/DUE/duaIterate/ and sumo/routes/
  ✓ Delete empty directories
  ✓ Move audits/ into Docs/

Phase 2 (import updates, ~2 hours, run simulation after each rename)
  ✓ Rename src/MLflow/ → src/mlflow_tracking/
  ✓ Move get_avg_speed, get_free_flow_speed, get_total_length_network to src/utils/
  ✓ Rename remaining src/scripts/ → src/tools/
  ✓ Rename data/internal/ → data/agent_state/ + data/environment/
  ✓ Move r/ root files into r/shared/

Phase 3 (before adding RQ2 / a third algorithm)
  ✓ Parameterize paths.py to avoid a third copy-paste block
  ✓ Add {network} dimension to data/DUE/ paths
  ✓ Create r/RQ2/ following the same pattern as r/RQ1/
```

---

## Summary

The structure is coherent for a solo research project at its current size, but has three latent structural debts that will compound quickly:

1. **Mirrored `data/DUE/` pattern** — already repeated once for duaIterate; a third algorithm forces a third mirror.
2. **`paths.py` god file** — already doubled once; adding algorithms or networks makes it unmanageable.
3. **`src/scripts/` junk drawer** — mixes importable helpers, standalone tools, and large data files.

The Phase 1 cleanup takes roughly an hour and has zero risk. The `paths.py` parameterization (Phase 3) is the most important architectural fix and should happen before a third algorithm or a second network enters the benchmark.


## Audit Review Summary
### Implemented changes
#### Priority 1 — Cleanup (no code changes)
| Move | `audits/*.md` | `Docs/audits/` |
| Delete | `src/mlflow.db` | (stale, already gitignored) |
| Delete | Duplicate-casing `dueiterate` files in `data/DUE/duaIterate/` | Keep `duaIterate` variants only |
| Delete | `routes_dueiterate.rou.xml` in `sumo/routes/` | Keep `routes_duaIterate.rou.xml` only |
#### Priority 2 — Rename/Reorganize (requires import updates)
| Rename `src/MLflow/` → `src/mlflow_tracking/` | Update all imports (`from MLflow.X` → `from mlflow_tracking.X`) |
| Move `get_avg_speed.py`, `get_free_flow_speed.py`, `get_total_length_network.py` to `src/utils/` | Update `demand_calibration/` imports |
| Rename remaining `src/scripts/` → `src/tools/` | No import changes needed (these are standalone) |
| Rename `data/internal/` → `data/agent_state/` + `data/environment/` | Update `paths.py` constants |
| Create `r/shared/` and move root R files there | |
### Priority 3 — Refactor (code changes, when pain is felt)
| Parameterize `paths.py` | Replace duplicated BM/duaIterate blocks with `get_due_paths(algo: str)` returning a dataclass |

### Rejected changes
| Move | `src/scripts/map.osm` | `sumo/net/scratch/` |       (deleted)
| Move | `src/scripts/net.net.xml` | `sumo/net/scratch/` |   (deleted)
| Move | `src/scripts/output/*.csv` | `output/data/` |       (deleted)
| Delete | 6 empty directories | (listed above) |            (they are empty, because code remove files inside them at the end)
| Split `scenario.py` | 490 lines; extract SUMO runner, output parser, and agent loop into separate files | (I already have the section written in overleaf)
| Add `{network}` dimension to `data/DUE/` | Before a third network is benchmarked | (there is not gonna be a third network)