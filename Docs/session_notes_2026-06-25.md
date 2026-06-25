# Session Notes — 2026-06-25

## What we did

### 1. Documentation audit
Created a full documentation audit at `Docs/audits/documentation_and_comments_audit.md`.
Overall debt score: 61/100 (high risk). Top findings:
- `agents/agent.py` — no paper reference, no formulas, no notation (score 85/100 critical)
- `README.md` — describes abandoned DQN phase, not current BM system (score 90/100 critical)
- `DUE_convergence/rgap.py` — R-gap formula missing (score 75/100)
- Silent bug in `mlflow_tracking/analysis.py:26` — `_log_params` referenced but never called (missing `()`)

---

### 2. Module docstrings improved (file by file)

Every file below had its module docstring rewritten. Key decisions made during the session are noted.

#### `src/main.py`
- Added execution order (0–7), entry points, run mode documentation.
- Clarified that duaIterate is run as a DUE benchmark step inside `run_due_convergence_checks`, not as a co-trained algorithm.

#### `src/experiment.py`
- Listed all 8 data streams (aggregated, vehroute, trips_info, fcd, edgedata, actions, rewards, BM_results).
- Named the two-phase pattern: per-episode accumulate → end-of-run flush.

#### `src/utils/get_avg_speed.py`
- Explained WHY warm-up is excluded: few vehicles during warm-up → higher speed → avg_speed overestimated → calibration thinks network is emptier than it is. (User wrote this reasoning, better than the original.)
- Noted the `meanSpeed > 0` filter (SUMO emits -1 as sentinel at last timestep).

#### `src/utils/get_free_flow_speed.py`
- Stated role: denominator of `congestion_ratio = avg_speed / free_flow_speed`.
- Noted Sioux Falls uses uniform 13.89 m/s, so result is trivially constant — general formula kept for network portability.
- Clarified "behavior heterogeneity" means: experiment studies route-choice, not speed-limit effects.

#### `src/utils/get_total_length_network.py`
- Stated role in initial guess formula: `demand = heuristic_veh_km_hour × total_length_km × hours`.

#### `src/utils/network.py`
- Explained `min_distance = 2 × median_edge_length` heuristic and why (filter trivially short trips).

#### `src/utils/od_routes.py`
- Added input/output shape example (nested dict → tidy row-per-edge format).

#### `src/utils/sumo_xml.py`
- Explained the optional-arguments design of `write_sumo_conf` (avoids multiple static config files).
- Named the two callers and what each passes.

#### `src/tools/modify_speed_lanes.py`
- Added speed distribution table (20/30/50/60 km/h with weights).
- Stated WHY: introduce speed heterogeneity into Sioux Falls (uniform at 13.89 m/s by default).
- Added "run once, then commit" note.

#### `src/tools/netconvert.py`
- Documented every flag group with one-line explanations.
- Explained traffic light removal is an intentional experiment design decision.

#### `src/tools/network_stats_edges_len.py`
- Added hardcoded-path warning (both NETWORK_PATH and output path inside function body need manual update).

#### `src/tools/network_stats.py`
- Listed all four metrics (nodes, edges, lanes, connections) with their XPath filters.
- Noted connection filter (`starts-with E or -E`) is Sioux Falls-specific.

#### `src/stopping_rule/stopping_rule.py`
- Added L1 norm formula: `mean(||p_t - p_{t-1}||_1)`.
- Documented WHY mean not max (MARL always has at least one agent updating; max was too restrictive).
- Documented WHY L1 not KL-divergence (KL requires smoothing for zero probabilities on unvisited routes).
- Documented warm-up+1 offset: first learning episode still uses uniform policy carried from warm-up.

#### `src/simulation/environment.py`
- Documented no-TraCI design: file-based route injection is significantly faster (avoids per-timestep Python↔SUMO socket overhead). Trade-off: cannot change routes mid-episode.

