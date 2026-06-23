# Complexity Audit

**Date:** 2026-06-17  
**Scope:** All Python source files under `src/`  
**Tool:** AST-based cyclomatic complexity (branches + loops + bool-ops + 1)
**Meaning** "I parsed your code's syntax tree and counted decision points (ifs, loops, and/or operators, etc.) to estimate how many independent execution paths this function contains."

| Complexity | Interpretation |
|------------|---------------|
| 1–5 | Simple |
| 6–10 | Moderate |
| 11–20 | Complex |
| >20 | Consider refactoring |
| >30 | Often difficult to maintain |

Higher complexity usually means:

More code paths (A code path is simply a possible route that execution can take through your program)
More tests needed
Harder debugging
Greater chance of hidden bugs

---

## Summary Table

| # | Category | Location | Issue | Importance |
|---|----------|----------|-------|------------|
| CC1 | Cyclomatic | `scenario.py:110` | `compute_k_routes` CC=11 — only function exceeding the 10 threshold | 8/10 |
| CC2 | Cognitive | `DUE_convergence/utils.py:96` | `compute_travel_time_links_t_k` — 223 lines, 5 distinct phases in one body | 9/10 |
| CC3 | Cognitive | `DUE_convergence/DUE_convergence.py:158` | `check_DUE_convergence_duaIterate` — 132 lines, 15 numbered steps | 8/10 |
| CC4 | Cognitive | `agents/agent.py:120` | `update_probabilities` — CC=6, two different mathematical algorithms in one if/else | 6/10 |
| CC5 | Lines | `DUE_convergence/utils.py` | 958-line file, four unrelated responsibilities | 9/10 |
| CC6 | Lines | `scenario.py` | 466-line file, `Scenario` class with five unrelated responsibilities | 7/10 |
| CC7 | Lines | `analysis/sumo_edge_analysis.py` | 404-line file — entire visualization pipeline in one module | 6/10 |
| CC8 | Coupling | `DUE_convergence/utils.py:1` | Imports `parse_*` from `experiment.py` — analysis layer depending on orchestration layer | 9/10 |
| CC9 | Coupling | `config.config` / `paths` | Afferent coupling = 13 and 11 respectively — any change propagates to every module | 7/10 |
| CC10 | Cohesion | `experiment.py` | Three concerns mixed: XML parsing, data wrangling, orchestration helpers | 6/10 |
| CC11 | Cognitive | `DUE_convergence/utils.py:269` | `get_max_value` nested function `process_df` has CC=6 inside an already-complex parent | 5/10 |
| CC12 | Cognitive | `main.py:34` | `main` CC=6, directly orchestrates all 9 pipeline stages without intermediate grouping | 5/10 |

---

## CC1 — Cyclomatic Complexity: `compute_k_routes` CC=11

**Importance: 8/10**  
**File:** `src/scenario.py:110–167` (58 lines)

### Measured CC = 11

Decision points contributing:
```
+1  base
+1  with tempfile.TemporaryDirectory
+1  if not best_routes: return
+1  (implied: routes_per_od list comprehension)
+1  for seed in seeds
+1  if all(len(rlist) >= k for rlist in routes_per_od): break  ← also +1 for 'all'
+1  if not new_routes: continue
+1  for i, route in enumerate(new_routes)
+1  if route not in routes_per_od[i]
+1  if len(routes_per_od[i]) < k
+1  (comprehension in 'all()')
─────
11
```

### Why it's hard to follow

The function mixes three concerns: managing a temp directory, running duarouter repeatedly, and deduplicating routes. The early-exit `if not best_routes` is inside the `with` block, which means it exits before the cleanup at line 161 (`UNDESIRED_ROUTE_FILE.unlink()`). If `best_routes` is empty, the file is never cleaned up.

### Fix

Extract the route-deduplication accumulation into a helper, separate the duarouter-loop body:

```python
def compute_k_routes(self, seeds, k=config.n_routes_per_OD, ...):
    with tempfile.TemporaryDirectory() as tmpdir:
        trips_file = os.path.join(tmpdir, "trips.xml")
        routes_file = os.path.join(tmpdir, "routes.xml")
        self._write_trip(trips_file)

        best_routes = self._run_duarouter(trips_file, routes_file, random_factor=1.0, seed=config.seed)
        if not best_routes:
            return {}

        routes_per_od = [[r] for r in best_routes]
        self._fill_alternative_routes(routes_per_od, trips_file, routes_file, seeds, k)

    UNDESIRED_ROUTE_FILE.unlink(missing_ok=True)   # safe even if not created
    return dict(zip(self.unique_ods, routes_per_od))


def _fill_alternative_routes(self, routes_per_od, trips_file, routes_file, seeds, k):
    for seed in seeds:
        if all(len(rlist) >= k for rlist in routes_per_od):
            break
        new_routes = self._run_duarouter(trips_file, routes_file, random_factor=config.random_factor, seed=seed)
        if not new_routes:
            continue
        for i, route in enumerate(new_routes):
            if route not in routes_per_od[i] and len(routes_per_od[i]) < k:
                routes_per_od[i].append(route)
```

New CC of `compute_k_routes`: **4**. New CC of `_fill_alternative_routes`: **6**.

---

## CC2 — Cognitive Complexity: `compute_travel_time_links_t_k` — 223 lines

**Importance: 9/10**  
**File:** `src/DUE_convergence/utils.py:96–318`

This is the most cognitively complex unit in the codebase. It has **five distinct phases** that each warrant their own function, but are all fused into one 223-line body:

| Phase | Lines | Responsibility |
|-------|-------|----------------|
| 1 | 133–187 | Load inputs, compute per-edge travel times |
| 2 | 189–207 | Expand to full (episode × edge × interval) grid |
| 3 | 209–241 | Analyse and persist missingness patterns |
| 4 | 243–279 | Merge density data, forward-fill missing values |
| 5 | 310–318 | Fill remaining NaNs with free-flow travel times |

Phase 3 (missingness analysis) is a diagnostic concern that could be disabled independently — yet it is embedded in the middle of the computation with side effects (parquet writes).

### Fix

