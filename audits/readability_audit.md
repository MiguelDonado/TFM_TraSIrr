# Readability & Naming Audit

**Date:** 2026-06-17  
**Scope:** All Python source files under `src/`

---

## Summary Table

| # | Category | Location | Issue | Importance |
|---|----------|----------|-------|------------|
| R1 | Bug / Naming | `MLflow/mlflow_utils.py:59` | `log_params` called with positional args instead of `log_param` | 10/10 |
| R2 | Consistency | `DUE_convergence/utils.py` | `dueIterate` vs `duaIterate` — two different spellings in same file | 8/10 |
| R3 | Consistency | `DUE_convergence/utils.py:927,953` | `process_trips_info_duaIterate` vs `process_vehroute_dueIterate` — inconsistent casing of the suffix within the same file | 8/10 |
| R4 | Spelling | `scenario.py:297` | `destinies` should be `destinations` | 8/10 |
| R5 | Naming | `analysis/sumo_edge_analysis.py:52` / `DUE_convergence/utils.py:98` | Functions with 12 parameters | 8/10 |
| R6 | Convention | `scenario.py` / `DUE_convergence/utils.py` | Mixed `_` vs `__` private naming with no consistent rule | 7/10 |
| R7 | Convention | `DUE_convergence/DUE_convergence.py` + `utils.py` | `DUE` mixed into snake_case identifiers | 7/10 |
| R8 | Readability | `agents/agent.py:96-103` | Single-letter aliases `A`, `M`, `M_c` in `compute_stimulus` | 7/10 |
| R9 | Bool flag | `analysis/sumo_edge_analysis.py:64` / `demand_calibration/utils.py:21` | Boolean parameters as control-flow flags | 6/10 |
| R10 | Convention | `DUE_convergence/utils.py:735` | `TARGET_FOLDERS` — UPPER_CASE for a local variable | 6/10 |
| R11 | Spelling | `analysis/sumo_edge_analysis.py:223,333` | `dissagregated` — double typo | 6/10 |
| R12 | Naming | `scenario.py:67` | `od_s` — non-standard plural suffix | 5/10 |
| R13 | Naming | `DUE_convergence/utils.py:863` | `agents_id` — grammatically wrong plural | 5/10 |
| R14 | Naming | `experiment.py:200` | `extract_dict` — too generic, intent unclear | 5/10 |
| R15 | Naming | `scenario.py:83` | `ensure_routes` — not a clear verb | 5/10 |
| R16 | Magic val | `analysis/sumo_edge_analysis.py:377` | `period - 2` unexplained offset | 5/10 |
| R17 | Naming | `agents/agent.py` | `BMAgent`, `compute_ET`, `compute_PT` — unexpanded acronyms | 5/10 |
| R18 | Convention | `DUE_convergence/utils.py:6,16` (see duplication audit F11) | `__private` at module level triggers unintended name-mangling risk | 4/10 |
| R19 | Naming | `parsing/parser.py:39` | `v` for vehicle XML element | 4/10 |
| R20 | Comment | `analysis/sumo_edge_analysis.py:99` | Numbering error: two steps labelled `# 3.` | 3/10 |

---

## R1 — Bug: `mlflow.log_params` called with positional arguments

**Importance: 10/10** ← this is a silent runtime bug, not just a naming smell  
**File:** `src/MLflow/mlflow_utils.py:59`

### Evidence

```python
# mlflow_utils.py:58–59
commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
mlflow.log_params("git_commit", commit_hash)   # ← WRONG
```

`mlflow.log_params` takes a single `dict` argument. Passing two positional strings will raise `TypeError` at runtime. The correct call is `mlflow.log_param` (singular).

### Fix

```python
mlflow.log_param("git_commit", commit_hash)
```

---

## R2 — Naming Consistency: `dueIterate` vs `duaIterate`

**Importance: 8/10**  
**File:** `src/DUE_convergence/utils.py`

### Evidence

| Function | Spelling |
|----------|----------|
| `generate_trips_file_duaIterate` (line 750) | `dua` |
| `call_dueIterate` (line 760) | `due` |
| `run_simulation_dueIterate` (line 780) | `due` |
| `delete_dueIterate_folders` (line 788) | `due` |
| `extract_routes_file_dueIterate` (line 796) | `due` |
| `compute_od_routes_table_dueIterate` (line 827) | `due` |
| `compute_actions_table_dueIterate` (line 910) | `due` |
| `process_vehroute_dueIterate` (line 953) | `due` |

