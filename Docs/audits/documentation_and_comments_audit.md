# Documentation & Code Comments Audit

**Project:** Day-to-Day Route Choice with Bush-Mosteller RL in SUMO  
**Date:** 2026-06-24  
**Audited files:** All Python source files in `src/`, R scripts in `r/`, README, and Docs.

---

## Executive Summary

The codebase has a mixed documentation posture. Infrastructure paths (`paths.py`) and the DUE pipeline have genuinely good documentation, while the core algorithmic heart of the project — the Bush-Mosteller update rules, stimulus computation, the time-dependent shortest path pipeline, and the demand calibration controller — carry almost no documentation explaining the math, the assumptions, or the design decisions. Given that this is a research project where correctness of the algorithm matters more than any other property, these gaps represent the highest-risk knowledge hotspots.

**Overall Documentation Debt Score: 61 / 100** (High risk — mitigated by decent file-level docstrings, damaged by absent algorithmic documentation.)

---

## Part 1 — Findings

### 1. CODE COMMENTS

#### Strengths

- Section dividers in `main.py` (`# 1. AGENTS CHOOSE ACTIONS`, `# 2. RUN EPISODE` …) work well as structural navigation.
- Inline rationale comments are used correctly in several places, e.g.:
  - `tdsp.py:54` — explains why the first edge's entry time equals departure time.
  - `tdsp.py:136–138` — explains why forward fill is applied for high-density cells.
  - `scenario.py:384` — notes that `--max-alternatives` does not work as expected, which is a critical workaround.

#### Issues