```python
def compute_travel_time_links_t_k(
    time_interval, network, threshold_density, output_file,
    agents_od_file, vehroute_file, edgedata_file,
    missingness: MissingnessOutputPaths,   # see CC R5 in readability audit
):
    all_edges = _load_network_edges(network)
    df_edges = _compute_edge_travel_times(vehroute_file, agents_od_file, time_interval)
    avg_tt = _build_full_grid(df_edges, all_edges)
    _save_missingness_report(avg_tt, missingness)
    df_filled = _fill_missing_travel_times(avg_tt, edgedata_file, all_edges, threshold_density)
    df_filled.to_parquet(output_file)


def _load_network_edges(network) -> set:
    tree = etree.parse(network)
    return set(tree.xpath("//edge[not(@function='internal')]/@id"))


def _compute_edge_travel_times(vehroute_file, agents_od_file, time_interval) -> pd.DataFrame:
    df_edges = pd.read_parquet(vehroute_file)
    df_edges.rename(columns={"vehicle_id": "agent_id"}, inplace=True)
    df_agents_od = pd.read_parquet(agents_od_file)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)
    df_edges = df_edges.merge(df_agents_od[["agent_id", "departure_time"]], on="agent_id", how="left")
    df_edges = df_edges.sort_values(["episode", "agent_id", "exit_times"])
    df_edges["entry_time"] = df_edges.groupby(["episode", "agent_id"])["exit_times"].shift(1)
    df_edges["entry_time"] = df_edges["entry_time"].fillna(df_edges["departure_time"])
    df_edges = df_edges.drop("departure_time", axis=1)
    df_edges["travel_time"] = df_edges["exit_times"] - df_edges["entry_time"]
    assert (df_edges["travel_time"] >= 0).all()
    max_interval = pd.read_parquet(TIMES_INTERVAL)["interval"].max()
    df_edges["time_interval"] = (df_edges["entry_time"] // time_interval).astype(int).clip(upper=max_interval)
    return df_edges


def _build_full_grid(df_edges, all_edges) -> pd.DataFrame:
    avg_tt = df_edges.groupby(["episode", "edge", "time_interval"])["travel_time"].mean()
    full_index = pd.MultiIndex.from_product(
        [df_edges["episode"].unique(), all_edges, df_edges["time_interval"].unique()],
        names=["episode", "edge", "time_interval"],
    )
    return avg_tt.reindex(full_index).reset_index()


def _save_missingness_report(avg_tt: pd.DataFrame, paths: MissingnessOutputPaths):
    df = avg_tt.copy()
    df["col_missing"] = df["travel_time"].isna().astype(int)
    with open(paths.report, "w") as f:
        f.write(f"Proportion missing: {df['col_missing'].mean():.4f}\n")
        f.write(f"Total missing: {df['col_missing'].sum()}\n")
    df.groupby("time_interval")["col_missing"].sum().reset_index().to_parquet(paths.by_interval, index=False)
    df.groupby("edge")["col_missing"].sum().reset_index().to_parquet(paths.by_edge, index=False)
    df.groupby("episode")["col_missing"].sum().reset_index().to_parquet(paths.by_episode, index=False)


def _fill_missing_travel_times(avg_tt, edgedata_file, all_edges, threshold_density) -> pd.DataFrame:
    df_density = pd.read_parquet(edgedata_file).drop(columns=["entered"])
    df_density.rename(columns={"interval": "time_interval"}, inplace=True)
    full_index = pd.MultiIndex.from_product(
        [df_density["episode"].unique(), df_density["time_interval"].unique(), all_edges],
        names=["episode", "time_interval", "edge"],
    )
    df_full = df_density.set_index(["episode", "time_interval", "edge"]).reindex(full_index).reset_index().fillna(0)
    df = avg_tt.merge(df_full, on=["episode", "time_interval", "edge"], how="left")
    df = df.sort_values(["episode", "edge", "time_interval"])
    df["ffill"] = df.groupby(["episode", "edge"])["travel_time"].ffill()
    df = df.astype({"episode": "Int64", "edge": str, "time_interval": "Int64",
                    "travel_time": float, "density": float, "ffill": float})
    mask_ffill = df["travel_time"].isna() & (df["density"] > threshold_density)
    df.loc[mask_ffill, "travel_time"] = df.loc[mask_ffill, "ffill"]
    free_flow = pd.read_parquet(FREE_FLOW_TRAVEL_TIMES)[["edge", "free_flow_travel_time"]]
    df = df.merge(free_flow, on="edge", how="left")
    mask_fft = df["travel_time"].isna()
    df.loc[mask_fft, "travel_time"] = df.loc[mask_fft, "free_flow_travel_time"]
    return df.drop(["density", "ffill", "free_flow_travel_time"], axis="columns")
```

---

## CC3 — Cognitive Complexity: `check_DUE_convergence_duaIterate` — 132 lines

**Importance: 8/10**  
**File:** `src/DUE_convergence/DUE_convergence.py:158–289`

The function lists **15 numbered steps** in a single body. Steps 1–13 are the duaIterate pipeline. Steps 14.1–14.5 are the TDSP computation. Step 15 is cleanup.

The TDSP block (steps 14.x, lines 233–272) is a verbatim copy of the same block in `check_DUE_convergence_BM` (lines 114–145). Both functions call `compute_travel_time_links_t_k`, `generate_weights_xmls`, `compute_time_dependent_shortest_paths`, `compute_cost_min_paths_odt_k`, and `delete_files_due_convergence` with different path arguments.

### Fix

Extract the shared TDSP block:

```python
def _run_tdsp_pipeline(
    time_interval, vehroute_file, edgedata_file,
    agents_od_file, missingness, cost_links, weights_dir,
    shortest_path_dir, cost_min_paths
):
    compute_travel_time_links_t_k(
        time_interval=time_interval, network=config.network,
        threshold_density=config.threshold_density, output_file=cost_links,
        agents_od_file=agents_od_file, vehroute_file=vehroute_file,
        edgedata_file=edgedata_file, missingness=missingness,
    )
    generate_weights_xmls(cost_links=cost_links, weights_dir=weights_dir)
    compute_time_dependent_shortest_paths(
        config.network, config.seed,
        weights_dir=weights_dir, shortest_path_dir=shortest_path_dir,
    )
    compute_cost_min_paths_odt_k(
        time_interval=time_interval,
        cost_min_paths=cost_min_paths,
        shortest_path_dir=shortest_path_dir,
    )
    delete_files_due_convergence(weights_dir=weights_dir, shortest_paths_dir=shortest_path_dir)
```

Then both callers become:

```python
# check_DUE_convergence_BM — step 4 block becomes:
_run_tdsp_pipeline(
    time_interval, VEHROUTE_PARQUET, EDGEDATA_PARQUET, AGENTS_OD,
    MissingnessOutputPaths(MISSINGNESS_REPORT, MISSINGNESS_INT, MISSINGNESS_EDGE, MISSINGNESS_EPISODE),
    COST_LINKS, WEIGHTS_DIR, SHORTEST_PATHS_DIR, COST_MIN_PATHS,
)

# check_DUE_convergence_duaIterate — step 14 block becomes:
_run_tdsp_pipeline(
    time_interval, VEHROUTE_DUEITERATE_PROCESSED, EDGEDATA_DUEITERATE_PROCESSED, AGENTS_OD,
    MissingnessOutputPaths(MISSINGNESS_DUEITERATE_REPORT, MISSINGNESS_DUEITERATE_INT,
                           MISSINGNESS_DUEITERATE_EDGE, MISSINGNESS_DUEITERATE_EPISODE),
    COST_LINKS_DUEITERATE, WEIGHTS_DIR_DUEITERATE, SHORTEST_PATHS_DIR_DUEITERATE,
    COST_MIN_PATHS_DUEITERATE,
)
```

`check_DUE_convergence_duaIterate` shrinks from 132 lines to ~70 lines.

---

## CC4 — Cognitive Complexity: `update_probabilities` — two algorithms in one if/else

**Importance: 6/10**  
**File:** `src/agents/agent.py:120–144` (CC=6)

```python
def update_probabilities(self, chosen, stimulus):
    p = self.p.copy()
    if stimulus >= 0:   # ← Algorithm A: "good route"
        p[chosen] += (1 - p[chosen]) * self.beta * stimulus
        for k in range(self.n_routes):
            if k != chosen:
                p[k] -= p[k] * self.beta * stimulus
    else:               # ← Algorithm B: "bad route" (different formula entirely)
        p[chosen] += p[chosen] * self.beta * stimulus
        for k in range(self.n_routes):
            if k != chosen:
                p[k] = (p[k] - p[k] * p[chosen] * self.beta * stimulus) / (
                    1 - p[chosen]
                )
    self.p = p / np.sum(p)
```

The two branches implement mathematically distinct update rules. A reader must parse both to understand either.

### Fix

```python
def update_probabilities(self, chosen, stimulus):
    p = self.p.copy()
    if stimulus >= 0:
        p = self._reinforce_chosen(p, chosen, stimulus)
    else:
        p = self._penalise_chosen(p, chosen, stimulus)
    self.p = p / np.sum(p)

def _reinforce_chosen(self, p, chosen, stimulus):
    p[chosen] += (1 - p[chosen]) * self.beta * stimulus
    for k in range(self.n_routes):
        if k != chosen:
            p[k] -= p[k] * self.beta * stimulus
    return p

def _penalise_chosen(self, p, chosen, stimulus):
    p[chosen] += p[chosen] * self.beta * stimulus
    for k in range(self.n_routes):
        if k != chosen:
            p[k] = (p[k] - p[k] * p[chosen] * self.beta * stimulus) / (1 - p[chosen])
    return p
```

---

## CC5 — Lines of Code: `DUE_convergence/utils.py` — 958 lines, four responsibilities