`duaIterate.py` is the actual SUMO binary name, which explains the `dua` spelling in `generate_trips_file_duaIterate`. But every other function in the same file uses `due`. The binary call at line 761 (`"duaIterate.py"`) is correct; the function wrapping it should match the project-wide convention.

### Fix

Replace all `due` by `dua`, as is the name that SUMO uses (duaIterate)

Rename `generate_trips_file_duaIterate` → `generate_trips_file_dueIterate`.

```python
# DUE_convergence/utils.py:750
def generate_trips_file_dueIterate(agents):   # was: duaIterate
    ...
```

Update the call site in `DUE_convergence/DUE_convergence.py:166`:
```python
generate_trips_file_dueIterate(scen.agents)   # was: duaIterate
```

---

## R3 — Naming Consistency: `duaIterate` vs `dueIterate` suffix casing

**Importance: 8/10**  
**File:** `src/DUE_convergence/utils.py`

### Evidence

Two functions in the same file have different casing of the same suffix:

```python
def process_trips_info_duaIterate(...)   # line 927 — all-lowercase
def process_vehroute_dueIterate(...)     # line 953 — camelCase suffix
def process_edgedata_file(...)           # line 1028 — no suffix at all
```

The third function (`process_edgedata_file`) is also about dueIterate data but its name gives no indication.

### Fix