| Severity | File | Line(s) | Problem |
|----------|------|---------|---------|
| 7 | `agents/agent.py` | 63–70 | `_compute_expected_travel_time`: The docstring example (`for i in range(1): print(i)`) explains Python range semantics, not why the history slice is `history[:-1]` (i.e., why today's travel time is excluded from the ET). The business reason is missing. |
| 6 | `agents/agent.py` | 103–106 | "Heuristic" comment for the NaN-fill of unused routes is unexplained. Why is ET the right substitute? Filling an unused route's PT with ET is a deliberate BM algorithmic choice; it should say so. |
| 5 | `experiment.py` | 85–99 | Docstring comment inside `accumulate_results` body explains how `getattr` works — this is Python literacy, not domain knowledge. The comment should be deleted. |
| 4 | `scenario.py` | 349–357 | Inline comment block inside `_write_od_matrix` shows a sample dataframe — useful once, but the surrounding code is self-explanatory. Low value. |
| 4 | `config/config.py` | 71–78 | Multi-line string used as a comment (`"""Scenario: Vehicles / km…"""`) inside the class body. This becomes an anonymous string literal at runtime (a no-op docstring). Use `#` comments or move to a real docstring. |
| 3 | `main.py` | 203–211 | Commented-out profiling code is dead code that has drifted. Either delete it or gate it behind an env variable. |
| 3 | `r/shared/plots.R` | 1–30 | `plots.R` has `quit()` on line 76 causing the rest of the file to be silently skipped. There is no comment explaining this is intentional. |
| 2 | `utils/get_free_flow_speed.py` | 10 | Hardcoded `NETWORK_PATH` points to a Koh network that is not the current network. The comment says "CONSTANTS" but the path is stale. |
| 2 | `utils/get_avg_speed.py` | 17–18 | Same issue — `SUMMARY_FILE_PATH` is a dated file path from 2026-03-26 with a timestamp in the name. |

---

### 2. FUNCTION & METHOD DOCUMENTATION

#### Issues

| Severity | File | Symbol | Problem |
|----------|------|--------|---------|
| 9 | `agents/agent.py` | `_compute_stimulus` | No docstring. This is the core BM contribution: it computes a normalised relative advantage of the chosen route vs all others. The formula, the `epsilon` purpose, and the asymmetric positive/negative branches are not documented anywhere in the code. |
| 9 | `agents/agent.py` | `_reinforce_chosen` / `_penalise_chosen` | No docstrings. These implement the actual BM probability update rule. Without a reference to the paper, a future reader cannot verify correctness. |
| 8 | `agents/agent.py` | `_compute_expected_travel_time` | Docstring describes the mechanics with a misleading example. Does not say what ET represents (exponentially weighted average of all past travel times excluding the current episode). |
| 8 | `agents/agent.py` | `_compute_perceived_travel_times` | No docstring. PT is the per-route exponentially weighted average — a distinct formula from ET, with the same decay parameter applied route-specifically. |
| 8 | `DUE_convergence/tdsp.py` | `_fill_missing_travel_times` | Function has two imputation strategies (ffill and free-flow). The threshold logic is mentioned in comments but the business rule ("density above threshold means traffic existed even if no vehicles happened to enter, so forward-fill is safe") is never stated. |
| 7 | `DUE_convergence/rgap.py` | `_compute_rgap_generic` | No docstring. The R-gap formula (`Σ f·(c−c*) / Σ d·c*`) is the convergence criterion for DUE and the central metric of the research. It has no formula, reference, or explanation. |
| 7 | `DUE_convergence/tdsp.py` | `compute_time_dependent_shortest_paths` | Single-sentence docstring; does not explain why TDSP is required (time-varying link costs mean static Dijkstra gives wrong benchmark costs). |
| 6 | `stopping_rule/stopping_rule.py` | `_compute_mean_policy_change` | Docstring explains L1 norm semantics but not why `episode > warm_up + 1` (the +1 accounts for the first learning episode where the policy is still the uniform prior). |
| 6 | `demand_calibration/demand_calibration.py` | `DemandCalibration.compute_congestion_ratio` | No docstring. Does not explain what `avg_speed / free_flow_speed` measures (V/C proxy) or why that ratio is the chosen congestion metric. |
| 6 | `demand_calibration/utils.py` | `_calibration_loop` | No docstring. The proportional update rule (`1 + k * error`) is a control-theory pattern. The choice of proportional (not PI or PD) and the manual clip to [0.6, 1.4] should be explained. |
| 5 | `simulation/scenario.py` | `_sample_od_space` | Docstring describes the format of the counter object but not why sampling is proportional to observed frequency (preservation of empirical OD distribution). |
| 5 | `simulation/scenario.py` | `compute_k_routes` | No explanation of why k routes are needed (agents need a fixed action space), why `random_factor` is used to diversify (perturbing edge weights generates alternative near-shortest paths), or why the first route uses `random_factor=1.0`. |
| 4 | `mlflow_tracking/simulation.py` | `_extract_mlflow_hyperparams` | Large block of commented-out parameters with no explanation of why they were commented out vs logged. |
| 4 | `parsing/sumo_outputs.py` | `parse_edgedata` | No docstring. Unclear why `interval` is an integer counter rather than the time-interval ID from the XML. |
| 3 | `utils/od_routes.py` | `od_routes_to_rows` | No docstring. A type hint on `od_routes` would suffice, but the data shape (nested `{(o,d): [[edge, …], …]}`) is nowhere explained. |

---

### 3. MODULE & FILE DOCUMENTATION

| Severity | File | Problem |
|----------|------|---------|
| 8 | `agents/agent.py` | Module has no docstring. This is the most important file — it should reference the BM paper, define the notation (ET, PT, stimulus, β, γ), and list the warm-up rule. |
| 7 | `stopping_rule/stopping_rule.py` | Module-level comment is a section header (`# Policy stability`) but gives no context about the convergence criterion or why L1 norm was chosen over L-inf or KL divergence. |
| 7 | `DUE_convergence/tdsp.py` | Module docstring `"""Link travel time + TDSP generation"""` is too brief. The file orchestrates a complex multi-step pipeline (edge travel times → full grid → missingness → imputation → XML weights → duarouter TDSP → cost extraction). |
| 6 | `DUE_convergence/aggregation.py` | Module docstring `"""Flow and path travel time aggregation"""` is present but does not explain what "flows" mean (number of agents choosing a given path per time interval per episode). |
| 6 | `DUE_convergence/duaiterate.py` | No module docstring. File wraps the entire duaIterate DUE benchmark pipeline (15+ steps). Its role relative to the BM pipeline is not described. |
| 6 | `demand_calibration/demand_calibration.py` | No module docstring. The class-level approach (run SUMO with random trips, measure speed ratio) is a non-obvious calibration strategy. |
| 5 | `config/config.py` | File comment `# This file stores constants, hyperparameters…` is accurate but minimal. Derived fields (`warm_up`, `time_interval`, `end_time`) and the YAML-loading mechanism deserve a sentence. |
| 4 | `simulation/environment.py` | Module docstring `"""Encapsulate the use of SUMO simulator"""` is present. It does not mention the no-TraCI design decision (file-based route injection) which is architecturally important. |
| 4 | `utils/get_free_flow_speed.py` | File-level docstring is good but contains a stale hardcoded path constant. |
| 4 | `utils/get_avg_speed.py` | Same issue — stale default path. |
| 3 | `agents/factory.py` | Comment at the top is functional (`# This file is regarding…`) but explains *what* not *why*. Acceptable length; the module is simple. |

---

### 4. CLASS DOCUMENTATION

| Severity | File | Class | Problem |
|----------|------|-------|---------|
| 9 | `agents/agent.py` | `BMAgent` | The docstring is one line: `"Bush-Mosteller reinforcement learning agent for route choice"`. No state description, no invariants, no learning lifecycle, no paper reference. |
| 7 | `demand_calibration/demand_calibration.py` | `DemandCalibration` | No class docstring. The calibration oracle role (accepts n_agents, runs SUMO, returns a speed ratio) is not described. |
| 5 | `simulation/scenario.py` | `Scenario` | Docstring exists in `__init__` but not on the class itself. The three-step auto-initialization (agents, routes, conf) is described as a bullet list inside `__init__`'s body as a string literal, not a real docstring. |
| 3 | `config/paths.py` | `DuePaths` / `DuaIteratePaths` | Both have detailed Attributes docstrings. `DuePaths` has a minor duplicate — `missingness_int` appears twice in the docstring (should be `missingness_episode` on the second occurrence). |

---

### 5. ARCHITECTURE DOCUMENTATION

| Finding | Detail |
|---------|--------|
| README is severely outdated | The README describes an in-progress DQN replication from an earlier phase. It does not describe the current BM system, the DUE convergence pipeline, or how to run the code. A developer reading it would have no idea the current state of the project. |
| `UserGuide.md` exists but unclear scope | `Docs/UserGuide.md` exists — **unable to verify its completeness** without reading it. |
| No architecture diagram | The data flow from `main.py` → SUMO XML → parsed parquet → DUE convergence → R-gap → MLflow is nowhere diagrammed. |
| No ADRs | Key design decisions (no TraCI, k=10 OD space restriction, no static Dijkstra for TDSP, ffill vs free-flow imputation strategy, proportional demand controller) have no Architecture Decision Records. |
| `config/config.yaml` not audited | XPath selectors file — **unable to verify** alignment with current SUMO output schema. |

---

### 6. DOMAIN KNOWLEDGE PRESERVATION

| Severity | Location | Gap |
|----------|---------|-----|
| 9 | `agents/agent.py` | The BM update rules, stimulus formula, and the PT/ET definitions are nowhere mapped to the Wei et al. (2014) paper they derive from. A future maintainer cannot verify the implementation matches the paper. |
| 8 | `DUE_convergence/rgap.py` | The R-gap formula is a standard traffic equilibrium metric. The numerator (`Σ f·(c−c*)`) and denominator (`Σ d·c*`) are standard but their derivation and the DUE condition they test (R-gap → 0 iff DUE) are undocumented. |
| 8 | `DUE_convergence/tdsp.py` | The choice of TDSP over static shortest path as the benchmark is a domain decision: in a time-varying network, the static shortest path is not a valid DUE comparison because costs depend on when you depart. This justification is absent. |
| 7 | `demand_calibration/utils.py` | The congestion ratio definition (`v_avg / v_free`) and the target value (0.6) have no documented theoretical basis or calibration rationale. |
| 6 | `simulation/scenario.py` | The `min_distance = 2 * median_edge_length` heuristic has no explanation. Why 2× the median? |
| 6 | `stopping_rule/stopping_rule.py` | `warm_up = n_routes * 3` — the factor of 3 is a domain heuristic (each route should be visited at least 3 times before learning). Not documented. |
| 5 | `DUE_convergence/tdsp.py` | The `depart = interval_start + 1` offset in `generate_trips_odt_file` (rgap.py line 174) avoids placing vehicles exactly at the interval boundary. The +1 second is an implementation detail that prevents a SUMO edge case — this is not documented. |

---

### 7. SELF-DOCUMENTING CODE

The code is generally well-structured. Most issues are missing documentation rather than poor naming forcing compensatory comments. Specific cases where better code would eliminate documentation needs:

| File | Issue |
|------|-------|
| `experiment.py:85–99` | `accumulate_results` explains `getattr` with a Spanish-named example (`"Padre"`). Replace with a typed dispatch dict or a Protocol; delete the comment. |
| `agents/agent.py:64–70` | The `_compute_expected_travel_time` range-semantics example obscures the real logic. Remove example; add a short docstring about the exclusion of today's observation. |
| `config/config.py:71–78` | Anonymous string literal used as inline comment in class body. Convert to real comments (`#`). |
| `r/shared/plots.R:76` | `quit()` mid-file is a hidden control flow that makes dead code invisible. Move the live code to a separate file or use a sourcing pattern. |

---

### 8. DOCUMENTATION CONSISTENCY

| Issue | Detail |
|-------|--------|
| Mixed docstring styles | Some functions use NumPy-style (`Parameters / Returns` sections), others use plain prose, others have none. No project-wide standard is declared. |
| Inconsistent module docstrings | `environment.py`, `experiment.py`, `parser.py`, `get_free_flow_speed.py`, `get_avg_speed.py` have module docstrings; `agent.py`, `factory.py`, `demand_calibration.py`, `duaiterate.py` do not. |
| British/American spelling | No issues found. |
| Terminology inconsistency | "episode" used consistently in Python; R scripts use both "episode" and "iteration" (duaIterate context is correct, but mixed in comments). |
| `DuaIterate` vs `duaIterate` | Naming alternates between title case and camelCase in comments and identifiers. Pick one. |
| `BM_results` vs `bm_result` | Snake case with capitalized BM is inconsistent across file names and variable names. |

---

### 9. DOCUMENTATION MAINTAINABILITY

| Risk | File | Detail |
|------|------|--------|
| High drift risk | `utils/get_free_flow_speed.py` | Hardcoded default path to Koh network will mislead callers. |
| High drift risk | `utils/get_avg_speed.py` | Hardcoded default path to a dated summary file. |
| High drift risk | `README.md` | Already stale; describes DQN phase, not current BM system. |
| Medium drift risk | `mlflow_tracking/simulation.py` | Large commented-out parameter block in `_extract_mlflow_hyperparams`; will drift as config evolves. |
| Medium drift risk | `r/shared/plots.R` | Dead code after `quit()` on line 76; references stale paths (`data/internal/` dir that may have been renamed). |
| Low drift risk | `config/paths.py` | Fully derived from `BASE_DIR`; path strings are single-source-of-truth. Well-maintained. |
| Latent bug | `mlflow_tracking/analysis.py:26` | `_log_params` is referenced but never called (line 26 reads `_log_params` with no parentheses). This is a silent no-op. Not a documentation issue but a correctness risk. |

---

### 10. ONBOARDING EXPERIENCE

Estimated time for a new developer to:

| Task | Estimate | Bottleneck |
|------|---------|-----------|
| Understand project purpose | ~30 min | README is stale; must read `Docs/design.md` and meeting notes |
| Understand BM algorithm | ~3–4 hours | No paper reference in code; must locate and read Wei et al. (2014) independently |
| Understand DUE / R-gap | ~2 hours | No formula in `rgap.py`; must find textbook reference |
| Understand TDSP pipeline | ~4–6 hours | 15-step pipeline with undocumented domain decisions |
| Run locally | ~1–2 hours | `UserGuide.md` may help; SUMO installation not documented |
| Contribute safely | ~2 weeks | Core algorithmic files have no invariants documented |

**Biggest single onboarding gap:** The absence of any paper reference or formula in `agents/agent.py`. A new contributor touching the BM update logic has no ground truth to check against.

---

## Part 2 — Knowledge Hotspots

### Hotspot 1 — `agents/agent.py` — BMAgent update rules

**Score: 9/10**

**Why it exists:** Implements the Bush-Mosteller reinforcement learning model for route choice.

**Context recovery cost:**
- Why does this exist? Learnable only from README/meetings, not from code.
- What problem does it solve? Route probability update based on relative travel time performance.
- What assumptions does it rely on? Exponential memory decay with `gamma`. Warm-up period. Symmetric normalisation of stimulus with `epsilon`. Exclusion of today's travel time from ET.
- What would break if modified? Any change to stimulus computation alters convergence behaviour and would invalidate comparison with the DUE baseline.
- How was the approach chosen? Wei et al. 2014 — not cited anywhere.

**Documentation gaps:**
- No paper reference
- No formula for ET, PT, or stimulus
- No explanation of the asymmetric stimulus branch (positive vs negative)
- No invariant: `sum(p) == 1` at all times

**Recommended fix:** 5-line module docstring + inline formula comments (see Remediation section).

---

### Hotspot 2 — `DUE_convergence/tdsp.py` — TDSP pipeline

**Score: 8/10**

**Why it exists:** Computes time-dependent shortest paths as the DUE benchmark.

**Context recovery cost:**
- Why TDSP not static SP? Requires external knowledge of DUE theory.
- What does the imputation strategy affect? Missing link costs corrupt the TDSP and therefore the R-gap. The choice between ffill and free-flow is a methodological decision.
- What breaks on modification? Changing the imputation threshold changes R-gap values and therefore whether convergence is reported.

**Documentation gaps:**
- No explanation of why TDSP is needed
- Imputation business rule implicit
- Full grid construction explained in comments but not why it's needed

**Recommended fix:** 8-line module docstring + 3-line docstring on `_fill_missing_travel_times`.

---

### Hotspot 3 — `DUE_convergence/rgap.py` — R-gap formula

**Score: 8/10**

**Why it exists:** Computes the relative gap metric to assess DUE convergence.

**Context recovery cost:**
- What is R-gap? Standard DUE metric from traffic assignment literature.
- What does it measure? How far the current flow pattern is from equilibrium.
- When is it zero? At DUE (no agent can reduce travel time by switching routes).
- What is the "refined" version? Computed per time interval instead of across all departure times — a project-specific extension.

**Documentation gaps:**
- No mathematical formula anywhere
- No explanation of "refined" vs standard R-gap
- No reference to traffic assignment literature

**Recommended fix:** 5-line module docstring with the formula.

---

### Hotspot 4 — `demand_calibration/utils.py` — Calibration controller

**Score: 7/10**

**Why it exists:** Finds the number of agents that produces the target congestion level before RL training begins.

**Context recovery cost:**
- Why is demand calibration needed? Without it, network congestion is uncontrolled and the RL experiment is not reproducible across networks.
- Why use `v_avg / v_free` as the congestion metric? Proxy for the V/C ratio; appropriate for networks without signal data.
- Why clip the update factor to [0.6, 1.4]? Prevents oscillation; chosen empirically.

**Documentation gaps:**
- No explanation of the proportional controller design
- No explanation of the clip bounds
- No convergence guarantee discussion

---

### Hotspot 5 — `simulation/scenario.py` — k-routes computation

**Score: 7/10**

**Why it exists:** Generates the fixed action space (k route alternatives) for each OD pair.

**Context recovery cost:**
- Why `random_factor`? Duarouter with perturbed edge weights finds near-shortest alternative paths.
- Why is the first route computed with `random_factor=1.0`? That returns the true shortest path as the baseline route.
- Why k=3? Domain default.
- Why restrict to k=10 ODs? Reduce the OD space to ensure agents frequently revisit the same routes.

**Documentation gaps:**
- No explanation of why `random_factor=1.0` for the first call
- No explanation of the OD restriction rationale

---

### Hotspot 6 — `DUE_convergence/DUE_convergence.py` — Full DUE pipeline orchestration

**Score: 6/10**

**Why it exists:** Orchestrates 15-step DUE convergence check for both BM and duaIterate.

**Context recovery cost:** Moderate. The numbered steps give reasonable navigation. The relationship between BM results and duaIterate results (they are compared to confirm BM convergence relative to a known DUE solver) is not explained at the top.

**Documentation gaps:**
- No module-level explanation of the two-algorithm comparison design

---

### Hotspot 7 — `stopping_rule/stopping_rule.py` — Convergence criterion

**Score: 6/10**

**Why it exists:** Stops BM training when the mean L1 policy change falls below a threshold for k consecutive episodes.

**Context recovery cost:**
- Why L1 norm? Measures total probability mass shift — intuitive for probability vectors.
- Why mean across agents? Avoids stopping when only a few agents have converged.
- Why skip warm-up? Policies are uniform and identical before learning; L1 change is uninformative.
- Why `warm_up + 1`? First learning episode still uses the uniform policy carried over from warm-up.

**Documentation gaps:** The `warm_up + 1` offset is the most subtle correctness detail and has no comment.

---

### Hotspot 8 — `DUE_convergence/duaiterate.py` — duaIterate wrapper

**Score: 6/10**

**Why it exists:** Runs SUMO's built-in DUE solver to produce a benchmark R-gap for comparison with BM.

**Context recovery cost:** The step-by-step process (generate trips, call duaIterate, extract last iteration routes, rebuild action table, recompute R-gap using same pipeline as BM) requires knowing that duaIterate produces one solution not a time series, unlike BM.

**Documentation gaps:**
- No module docstring
- Episode=1 hardcoded for duaIterate (it produces a single-snapshot result, not a history) — not commented

---

### Hotspot 9 — `simulation/environment.py` — SUMO file-based integration

**Score: 5/10**

**Why it exists:** Runs each training episode without TraCI by writing a routes XML and invoking the SUMO CLI.

**Context recovery cost:** Low once you know the pattern. The no-TraCI design decision is mentioned only in a code comment (`# This functions creates a rou.xml file that allows to run simulation without traci`). The rationale (speed — TraCI step-by-step is orders of magnitude slower) is absent.

**Recommended fix:** One-sentence comment in `run_episode` explaining why no TraCI.

---

### Hotspot 10 — `r/shared/plots.R` — Legacy plotting script

**Score: 5/10**

**Why it exists:** Original exploratory plotting script. Now superseded by `r/RQ1/RQ1.qmd` but retained.

**Context recovery cost:** The `quit()` on line 76 makes it appear the file ends there. Dead code after that line references stale paths (`data/internal/` directory). This will mislead future contributors.

**Recommended fix:** Delete dead code or move to an archived folder.

---

### Hotspot Priority Ranking (Documentation Investment)

| Rank | File | Score | Reason |
|------|------|-------|--------|
| 1 | `agents/agent.py` | 9 | Core algorithm, no paper reference, high modification risk |
| 2 | `DUE_convergence/rgap.py` | 8 | Central research metric, formula missing |
| 3 | `DUE_convergence/tdsp.py` | 8 | 15-step pipeline, imputation strategy undocumented |
| 4 | `demand_calibration/utils.py` | 7 | Non-obvious control design |
| 5 | `simulation/scenario.py` | 7 | k-routes design decisions missing |
| 6 | `stopping_rule/stopping_rule.py` | 6 | Subtle warm_up+1 offset |
| 7 | `DUE_convergence/DUE_convergence.py` | 6 | Two-algorithm comparison not explained |
| 8 | `DUE_convergence/duaiterate.py` | 6 | episode=1 hardcoding undocumented |
| 9 | `simulation/environment.py` | 5 | No-TraCI rationale missing |
| 10 | `r/shared/plots.R` | 5 | Dead code after quit() |

---

## Part 3 — Documentation Standards Guide

### Module Docstrings

Every module should begin with a docstring that states:
1. What the module contains
2. Why it exists (its role in the system)
3. Any non-obvious dependencies or entry points

```python
"""
Bush-Mosteller reinforcement learning agent for day-to-day route choice.

Implements the BM update rule from:
    Wei, F., Ma, S., & Jia, N. (2014). A Day-to-Day Route Choice Model Based
    on Reinforcement Learning. DOI: 10.1155/2014/646548

Notation
--------
ET  : Expected Travel Time — exponentially weighted mean of all past episodes
PT  : Perceived Travel Time — per-route exponentially weighted mean
β   : Learning rate (config.learning_rate)
γ   : Memory level / decay factor (config.memory_level)
"""
```

---

### Function Docstrings (NumPy style — consistent across project)

Use NumPy-style docstrings for all public functions and any private function whose behaviour is non-obvious:

```python
def compute_rgap_and_refined_rgap(
    flow_paths, cost_paths, cost_min_paths,
    rgap_path, refined_rgap_path,
    rgap_by_od_path, refined_rgap_by_od_path,
):
    """
    Compute relative gap (R-gap) for DUE convergence assessment.

    R-gap formula
    -------------
    R-gap = Σ_{o,d,t,p} f_{odtp} · (c_{odtp} − c*_{odt})
            ─────────────────────────────────────────────────
            Σ_{o,d,t} d_{odt} · c*_{odt}

    where f = flow, c = path cost, c* = minimum cost (TDSP), d = demand.

    R-gap = 0 if and only if the flow pattern is at Dynamic User Equilibrium.

    Parameters
    ----------
    flow_paths : Path
        Parquet file with columns [episode, origin, destination,
        time_interval, path, count].
    cost_paths : Path
        Parquet file with columns [episode, origin, destination,
        time_interval, path, avg_travel_time].
    cost_min_paths : Path
        Parquet file with columns [episode, origin, destination,
        time_interval, cost].
    rgap_path : Path
        Output path — R-gap per episode.
    refined_rgap_path : Path
        Output path — R-gap per episode and time interval.
    rgap_by_od_path : Path
        Output path — R-gap per episode and OD pair.
    refined_rgap_by_od_path : Path
        Output path — R-gap per episode, OD pair, and time interval.
    """
```

---

### Class Documentation

```python
class BMAgent:
    """
    Bush-Mosteller reinforcement learning agent for route choice.

    Agents learn route probabilities over episodic traffic simulations.
    Each episode, the agent selects a route, experiences a travel time,
    and updates its probability vector using the BM rule.

    State
    -----
    p : ndarray of shape (n_routes,)
        Route probability vector. Invariant: p.sum() == 1, p >= 0.
    history : list of (route_idx, travel_time)
        Full history of (chosen_route, reward) tuples.
    expected_travel_time : float
        ET — exponentially weighted mean of all past travel times.
    perceived_travel_times : ndarray of shape (n_routes,)
        PT — per-route exponentially weighted mean.

    Lifecycle
    ---------
    - Warm-up: episodes 1..warm_up — agent acts but does not learn.
    - Exploration guard: learning only begins after all routes have been
      visited at least once.
    - Active learning: probability vector updated each episode thereafter.

    Reference
    ---------
    Wei et al. (2014). DOI: 10.1155/2014/646548
    """
```

---

### Algorithm Documentation (critical for this project)

For the BM stimulus and update rules, add inline formula comments:

```python
def _compute_stimulus(self, chosen):
    """
    Compute normalised stimulus for the chosen route.

    Stimulus measures how much better (or worse) the chosen route was
    relative to the agent's expected travel time, normalised to [-1, 1].

    Formula (positive branch, chosen route is good):
        stimulus = (ET - PT_chosen) / (max_j(ET - PT_j) + ε)

    Formula (negative branch, chosen route is bad):
        stimulus = (ET - PT_chosen) / (|min_j(ET - PT_j)| + ε)

    ε (epsilon) prevents division by zero when all routes have equal PT.
    Unused routes have their PT set to ET so they do not contribute to
    the max/min computation (they are neutral).
    """
```

```python
def _reinforce_chosen(self, p, chosen, stimulus):
    """
    BM reinforcement update (stimulus >= 0, good route).

    p_chosen += (1 - p_chosen) * β * stimulus      [push toward 1]
    p_k      -= p_k * β * stimulus   for k != chosen [pull others down]

    This preserves the simplex constraint (probabilities sum to 1)
    before the explicit normalisation step.

    Reference: Wei et al. (2014), Eq. (6a).
    """
```

---

### Comment Style Rules

- **Write comments that explain WHY, not WHAT.**
- **Delete comments that restate the code** (`# Increment i`, `# Return result`).
- **No anonymous string literals as inline comments.** Use `#`.
- **No commented-out code in production files** — use git history or a feature flag.
- One-line comments are preferred. If a comment requires more than 3 lines, consider whether a docstring or README note is more appropriate.

**Good:**
```python
# Exclude today's travel time from ET (agent uses yesterday's expectation, not today's)
times = [tt for _, tt in self.history[:-1]]
```

**Bad:**
```python
# Old to new
times = [tt for _, tt in self.history[:-1]]
```

---

### TODO/FIXME Conventions

```python
# TODO(miguel): Remove after demand calibration is network-agnostic.
# FIXME: This clip prevents oscillation but is empirically chosen; revisit.
# HACK: duarouter --max-alternatives is ignored; using random_factor loop instead.
```

Always include the author tag and a one-sentence reason. `HACK` should link to the relevant SUMO issue or ticket if possible.

---

### README Structure

```markdown
# Project Name

## Purpose
One paragraph: what is being studied, with which algorithm, on which simulator.

## Architecture
Component diagram or table: modules and their roles.

## How to Run
Step-by-step: environment setup, config, python main.py.

## Configuration
Key config fields and their effect.

## Data Flow
Input → processing → output with file paths.

## Research Questions
Which RQ each analysis script answers.
```

---

### ADR Template

```markdown
# ADR-001: No TraCI for episode execution

**Status:** Accepted

**Context:**
TraCI (Traffic Control Interface) allows Python to interact with SUMO
in real time. However, step-by-step interaction carries significant
overhead for large fleets.

**Decision:**
Write the full route file (`.rou.xml`) before each episode and invoke
`sumo` via CLI. Read results from `tripinfo.xml` after the episode.

**Consequences:**
- (+) ~10x faster than TraCI for large agent counts.
- (-) Cannot change routes mid-episode.
- (-) Requires regenerating the route file each episode.
```

---

## Part 4 — Remediation Priority List

### Critical (fix before thesis submission)

1. **`agents/agent.py`** — Add module docstring with paper reference, notation table, and lifecycle description. Add formula docstrings to `_compute_stimulus`, `_reinforce_chosen`, `_penalise_chosen`.

2. **`DUE_convergence/rgap.py`** — Add R-gap formula as module docstring and in `_compute_rgap_generic`. Explain "refined" variant.

3. **`README.md`** — Rewrite to describe the current BM system. The current README describes an abandoned DQN phase.

### High (fix before code review / thesis defence)

4. **`DUE_convergence/tdsp.py`** — Add module docstring explaining TDSP rationale. Add docstring to `_fill_missing_travel_times` explaining the two imputation strategies.

5. **`demand_calibration/utils.py`** — Add docstring to `_calibration_loop` documenting the proportional controller and clip bounds.

6. **`agents/agent.py` — `_compute_expected_travel_time`** — Replace the misleading range-example docstring with a correct explanation of why `history[:-1]` is used.

7. **`mlflow_tracking/analysis.py:26`** — Fix the silent no-op: `_log_params` is referenced but not called. Add `()`.

### Medium (fix during refactoring pass)

8. **`config/config.py`** — Convert the anonymous string literal (lines 71–78) to real `#` comments.

9. **`simulation/scenario.py`** — Add comment explaining `random_factor=1.0` on first duarouter call and the `2 * median_edge_length` min_distance heuristic.

10. **`utils/get_free_flow_speed.py`, `utils/get_avg_speed.py`** — Remove stale hardcoded default paths.

11. **`experiment.py:85–99`** — Delete the `getattr` explanation comment; it explains Python, not the domain.

12. **`r/shared/plots.R`** — Delete or archive dead code after `quit()` on line 76.

### Low (quality-of-life)

13. **`stopping_rule/stopping_rule.py`** — Add comment explaining `warm_up + 1` offset.

14. **`main.py:203–211`** — Delete commented-out profiling block.

15. **`DUE_convergence/duaiterate.py`** — Add module docstring and a comment explaining why `episode=1` is hardcoded.

16. **`DuePaths` docstring** — Fix duplicate attribute entry (`missingness_int` appears twice; second should be `missingness_episode`).

---

## Documentation Debt Scores by File

| File | Score | Band |
|------|-------|------|
| `agents/agent.py` | 85 | Critical |
| `DUE_convergence/rgap.py` | 75 | High risk |
| `DUE_convergence/tdsp.py` | 70 | High risk |
| `demand_calibration/utils.py` | 65 | High risk |
| `README.md` | 90 | Critical |
| `simulation/scenario.py` | 55 | Moderate risk |
| `stopping_rule/stopping_rule.py` | 50 | Moderate risk |
| `DUE_convergence/duaiterate.py` | 55 | Moderate risk |
| `DUE_convergence/DUE_convergence.py` | 40 | Minor gaps |
| `simulation/environment.py` | 35 | Minor gaps |
| `experiment.py` | 30 | Minor gaps |
| `config/config.py` | 30 | Minor gaps |
| `config/paths.py` | 10 | Well documented |
| `mlflow_tracking/simulation.py` | 35 | Minor gaps |
| `agents/factory.py` | 20 | Well documented |
| `parsing/parser.py` | 25 | Minor gaps |
| `parsing/sumo_outputs.py` | 35 | Minor gaps |
| `utils/get_free_flow_speed.py` | 40 | Moderate risk |
| `utils/get_avg_speed.py` | 40 | Moderate risk |
| `r/RQ1/RQ1.qmd` | 15 | Well documented |
| `r/shared/plots.R` | 60 | Moderate risk |

**Overall Project Documentation Debt Score: 61 / 100**

The score is pulled down primarily by the gap in algorithmic documentation (`agents/agent.py`, `rgap.py`) and the stale README. The infrastructure and path management are genuinely well documented. Fixing the top 7 items in the remediation list would bring the score to approximately 35/100.