**Importance: 9/10**  
**File:** `src/DUE_convergence/utils.py`

The file currently contains four unrelated logical groups:

| Lines | Logical Group | Candidate Module |
|-------|---------------|-----------------|
| 24–93 | Flow and path travel time aggregation | `DUE_convergence/aggregation.py` |
| 96–400 | Link travel time + TDSP generation | `DUE_convergence/tdsp.py` |
| 414–638 | Rgap computation + demand helpers | `DUE_convergence/rgap.py` |
| 641–958 | duaIterate pipeline (run, parse, process) | `DUE_convergence/duaiterate.py` |

The four groups do not share any private state and only exchange data via parquet files and path arguments. They are already loosely coupled — the split is purely mechanical.

### Proposed module layout

```
src/DUE_convergence/
├── __init__.py
├── DUE_convergence.py       # orchestration only (stays as-is, smaller)
├── aggregation.py           # compute_flows_odtp_k, compute_travel_time_paths_odtp_k
├── tdsp.py                  # compute_travel_time_links_t_k, generate_weights_xmls,
│                            # compute_time_dependent_shortest_paths, compute_cost_min_paths_odt_k
├── rgap.py                  # compute_rgap_*, compute_rgap_and_refined_rgap,
│                            # generate_demand_odt, generate_time_intervals_table,
│                            # generate_trips_odt_file
└── duaiterate.py            # all generate_*/process_*/call_*/run_simulation_* for duaIterate
```

`DUE_convergence.py` would import from all four and remain the only public API.

---

## CC6 — Lines of Code: `scenario.py` — 466 lines, `Scenario` does five things

**Importance: 7/10**  
**File:** `src/scenario.py`

The `Scenario` class mixes five distinct concerns:

| Methods | Responsibility |
|---------|----------------|
| `generate_agents`, `generate_od_for_agents`, `generate_random_trips_agents`, `parse_od_agents`, `restrict_od_space`, `sample_od_space`, `generate_departure_times` | Agent + OD generation |
| `compute_k_routes`, `_run_duarouter`, `_write_trip`, `_parse_route`, `load_or_compute_routes`, `reconstruct_od_routes` | Route computation |
| `generate_conf`, `generate_meandata_file` | SUMO config file writing |
| `_generate_free_flow_tt_links`, `_compute_median_free_flow_travel_time`, `_set_time_interval` | Network analysis |
| `save_scenario_data`, `_save_od_routes`, `_save_agents`, `write_od_matrix`, `process_od_routes` | Data persistence |

### Recommended split

Route computation is the most self-contained group and the heaviest (CC=11). Extract it:

```python
# src/routing/k_routes.py
class KRoutesComputer:
    def __init__(self, network, unique_ods, config):
        self.network = network
        self.unique_ods = unique_ods
        self.config = config

    def compute(self, seeds) -> dict:
        """Returns od_routes dict."""
        ...
```

`Scenario.__init__` delegates:
```python
self.od_routes = KRoutesComputer(MAP, self.unique_ods, config).compute(seeds)
```

This alone removes ~60 lines from `Scenario` and brings `compute_k_routes` CC under test.

---

## CC7 — Lines of Code: `analysis/sumo_edge_analysis.py` — 404 lines

**Importance: 6/10**  
**File:** `src/analysis/sumo_edge_analysis.py`

The file is a single-pipeline visualization module. It is already well-structured (one public entry point `run_edge_visualization`, each sub-step a private helper), but a nested function (`process_df` inside `get_max_value`) adds unnecessary cognitive depth.

`process_df` reads a dimension table and aggregates by metric and aggregation mode. It is called twice in the same parent (`get_max_value`). Lifting it to module level makes both call sites clearer:

```python
# Before (nested, lines 277-301):
def get_max_value(metric, edgedata_dueIterate_file, edgedata_BM_file, aggregated, period=900):
    def process_df(df, aggregated):   # ← nested
        ...
    df_due = ...
    max_value_dueIterate = process_df(df_due, aggregated)
    ...

# After (module-level private):
def _aggregate_edgedata(df: pd.DataFrame, metric: str, aggregated: bool, period: int) -> float:
    times_interval = pd.read_parquet(TIMES_INTERVAL)
    df = df.copy().merge(times_interval, on="interval")
    df[metric] = df[metric].astype(float)
    if aggregated:
        agg_fn = "sum" if metric == "entered" else "mean"
        return df.groupby("edge")[metric].agg(agg_fn).max()
    else:
        df["period"] = df["start_time"] // period
        agg_fn = "sum" if metric == "entered" else "mean"
        return df.groupby(["edge", "period"])[metric].agg(agg_fn).max()

def get_max_value(metric, edgedata_dueIterate_file, edgedata_BM_file, aggregated, period=900):
    max_due = _aggregate_edgedata(pd.read_parquet(edgedata_dueIterate_file), metric, aggregated, period)
    df_bm = pd.read_parquet(edgedata_BM_file)
    last_ep = df_bm["episode"].max()
    max_bm = _aggregate_edgedata(df_bm[df_bm["episode"] == last_ep], metric, aggregated, period)
    return max(max_due, max_bm)
```

---

## CC8 — Coupling: `DUE_convergence/utils.py` imports from `experiment.py`

**Importance: 9/10**  
**File:** `src/DUE_convergence/utils.py:1`

```python
from experiment import parse_trips_info, parse_vehroute, parse_edgedata
```

**Architecture violation.** `experiment.py` is the training-loop orchestration layer. `DUE_convergence/utils.py` is an analysis layer. The analysis layer should not depend on the orchestration layer — this creates a circular dependency risk and prevents `DUE_convergence/` from being tested or run independently.

The root cause is that `parse_trips_info`, `parse_vehroute`, and `parse_edgedata` live in `experiment.py` rather than in the `parsing/` package where they belong.

### Fix

Move the three parse functions to `src/parsing/`:

```python
# src/parsing/sumo_outputs.py  (new file)
from lxml import etree
import yaml
from paths import YAML_CONF

with open(YAML_CONF) as f:
    _config = yaml.safe_load(f)

def parse_trips_info(episode, trips_info_path): ...   # move from experiment.py:174
def parse_vehroute(episode, vehroute_path): ...       # move from experiment.py:146
def parse_edgedata(episode, edgedata_path): ...       # move from experiment.py:213
def parse_aggregated_data(episode): ...               # move from experiment.py:136
def parse_fcd(episode): ...                           # move from experiment.py:206
```

Then update imports:

```python
# experiment.py — replace local definitions with:
from parsing.sumo_outputs import (
    parse_trips_info, parse_vehroute, parse_edgedata,
    parse_aggregated_data, parse_fcd,
)

# DUE_convergence/utils.py — replace:
from experiment import parse_trips_info, parse_vehroute, parse_edgedata
# with:
from parsing.sumo_outputs import parse_trips_info, parse_vehroute, parse_edgedata
```

Dependency diagram after fix:

```
main.py
  └── experiment.py
        └── parsing/sumo_outputs.py  ← both layers use this
  └── DUE_convergence/
        └── parsing/sumo_outputs.py  ← no longer touches experiment.py
```

---

## CC9 — Coupling: `config.config` and `paths` as universal dependencies

**Importance: 7/10**

| Module | Afferent coupling (importers) |
|--------|-------------------------------|
| `config.config` | 13 |
| `paths` | 11 |

Both modules are imported by nearly every other module. This is partially by design (they are deliberately global), but it means:

1. **`config/config.py`** — `Config.__post_init__` calls `get_edges_lengths_program`, which parses the network XML. This means `import config` at module load time parses a file from disk. Any module that imports `config` at import time (e.g., as a default argument: `k=config.n_routes_per_OD` at `scenario.py:111`) will trigger file I/O at import time.

```python
# scenario.py:111 — triggers disk I/O at class definition time
def compute_k_routes(self, seeds, k=config.n_routes_per_OD, ...):
```