Standardise on `_duaIterate` suffix (all-lowercase, consistent with Python's snake_case):

```python
def process_trips_info_duaIterate(max_iterations, output_file): ...   # unchanged
def process_vehroute_duaIterate(max_iterations, output_file): ...     # was: dueIterate
def process_edgedata_duaIterate(max_iterations, output_file): ...     # was: process_edgedata_file
```

Update all call sites in `DUE_convergence/DUE_convergence.py:210,227`:
```python
process_vehroute_duaIterate(...)   # line 210
process_edgedata_duaIterate(...)   # line 227
```

---

## R4 — Spelling: `destinies` → `destinations`

**Importance: 8/10**  
**File:** `src/scenario.py:297–298`

### Evidence

```python
def parse_od_agents(self, trips_file):
    tree = etree.parse(trips_file)
    origins = tree.xpath("//trip/@from")
    destinies = tree.xpath("//trip/@to")     # ← wrong word
    od_s = list(zip(origins, destinies))
    return od_s
```

`destinies` is not a domain term (that would be `destinations`). "Destinies" means "fates" in English.

### Fix

```python
destinations = tree.xpath("//trip/@to")
od_s = list(zip(origins, destinations))
```

---

## R5 — Function Signatures: 12-parameter functions

**Importance: 8/10**  
**Files:** `src/analysis/sumo_edge_analysis.py:52`, `src/DUE_convergence/utils.py:98`

### Evidence

`run_edge_visualization` — **12 parameters** (`sumo_edge_analysis.py:52–65`):
```python
def run_edge_visualization(
    generic_config,
    config_visualization,
    generic_gui_settings,
    gui_settings_visualization,
    edgedata_BM_file,
    edgedata_dueIterate_file,
    generic_meandata,
    meandata_visualization,
    routes_file,
    metric,
    period,
    aggregated=True,
):
```

`compute_travel_time_links_t_k` — **12 parameters** (`DUE_convergence/utils.py:98–112`):
```python
def compute_travel_time_links_t_k(
    time_interval, network, threshold_density, output_file,
    agents_od_file, vehroute_file, edgedata_file,
    missingness_report_file, missingness_interval_file,
    missingness_edge_file, missingness_episode_file,
    ...
):
```

### Fix for `compute_travel_time_links_t_k`

Group the four missingness output paths into a dataclass or named tuple:

```python
from dataclasses import dataclass

@dataclass
class MissingnessOutputPaths:
    report: Path
    by_interval: Path
    by_edge: Path
    by_episode: Path
```

Then the signature becomes:

```python
def compute_travel_time_links_t_k(
    time_interval, network, threshold_density,
    output_file, agents_od_file, vehroute_file,
    edgedata_file, missingness: MissingnessOutputPaths,
):
```

### Fix for `run_edge_visualization`

Group path arguments into a config object:

```python
@dataclass
class VisualizationPaths:
    generic_config: Path
    config_visualization: Path
    generic_gui_settings: Path
    gui_settings_visualization: Path
    edgedata_BM_file: Path
    edgedata_dueIterate_file: Path
    generic_meandata: Path
    meandata_visualization: Path
    routes_file: Path
```

---

## R6 — Convention: Mixed `_` vs `__` private naming

**Importance: 7/10**  
**Files:** `src/scenario.py`, `src/DUE_convergence/utils.py`

### Evidence

`scenario.py` mixes both conventions with no apparent rule:

| Method | Prefix |
|--------|--------|
| `_run_duarouter` | single |
| `_generate_free_flow_tt_links` | single |
| `_save_od_routes` | single |
| `_set_time_interval` | single |
| `_add_time_intervals_to_agents` | single |
| `_save_agents` | single |
| `__write_trip` | double |
| `__parse_route` | double |
| `__compute_median_free_flow_travel_time` | double |

`DUE_convergence/utils.py` uses `__` for all module-level private functions (`__run_duarouter`, `__decompress_gzip`, `__parse_routes`, etc.). In Python, `__` prefix at module level does not have special semantics (name mangling only applies inside classes). The intention is presumably to signal "internal only", which `_` achieves correctly.

### Fix

Standardise on **single underscore** for all private helpers in both files. Double underscore should only be used inside class bodies for genuine name-mangling needs (there are none here).

In DUE_convergence because there was no class I removed the leading "_" on the functions. I only use it inside classes, to signal they are internal, and should not be called outside class definition (private)

```python
# scenario.py — rename these three:
def _write_trip(self, file_path): ...            # was __write_trip
def _parse_route(self, routes_file): ...         # was __parse_route
def _compute_median_free_flow_travel_time(self): # was __compute_median_...

# DUE_convergence/utils.py — rename module-level helpers:
def _run_duarouter(...): ...          # was __run_duarouter
def _decompress_gzip(...): ...        # was __decompress_gzip
def _parse_routes(...): ...           # was __parse_routes
def _get_unique_routes(...): ...      # was __get_unique_routes
def _build_od_routes_dict(...): ...   # was __build_od_routes_dict
def _process_od_routes(...): ...      # was __process_od_routes
```

---

## R7 — Convention: `DUE` mixed into snake_case identifiers

**Importance: 7/10**  
**Files:** `src/DUE_convergence/DUE_convergence.py`, `src/DUE_convergence/utils.py`

### Evidence

```python
# DUE_convergence/DUE_convergence.py
def run_DUE_convergence_checks(...)
def check_DUE_convergence_BM(...)
def check_DUE_convergence_dueIterate(...)
def generate_generic_files_DUE_convergence()

# DUE_convergence/utils.py
def delete_files_DUE_convergence(...)
```

`DUE` is an acronym (Dynamic User Equilibrium). Python convention (PEP 8) specifies that acronyms in function names should be lowercased in snake_case contexts (e.g., `get_html_content`, not `get_HTML_content`).

### Fix

```python
def run_due_convergence_checks(...)
def check_due_convergence_bm(...)
def check_due_convergence_duaIterate(...)
def generate_generic_files_due_convergence()
def delete_files_due_convergence(...)
```

Similarly in `experiment.py:251`:
```python
def prepare_bm_data(episode, agents): ...    # was prepare_BM_data
```

And in `MLflow/mlflow_utils.py`:
```python
def log_bm_rgap_metric(): ...               # was log_BM_rgap_metric
def log_bm_metrics(): ...                   # was log_BM_metrics
def log_bm_episode_convergence(): ...       # was log_BM_episode_convergence
def log_bm_mean_travel_time(): ...          # was log_BM_mean_travel_time
def log_bm_policy_change(): ...             # was log_BM_policy_change
```

---

## R8 — Readability: Single-letter aliases in `compute_stimulus`

**Importance: 7/10**  
**File:** `src/agents/agent.py:96–103`

### Evidence

```python
def compute_stimulus(self, chosen):
    A = self.ET       # A = Expected Travel Time
    M = self.PT       # M = Perceived Travel Times (array)

    M[np.isnan(M)] = A
    M_c = M[chosen]   # M_c = perceived cost of chosen route

    diff = A - M_c
    if diff >= 0:
        biggest_benefit = max(A - M) + config.epsilon
        stimulus = diff / biggest_benefit
        return stimulus
    else:
        biggest_loss = abs(min(A - M)) + config.epsilon
        stimulus = diff / biggest_loss
        return stimulus
```

`A` and `M` are single-letter names from the original Bush-Mosteller paper. Without reading the paper the intent is opaque. `M_c` is a paper subscript notation.

### Fix

```python
def compute_stimulus(self, chosen):
    expected_tt = self.ET
    perceived_tt = self.PT.copy()       # avoid mutating self.PT in-place

    perceived_tt[np.isnan(perceived_tt)] = expected_tt
    chosen_perceived_tt = perceived_tt[chosen]

    diff = expected_tt - chosen_perceived_tt
    if diff >= 0:
        biggest_benefit = max(expected_tt - perceived_tt) + config.epsilon
        return diff / biggest_benefit
    else:
        biggest_loss = abs(min(expected_tt - perceived_tt)) + config.epsilon
        return diff / biggest_loss
```

> Note: the current implementation mutates `self.PT` via `M[np.isnan(M)] = A` since `M = self.PT` is a reference, not a copy. Adding `.copy()` fixes the hidden side-effect.

---

## R9 — Bool Flag Parameters

**Importance: 6/10**  
**Files:** `src/analysis/sumo_edge_analysis.py:64`, `src/demand_calibration/utils.py:21`

### Evidence

```python
# sumo_edge_analysis.py:64
def run_edge_visualization(..., aggregated=True):
    ...
    if aggregated:
        # one code path
    else:
        # another code path
```

```python
# demand_calibration/utils.py:21
def demand_calibration(last_iteration_gui=True):
```

Boolean flags that control fundamentally different code paths inside a function are a recognised smell. They make call sites harder to read (`run_edge_visualization(..., True)`) and signal the function is doing two different things.

### Fix for `run_edge_visualization`

```python
def run_edge_visualization_aggregated(...):   # drop `aggregated` param, hardcode True path
    ...

def run_edge_visualization_by_interval(...):  # hardcode False path
    ...
```

Or use an `Enum`:
```python
from enum import Enum, auto

class AggregationMode(Enum):
    AGGREGATED = auto()
    BY_INTERVAL = auto()

def run_edge_visualization(..., mode: AggregationMode = AggregationMode.AGGREGATED):
```

### Fix for `demand_calibration`

```python
# demand_calibration/utils.py:21
def demand_calibration() -> int: ...          # always returns demand
# caller decides whether to run gui:
if last_iteration_gui:
    demand_calibration_obj.run_episode_with_gui()
```

---

## R10 — Convention: `TARGET_FOLDERS` — UPPER_CASE local variable

**Importance: 6/10**  
**File:** `src/DUE_convergence/utils.py:735–736`

### Evidence

```python
def delete_files_DUE_convergence(weights_dir, shortest_paths_dir):
    TARGET_FOLDERS = [weights_dir, shortest_paths_dir]    # ← local var, not a constant
    for folder in TARGET_FOLDERS:
        ...
```

`UPPER_CASE` is reserved for module-level constants (PEP 8). A local variable should be `snake_case`.

### Fix

```python
folders_to_clear = [weights_dir, shortest_paths_dir]
for folder in folders_to_clear:
    ...
```

---

## R11 — Spelling: `dissagregated` typo

**Importance: 6/10**  
**File:** `src/analysis/sumo_edge_analysis.py:223,333`

### Evidence

```python
# sumo_edge_analysis.py:223
edge_data.attrib["id"] = "dissagregated"   # ← double 's' and double 'g'

# sumo_edge_analysis.py:333
edges.attrib["edgeDataID"] = "dissagregated"
```

The correct spelling is `disaggregated`. This is also used as an XML ID that is matched in two different places — a spelling fix must be applied atomically to both write sites.

### Fix

```python
# sumo_edge_analysis.py:223
edge_data.attrib["id"] = "disaggregated"

# sumo_edge_analysis.py:333
edges.attrib["edgeDataID"] = "disaggregated"
```

---

## R12 — Naming: `od_s` non-standard plural

**Importance: 5/10**  
**File:** `src/scenario.py:67,69,295,297`

### Evidence

```python
# scenario.py:67
self.od_s = self.generate_od_for_agents()
# scenario.py:297
od_s = list(zip(origins, destinations))
```

`od_s` uses `_s` as a plural suffix, which is not Python convention. Python uses plain plurals: `ods` or better, `od_pairs`.

### Fix

```python
self.od_pairs = self.generate_od_for_agents()
# ...
od_pairs = list(zip(origins, destinations))
return od_pairs
```

Update all references: `self.od_s` → `self.od_pairs` at lines 69, 70, 265, 321, 346.

---

## R13 — Naming: `agents_id` — grammatically incorrect plural

**Importance: 5/10**  
**File:** `src/DUE_convergence/utils.py:863`

### Evidence

```python
agents_id = [vehicle.xpath("@id")[0] for vehicle in vehicles]
```

When you have a list of agent identifiers, the variable should be `agent_ids` (noun + plural marker), not `agents_id` (plural noun + singular marker).

### Fix

```python
agent_ids = [vehicle.xpath("@id")[0] for vehicle in vehicles]
# ...
return dict(zip(agent_ids, edges))
```

---

## R14 — Naming: `extract_dict` — too generic

**Importance: 5/10**  
**File:** `src/experiment.py:200–203`

### Evidence

```python
def extract_dict(parser, config_section):
    return {
        name: parser.extract_many(xpath, str)
        for name, xpath in config_section.items()
    }
```

This function parses all XPaths in a config section into a raw-string dict. The name `extract_dict` says nothing about what is being extracted or from where.

### Fix

```python
def parse_section_to_raw_strings(parser: Parser, config_section: dict) -> dict:
    return {
        name: parser.extract_many(xpath, str)
        for name, xpath in config_section.items()
    }
```

---

## R15 — Naming: `ensure_routes` — unclear verb

**Importance: 5/10**  
**File:** `src/scenario.py:83–87`

### Evidence

```python
def ensure_routes(self, seeds):
    if config.have_precomputed_routes:
        self.reconstruct_od_routes()
    else:
        self.od_routes = self.compute_k_routes(seeds)
```

`ensure` is vague — it doesn't communicate that this method either loads or computes routes. This is a common naming anti-pattern ("ensure X exists" vs "load or compute X").

### Fix

```python
def _load_or_compute_routes(self, seeds):
    if config.have_precomputed_routes:
        self.reconstruct_od_routes()
    else:
        self.od_routes = self.compute_k_routes(seeds)
```

---

## R16 — Magic Value: `period - 2` unexplained offset

**Importance: 5/10**  
**File:** `src/analysis/sumo_edge_analysis.py:377`

### Evidence

```python
breakpoints = list(range(period - 2, config.end_time + period - 2, period))
```

The `- 2` offset appears twice with no explanation. It is not obvious whether this is a SUMO-specific fencepost correction, an off-by-one fix for the GUI, or something else.

### Fix

Name the constant and add a one-line comment explaining the SUMO-specific reason:

```python
# SUMO-GUI breakpoint fires 2 s before the interval boundary to show the transition
BREAKPOINT_LEAD_S = 2
breakpoints = list(range(
    period - BREAKPOINT_LEAD_S,
    config.end_time + period - BREAKPOINT_LEAD_S,
    period,
))
```

---

## R17 — Naming: Unexpanded acronyms in `agents/agent.py`

**Importance: 5/10**  
**File:** `src/agents/agent.py`

### Evidence

| Identifier | Meaning |
|------------|---------|
| `BMAgent` | Bush-Mosteller Agent |
| `compute_ET` | compute Expected Travel time |
| `compute_PT` | compute Perceived Travel time |
| `self.ET` | Expected Travel time (scalar) |
| `self.PT` | Perceived Travel time (vector) |

A reader unfamiliar with the Bush-Mosteller paper cannot deduce what `ET` and `PT` mean without reading comments. The class name `BMAgent` likewise requires context.

### Fix (pragmatic — keep short form but document once)

The cleanest minimal fix is to add type-annotated aliases in `__init__`:

```python
# agents/agent.py — in __init__
self.expected_travel_time: float = 0          # ET in BM paper notation
self.perceived_travel_times: np.ndarray = ... # PT in BM paper notation
```

And rename the methods:
```python
def compute_expected_travel_time(self): ...   # was compute_ET
def compute_perceived_travel_times(self): ... # was compute_PT
```

The class can remain `BMAgent` (it's a recognised domain abbreviation), but add a one-line docstring:
```python
class BMAgent:
    """Bush-Mosteller reinforcement learning agent for route choice."""
```

---

## R18 — Convention: Module-level `__` private functions (name mangling context)

**Importance: 4/10**  
**File:** `src/DUE_convergence/utils.py`

This overlaps with R6. At module level (outside a class), `__name` does not trigger Python's name mangling (which only applies within class bodies). Using `__` for module-level functions is therefore misleading — it implies class semantics that don't exist. Covered fully in R6.

---

## R19 — Naming: `v` for XML vehicle element in parser

**Importance: 4/10**  
**File:** `src/parsing/parser.py:39`

### Evidence

```python
for v in ts.xpath("vehicle"):
    rows.append({
        "vehicle_id": v.get("id"),
        "x": float(v.get("x")),
        "y": float(v.get("y")),
    })
```

`v` is a single-letter variable for an XML element.

### Fix

```python
for vehicle_elem in ts.xpath("vehicle"):
    rows.append({
        "vehicle_id": vehicle_elem.get("id"),
        "x": float(vehicle_elem.get("x")),
        "y": float(vehicle_elem.get("y")),
    })
```

---

## R20 — Comment: Two steps numbered `# 3.` in `run_edge_visualization`

**Importance: 3/10**  
**File:** `src/analysis/sumo_edge_analysis.py:91–100`

### Evidence

```python
# 3. Create meandata file
create_meandata(...)

# 3. Update config file (add gui-settings file)   ← should be # 4.
update_config(...)
```

### Fix

```python
# 4. Update config file (add gui-settings file)
update_config(...)
```

---

## Naming Convention Guide

Based on the findings above, the following rules should be applied consistently across the project.

### 1. Functions and Methods

```
snake_case throughout.
Acronyms lowercased: run_due_convergence, not run_DUE_convergence
                      prepare_bm_data, not prepare_BM_data
Verbs first: compute_*, generate_*, load_*, parse_*, delete_*
Avoid vague verbs: ensure_*, handle_*, process_* (qualify with object)
```

### 2. Private Functions / Methods

```
Single underscore (_) for all private members — both module-level and class-level.
Double underscore (__) only inside class bodies when name-mangling is intentional (rare).
```

### 3. Classes

```
PascalCase. Acronyms treated as words: BushMostellerAgent or BMAgent (with docstring).
One-line docstring mandatory when name contains an abbreviation.
```

### 4. Constants

```
UPPER_SNAKE_CASE only at module level.
Local variables are always snake_case, even if logically constant.
```

### 5. Variables

```
No single-letter names outside list comprehensions / loop indices.
Domain abbreviations (od, tt, bm) are acceptable when universally understood in the domain,
but must be expanded in their first definition (docstring or comment).
Plural form: agent_ids, not agents_id. od_pairs, not od_s.
```

### 6. Boolean Parameters

```
Avoid bool flags that choose between two distinct code paths.
Prefer: two named functions, or an Enum.
Acceptable: flags that enable/disable a side-effect without changing the core logic
            (e.g., verbose=True).
```

### 7. Spelling

```
British vs American: use American English consistently (e.g., `aggregated`, not `dissagregated`).
Domain terms: `destinations`, not `destinies`.
```

## Audit Review Summary
### Implemented changes
R1 — Bug: `mlflow.log_params` called with positional arguments
R2 — Naming Consistency: `dueIterate` vs `duaIterate`
R3 — Naming Consistency: `duaIterate` vs `dueIterate` suffix casing
R4 — Spelling: `destinies` → `destinations`
R6 — Convention: Mixed `_` vs `__` private naming
R7 — Convention: `DUE` mixed into snake_case identifiers
R8 — Readability: Single-letter aliases in `compute_stimulus`
R10 — Convention: `TARGET_FOLDERS` — UPPER_CASE local variable
R11 — Spelling: `dissagregated` typo
R12 — Naming: `od_s` non-standard plural
R14 — Naming: `extract_dict` — too generic
R15 — Naming: `ensure_routes` — unclear verb
R16 — Magic Value: `period - 2` unexplained offset
R17 — Naming: Unexpanded acronyms in `agents/agent.py`
R18 — Convention: Module-level `__` private functions (name mangling context)
R19 — Naming: `v` for XML vehicle element in parser
R20 — Comment: Two steps numbered `# 3.` in `run_edge_visualization`



### Rejected changes
R5 — Function Signatures: 12-parameter functions (Introduces complexity and makes readability more difficult)
R9 — Bool Flag Parameters (It introduces a lot of complexity. Much easier to keep flag parameter, is not only function that is affected, there are several functions)