#### `src/simulation/scenario.py`
- Named the two exposed data structures (`self.agents`, `self.od_routes`) with their shapes.
- Documented 4 construction steps with non-obvious details:
  - Agents: OD restriction to k most frequent, departure times sorted ascending (SUMO requires declaration order).
  - Routes: `random_factor=1.0` for first call (true shortest path), then perturbed calls for alternatives.
  - The meandata XML instructs SUMO to collect `entered` and `density` per edge per time interval.

#### `src/parsing/parser.py`
- Explained the three extraction modes and why `extract_fcd_flat` exists separately (FCD has nested timestep > vehicle structure).
- Explained the config.yaml separation (XPath queries defined in YAML, not hardcoded).

#### `src/parsing/sumo_outputs.py`
- Table of all 5 parsers with source file and key columns returned.
- Noted `fcd` and `edgedata` do not use the YAML-driven loop — `fcd` YAML entries may be unused/legacy (worth verifying).

#### `src/mlflow_tracking/analysis.py`
- Two run types: simulation (BM training loop) / analysis (R scripts). User improved formatting by putting description before file reference.
- `source_run_id` tag is how analysis runs are linked to simulation runs.

#### `src/mlflow_tracking/simulation.py`
- Fixed copy-paste error ("analysis phase" → "simulation phase").
- Listed all logged parameters, metrics (time series vs scalar), and artifacts explicitly.

#### `src/mlflow_tracking/utils.py`
- Explained why explicit MLflow setup is needed (default scatters files to cwd).
- Named the two storage locations: SQLite backend (metadata) + filesystem artifact store (files).

#### `src/mlflow_tracking/load_mlflow_results.py`
- Documented 3-step workflow: batch experiments → `load_artifact_across_runs()` → R analysis.
- Absorbed the floating two-API string literal (mlflow high-level vs MlflowClient low-level) into the module docstring.

#### `src/DUE_convergence/aggregation.py`
- Named the two output tables with their full index key (origin, destination, time_interval, path, episode=k).
- User added "for each unique combination of the index" and `episode (k)` annotation — both good improvements.
- Connected to R-gap as downstream consumer.

#### `src/DUE_convergence/duaiterate.py`
- Documented duaIterate as SUMO's built-in DUE solver (not just a "benchmark tool").
- Key rationale: duaIterate is a **sanity check** — if it also fails to reach low R-gap, the cause is the network/demand configuration, not the learning algorithm.
- User improved: "Only the last iteration is used… (we compare the converged state of both algorithms, not their learning trajectories)."
- Added References section (SUMO duaIterate docs URL).
- Grouped functions: run pipeline, mirror BM data structures, auxiliary metric, cleanup.

#### `src/DUE_convergence/DUE_convergence.py`
- Named entry point (`run_due_convergence_checks`).
- Listed the three tables required by R-gap with full index keys decoded inline.
- BM → trajectory across all episodes; duaIterate → last iteration only (sanity check).
- Decision: no references here; references belong in the files where functions are implemented.