### Fix

Replace default-argument `config` references with `None` sentinel:

```python
def compute_k_routes(self, seeds, k=None, max_attempts=None, random_factor=None):
    k = k if k is not None else config.n_routes_per_OD
    max_attempts = max_attempts if max_attempts is not None else config.max_attempts
    random_factor = random_factor if random_factor is not None else config.random_factor
    ...
```

This allows test code to construct a `Scenario` without triggering XML parsing just by importing the module.

2. **`paths.py`** — `DUE_convergence/DUE_convergence.py` imports **41 names** from `paths`. Any restructuring of the output directory layout requires editing `paths.py` AND updating all importers. Consider grouping related paths into namespaced dataclasses:

```python
# paths.py — group DUE-specific paths
@dataclass(frozen=True)
class _DueBMPaths:
    flows_paths: Path = DUE_DATA_BM / "flows_paths_odtp_k.parquet"
    cost_paths: Path = DUE_DATA_BM / "costs_paths_odtp_k.parquet"
    ...

DUE_BM = _DueBMPaths()
```

---

## CC10 — Cohesion: `experiment.py` has three concerns

**Importance: 6/10**  
**File:** `src/experiment.py` (306 lines)

The file mixes:

| Lines | Concern |
|-------|---------|
| 136–234 | XML parsing (`parse_vehroute`, `parse_trips_info`, `parse_edgedata`, `parse_fcd`, `parse_aggregated_data`) |
| 48–123 | Data wrangling and persistence (`prepare_data`, `accumulate_results`, `save_processed_data`) |
| 237–266 | BM-specific data extraction (`prepare_actions`, `prepare_rewards`, `prepare_bm_data`) |
| 268–307 | Run-mode helpers (`log_run_mode`, `run_final_simulation`) |

The `accumulate_results` function (lines 69–98) contains a 15-line docstring that explains `getattr` — a Python built-in — because the function is non-obvious. This is a cohesion symptom: if you need to document the Python standard library inside a domain function, the function is doing something the domain does not own.

### Fix

Addressed by CC8 (move parse functions to `parsing/sumo_outputs.py`). The remaining `experiment.py` would contain only data wrangling and persistence — a coherent responsibility.

---

## CC11 — Cognitive: `get_max_value` nested `process_df` CC=6 inside CC=6 parent

**Importance: 5/10**  
**File:** `src/analysis/sumo_edge_analysis.py:269–315`

Covered in CC7. The nested function creates three levels of nesting for readers: module scope → `get_max_value` → `process_df` → `if aggregated` → `if metric ==`. Lifting `process_df` to module level reduces maximum nesting by one level.

---

## CC12 — Cognitive: `main` function CC=6 with nine unsequenced stages

**Importance: 5/10**  
**File:** `src/main.py:34–167` (133 lines)

`main()` directly orchestrates all nine pipeline stages inline. CC=6 arises from: `for episode in range`, `if current_episode in`, `if mean_policy_change`, `if should_stop`, `if config.last_episode_gui_BM`, plus one boolean-and in the episode loop.

The stages are already well-commented (`# 0. DEMAND CALIBRATION`, `# 1. CREATE SCENARIO`, etc.) but are all in one function. The episode training loop (lines 86–143) could be extracted:

```pythonCC9 — Coupling: `config.config` and `paths` as universal dependencies
def _run_training_loop(env, agents, scen):
    results = {k: [] for k in ("aggregated", "vehroute", "trips_info",
                               "fcd", "edgedata", "actions", "rewards", "BM_results")}
    policies_history = []
    policy_change_history = []
    no_change_count = 0

    for episode in range(1, config.max_episodes + 1):
        print(f"\n--- Episode {episode} ---")
        actions = select_actions(agents)
        env.run_episode(actions, episode)
        rewards = env.get_rewards()
        current_policies = create_policies_dict(agents)
        policies_history.append(current_policies)CC9 — Coupling: `config.config` and `paths` as universal dependencies
        update_agents(actions=actions, agents=agents,
                      episode=episode, rewards=rewards, warm_up=config.warm_up)
        result = prepare_data(episode, actions, rewards, agents)
        accumulate_results(results, result)
        should_stop, no_change_count, mean_policy_change = check_convergence(
            policies_history=policies_history, episode=episode, no_change_count=no_change_count)
        if mean_policy_change:
            policy_change_history.append({"episode": episode, "mean_policy_change": mean_policy_change})
        if should_stop:
            break

    return results, policy_change_history
```