#### `src/DUE_convergence/rgap.py`
- Added R-gap formula with all variables defined.
- Listed all 4 variants (rgap, refined_rgap, rgap_by_od, refined_rgap_by_od) with their grouping keys.
- Added References section (Wardrop 1952 + user's paper).

#### `src/DUE_convergence/tdsp.py`
- Opening: TDSP required by R-gap to measure how much time drivers lose by not taking the cheapest route. Costs are time-dependent (same edge can be congested at one interval, free-flowing at another).
- Documented 8-step pipeline clearly.
- Imputation rule expanded: density > threshold → ffill; otherwise → free-flow travel time.
- User improved "derive travel times on the edges each driver traversed" (clearer than "per-agent, per-edge travel times").
- User improved step 2: "compute mean travel time per (episode, edge, time_interval), then reindex".
- References: SUMO duarouter docs for TDSP.

#### `src/demand_calibration/demand_calibration.py`
- Removed "oracle" (jargon). Changed to: "Runs a single SUMO episode to measure the congestion level produced by a given number of vehicles."
- Explained why random trips (actual agent OD pairs not yet defined at calibration time).
- Added congestion ratio scale.

#### `src/demand_calibration/utils.py`
- Best docstring of the session (user's words). Key elements:
  - Context: calibration before MARL training.
  - Congestion metric formula + scale.
  - Two-phase procedure with formulas for both initial guess and update rule.
  - Clip [0.6, 1.4] explained (prevent overshooting).
  - Stopping condition: `|error| < tolerance_demand_calibration`.

#### `src/config/paths.py`
- Single source of truth design (all paths from BASE_DIR).
- Listed 9 sections.
- Explained DuePaths factory pattern (avoids duplicating structure for BM vs duaIterate).

#### `src/config/config.yaml`
- Explained separation-of-concerns design (XPath in YAML → one place to update if SUMO schema changes).
- Named consumer (`parsing/sumo_outputs.py`).
- Flagged that `fcd` and `edgedata` sections may be unused/legacy.

#### `src/config/config.py`
- Named both exported objects (`config` singleton, `RunMode` enum).
- Listed all 10 hyperparameter groups.
- Documented derived fields (`end_time`, `warm_up` computed in `__post_init__`).
- Explained `sys.argv[1]` loading pattern.

#### `src/analysis/sumo_edge_analysis.py`
- Named two visualization modes (aggregated / per-interval).
- Documented breakpoint lead (-2s) as a SUMO-GUI gotcha.
- Aggregation rules prominently: `entered` → sum; `density` → mean (with full intuition for density).
- Noted density verified in sumo-gui (not monotonically increasing confirms it's an average).

#### `src/agents/factory.py`
- Named the design pattern: batch operations over agent fleet.
- Stated return type of `select_actions` (`{agent_id: route_idx}`).
- Noted unique seed assignment per agent for reproducibility.

#### `src/agents/agent.py` (most important file)
- Paper reference: Wei et al. (2014), DOI 10.1155/2014/646548.
- Full notation table: β, γ, ET, PT_r, stimulus.
- ET and PT formulas with decay weights.
- Critical asymmetry: ET excludes episode T (expectation formed before departing); PT includes episode T.
- Two warm-up conditions and WHY (division by zero in stimulus normalisation).
- Agent lifecycle (init → select_action → update).

---

### 3. Code change discussed (not necessarily applied)

**`agents/agent.py` — `_compute_perceived_travel_times`:**
- The loop + if/else for NaN guard is dead code: warm-up conditions guarantee all routes visited before this function is ever called, so `denominator[k]` is always > 0.
- Can simplify to: `self.perceived_travel_times = numerator / denominator`
- Delete the `if denominator[k] == 0` block and "Unused routes have PT = None" comment.

---

### 4. Patterns established during session

- **Docstring opening**: never start with "This file...", "Purpose of...", "It contains...". Start with what the module IS or DOES.
- **Why before what**: explain the reason for a design decision before describing the mechanism.
- **Formulas belong in the file where the computation lives**, not in orchestrating files.
- **References belong in implementation files**, not orchestrators.
- **Informal voice** ("wanna", "I prefer to let it here", "incorpores") removed throughout.
- **"One-off tool"** prefix used consistently for files in `src/tools/`.
- User consistently improved descriptions by making causal chains explicit (e.g., warm-up exclusion, density aggregation rationale).

---

### 5. Still pending

- Verify whether `fcd` and `edgedata` sections in `config/config.yaml` are actually consumed anywhere.
- Fix the silent bug in `mlflow_tracking/analysis.py:26` (`_log_params` not called).
- `README.md` rewrite (still describes abandoned DQN phase).
- Function-level docstrings for `_compute_stimulus`, `_reinforce_chosen`, `_penalise_chosen` in `agents/agent.py`.
- Apply the `numerator / denominator` simplification in `_compute_perceived_travel_times`.