`main()` then becomes ~30 lines of stage orchestration with CC ≤ 3.

---

## Coupling Matrix

```
Module                          Afferent  Efferent  Instability*
─────────────────────────────── ─────────────────── ────────────
config/config.py                    13        1       0.07 (stable)
paths.py                            11        1       0.08 (stable)
experiment.py                        2        3       0.60 (unstable)
DUE_convergence/utils.py             1        5       0.83 (unstable)
DUE_convergence/DUE_convergence.py   1        3       0.75 (unstable)
scenario.py                          1        4       0.80 (unstable)
MLflow/mlflow_utils.py               1        2       0.67 (unstable)
agents/agent.py                      1        1       0.50
parsing/parser.py                    1        1       0.50
environment.py                       1        2       0.67
stopping_rule/stopping_rule.py       1        1       0.50

* Instability = efferent / (afferent + efferent).  Lower = more stable.
  Ideal: stable modules (low instability) are depended on by unstable ones.
```

**Key observation:** `experiment.py` has instability 0.60 yet is imported by `DUE_convergence/utils.py` (instability 0.83). An unstable module depending on another unstable module is the highest-risk coupling in the codebase. This is the core of CC8.

---

## Refactoring Priority

| Priority | Finding | Effort | Risk |
|----------|---------|--------|------|
| 1 | CC8 — move parse functions out of `experiment.py` | Low | Low |
| 2 | CC2 — split `compute_travel_time_links_t_k` into 5 functions | Medium | Low |
| 3 | CC3 — extract `_run_tdsp_pipeline` from both DUE functions | Low | Low |
| 4 | CC5 — split `DUE_convergence/utils.py` into 4 sub-modules | Medium | Low |
| 5 | CC1 — extract `_fill_alternative_routes` from `compute_k_routes` | Low | Low |
| 6 | CC6 — extract `KRoutesComputer` from `Scenario` | Medium | Medium |
| 7 | CC4 — extract `_reinforce_chosen` / `_penalise_chosen` | Low | Low |
| 8 | CC12 — extract `_run_training_loop` from `main` | Low | Low |
| 9 | CC9 — remove import-time side effects from config defaults | Low | Medium |
| 10 | CC7 — lift `process_df` out of `get_max_value` | Trivial | Low |


## Audit Review Summary
### Implemented changes
CC1 — Cyclomatic Complexity: `compute_k_routes` CC=11
CC2 — Cognitive Complexity: `compute_travel_time_links_t_k` — 223 lines
CC3 — Cognitive Complexity: `check_DUE_convergence_duaIterate` — 132 lines
CC4 — Cognitive Complexity: `update_probabilities` — two algorithms in one if/else
CC5 — Lines of Code: `DUE_convergence/utils.py` — 958 lines, four responsibilities
CC7 — Lines of Code: `analysis/sumo_edge_analysis.py` — 404 lines
CC8 — Coupling: `DUE_convergence/utils.py` imports from `experiment.py`
CC9 — Coupling: `config.config` and `paths` as universal dependencies (only implemented the config part, the paths part I dont consider it, essential and it introduces complexity)
CC10 — Cohesion: `experiment.py` has three concerns
CC11 — Cognitive: `get_max_value` nested `process_df` CC=6 inside CC=6 parent
CC12 — Cognitive: `main` function CC=6 with nine unsequenced stages


### Rejected changes
CC6 — Lines of Code: `scenario.py` — 466 lines, `Scenario` does five things (because the proposed change is to create additional classes, and I do not want to change all that in the diagram and change everything I have written in overleaf)