# Design Patterns Audit

**Date:** 2026-06-18  
**Scope:** All Python source files under `src/`  
**Method:** Manual static analysis — class structure, constructor behaviour, module interfaces, data-access sites

---

## Summary Table

| # | Category | Location | Issue | Importance |
|---|----------|----------|-------|------------|
| DP1 | Creational | `scenario.py:39–65` | Constructor does filesystem I/O and subprocess calls (implicit Builder anti-pattern) | 8/10 |
| DP2 | Domain | `scenario.py:71` | Agent data stored as plain `dict` — no type safety | 5/10 |
| DP3 | Domain | `experiment.py:39` | `config` import silently shadowed by a local `yaml.safe_load` assignment | 7/10 |
| DP4 | Creational | `agents/factory.py` | Factory module also owns behavioural ops (`select_actions`, `update_agents`) — naming mismatch | 4/10 |
| DP5 | Creational | `config/config.py:174` | Informal singleton is mutable after construction (`time_interval`, `min_distance` set later by `Scenario`) — hidden ordering dependency | 6/10 |
| DP6 | Domain | scattered | No Repository abstraction — `pd.read/write_parquet` calls spread across 5+ modules | 6/10 |
| DP7 | Structural | `environment.py` | `Environment` mixes route-file generation, episode execution, and reward extraction in one class | 4/10 |
| DP8 | Structural | `DUE_convergence/DUE_convergence.py` | Facade correctly implemented — positive finding | — |
| DP9 | Structural | `MLflow/mlflow_utils.py` | Facade correctly implemented — positive finding | — |
| DP10 | Behavioral | `main.py:172` | `RunMode` strategy implemented as `if/elif` — acceptable at current scale, revisit if modes grow | 2/10 |

---

## Detailed Findings

---

### DP1 — `Scenario.__init__` as an implicit Builder anti-pattern

**Importance: 8/10**

**Location:** `scenario.py:39–65`

`Scenario.__init__` calls four heavyweight operations:

```python
def __init__(self, map, n_agents_warmup, n_agents_post_warmup, seeds, rng):
    ...
    self.generate_agents(rng)      # calls randomTrips.py subprocess
    self.ensure_routes(seeds)      # may call duarouter N times
    self.save_scenario_data()      # writes 4+ parquet files + CSV
    self.conf = self.generate_conf()  # writes SUMO .sumocfg to disk
```

Subprocess invocations, disk writes, and network parsing all happen inside the constructor. This makes `Scenario(...)` non-idempotent, side-effectful, and untestable in isolation — you cannot construct a `Scenario` in a test without touching the filesystem.

The correct pattern is to separate construction from persistence.

**Remediation — split `__init__` into a factory method:**

```python
# scenario.py

class Scenario:
    def __init__(self, map, n_agents_warmup, n_agents_post_warmup, od_routes, conf):
        """Pure data holder — no side effects."""
        self.n_agents_warmup = n_agents_warmup
        self.n_agents_post_warmup = n_agents_post_warmup
        self.n_agents = n_agents_warmup + n_agents_post_warmup
        self.network = map
        self.od_routes = od_routes
        self.conf = conf
        self.agents: list[dict] = []

    @classmethod
    def build(cls, map, n_agents_warmup, n_agents_post_warmup, seeds, rng) -> "Scenario":
        """Factory method — runs subprocesses and writes files, returns ready Scenario."""
        scen = cls.__new__(cls)
        scen.n_agents_warmup = n_agents_warmup
        scen.n_agents_post_warmup = n_agents_post_warmup
        scen.n_agents = n_agents_warmup + n_agents_post_warmup
        scen.network = map
        scen.agents = []
        scen.od_routes = {}

        scen.generate_agents(rng)
        scen.ensure_routes(seeds)
        scen.save_scenario_data()
        scen.conf = scen.generate_conf()
        return scen
```

Call site in `main.py` changes from `Scenario(...)` to `Scenario.build(...)`. No other changes needed.

---

### DP2 — Agent data as untyped `dict`

**Importance: 5/10**

**Location:** `scenario.py:71–81`, `environment.py:37`, `agents/factory.py:13`

Every agent is a plain dict:
```python
self.agents.append({
    "id": f"agent_{i+1}",
    "origin": origin,
    "destination": dest,
    "departure_time": departure_time,
})
```

Later a fifth field `time_interval` is injected by `_add_time_intervals_to_agents`. These dicts are accessed by string key in three different modules — a typo silently returns `None` at runtime.

**Remediation — replace with a dataclass:**

```python
# agents/agent_data.py  (new file, ~10 lines)
from dataclasses import dataclass

@dataclass
class AgentData:
    id: str
    origin: str
    destination: str
    departure_time: int
    time_interval: int = 0
```

Replace `dict` construction in `scenario.py:75–80`:
```python
from agents.agent_data import AgentData

self.agents.append(AgentData(
    id=f"agent_{i+1}",
    origin=origin,
    destination=dest,
    departure_time=departure_time,
))
```

Access sites that currently do `agent["id"]` become `agent.id` — a mechanical rename, no logic changes.

---

### DP3 — `config` import silently shadowed in `experiment.py`

**Importance: 7/10**

**Location:** `experiment.py:15–39`

```python
from config.config import RunMode, config   # line 15: Config dataclass instance

...

with open(YAML_CONF, "r") as file:
    config = yaml.safe_load(file)           # line 39: OVERWRITES config with a plain dict
```

After line 39, `config` is a `dict`, not the `Config` object. Any code in this module that calls `config.mode`, `config.episodes_gui`, etc. would fail or return unexpected results. Currently the module only uses `config["metrics"][...]` (dict access), which works — but the name collision is a latent trap for future edits and makes the import at line 15 misleading.

**Remediation — rename the local variable:**

```python
# experiment.py

# Remove: from config.config import RunMode, config   ← only needed for RunMode
from config.config import RunMode

with open(YAML_CONF, "r") as file:
    xpath_config = yaml.safe_load(file)   # rename throughout this file
```

Replace all 7 occurrences of `config["metrics"]` with `xpath_config["metrics"]`. The `RunMode` import is still needed for `log_run_mode`.

---

### DP4 — `agents/factory.py` mixes Factory with behavioural operations

**Importance: 4/10**

**Location:** `agents/factory.py`

The file comment explicitly says it handles agent creation. It does — but it also owns `select_actions` and `update_agents`, which are episode-level behavioural operations with no creational concern:

```python
def initialize_agents(scen, seed):   # Factory ✓
def select_actions(agents):          # Behavioral — episode-level
def update_agents(agents, ...):      # Behavioral — episode-level
```

This is not a correctness bug, but it misrepresents the module's scope to future readers.

**Remediation — rename the module:**

```
agents/factory.py  →  agents/ops.py   (or agents/agent_ops.py)
```

Update the single import in `main.py:9`:
```python
from agents.ops import initialize_agents, select_actions, update_agents
```

Alternatively keep the file name and split: leave `initialize_agents` in `factory.py` and move the two behavioural functions to `agent.py` or `ops.py`.

---

### DP5 — `Config` singleton mutated after construction

**Importance: 6/10**

**Location:** `config/config.py:98–99, 163–172`, `scenario.py:473–478`

`Config` declares two `field(init=False)` fields that are set externally by `Scenario`:

```python
# config/config.py
time_interval: int = field(init=False)   # set by Scenario._set_time_interval
```

```python
# scenario.py:473
def _set_time_interval(self):
    config.time_interval = int(...)      # mutates the global singleton
```

Anyone who reads `config.time_interval` before `Scenario` is constructed gets `AttributeError` or a stale value. The ordering dependency is invisible from the call site.

**Remediation — two options, easiest first:**

*Option A* — make the default explicit so the field always has a value:
```python
# config/config.py
time_interval: int = 0   # overwritten by Scenario after network analysis
```
Prevents AttributeError; documents that this is a computed default.

*Option B* — pass `time_interval` as a parameter to `Scenario.__init__` and remove the mutation:
```python
# scenario.py  — inside _set_time_interval, return the value instead of mutating
def _compute_time_interval(self) -> int:
    return int(self.__compute_median_free_flow_travel_time() * config.time_interval_heuristic)
```
Then set it locally: `self.time_interval = self._compute_time_interval()` and pass it explicitly to `run_DUE_convergence_checks`. This is the cleaner approach but requires threading the value through more call sites.

---

### DP6 — Missing Repository pattern for data access

**Importance: 6/10**

`pd.read_parquet` / `df.to_parquet` calls are scattered across at least 5 modules:

| Module | Read sites | Write sites |
|--------|-----------|-------------|
| `experiment.py` | — | `save_processed_data` (8 writes) |
| `scenario.py` | `reconstruct_od_routes:91`, `__compute_median…:431` | `_save_od_routes`, `_save_agents`, `write_od_matrix` |
| `MLflow/mlflow_utils.py` | `_log_bm_rgap_metric:136`, `_log_bm_mean_travel_time:186`, `_log_bm_policy_change:201` | — |
| `DUE_convergence/utils.py` | multiple | multiple |
| `stopping_rule` | — | — |

There is no abstraction between the calling code and the storage format. If the output format changes (e.g., from parquet to Arrow IPC, or paths move), every module needs editing.

**Remediation — lightweight data access module (not a full Repository class):**

```python
# data/store.py  (new file)
import pandas as pd
from paths import STATISTICS_PARQUET, VEHROUTE_PARQUET, RGAP, ...

def load_statistics() -> pd.DataFrame:
    return pd.read_parquet(STATISTICS_PARQUET)

def save_statistics(df: pd.DataFrame) -> None:
    df.to_parquet(STATISTICS_PARQUET, engine="pyarrow")

def load_rgap_bm() -> pd.DataFrame:
    return pd.read_parquet(RGAP)

# ... one pair per dataset
```

Callers import `from data.store import load_rgap_bm` instead of `pd.read_parquet(RGAP)`. All path knowledge and engine choice is consolidated in one place. This is a thin wrapper, not a heavyweight Repository class — appropriate for this codebase size.

---

### DP7 — `Environment` mixes three concerns

**Importance: 4/10**

**Location:** `environment.py`

```python
class Environment:
    def generate_routes_file(self, actions): ...  # Concern 1: file serialisation
    def run_episode(self, actions, episode): ...   # Concern 2: subprocess execution
    def get_rewards(self): ...                     # Concern 3: result parsing
```

These three operations are always called together in the same fixed order from `main.py`. Grouping them in a class implies state sharing between calls, but there is no shared state — `generate_routes_file` writes a file, `run_episode` reads it via SUMO, `get_rewards` reads SUMO's output. The class provides structure but no real encapsulation benefit.

**Remediation — minor: extract reward parsing to `experiment.py`**

`get_rewards` already has a sibling function in `experiment.py` (`parse_trips_info`). Moving it there or to `parsing/parser.py` makes `Environment` a pure subprocess wrapper, which matches `Adapter` intent:

```python
# environment.py — after change
class Environment:
    def run_episode(self, actions, episode): ...   # writes file + runs sumo

# main.py
env.run_episode(actions, episode)
rewards = env.get_rewards()          # becomes:
rewards = parse_rewards(TRIPS_INFO_XML)   # new thin function in experiment.py
```

This is a low-priority cleanup; the current design is not incorrect.

---

### DP8 — Facade in `DUE_convergence/DUE_convergence.py` ✓

**Positive finding — no action needed.**

`run_DUE_convergence_checks()` is a textbook Facade: it hides a multi-step pipeline (generic file generation, duaIterate pipeline, BM R-gap pipeline, TDSP sub-pipeline) behind a single function. The private `_check_*` helpers are correctly scoped. This pattern is well applied here.

---

### DP9 — Facade in `MLflow/mlflow_utils.py` ✓

**Positive finding — no action needed.**

`set_up_mlflow()` and `log_simulation_mlflow()` provide a clean two-function surface hiding MLflow's API, artifact paths, and metric serialisation. The `_log_*` private hierarchy is well-decomposed. The `_log_metric_over_time` helper is a good reuse abstraction.

---

### DP10 — `RunMode` strategy implemented as `if/elif`

**Importance: 2/10**

**Location:** `main.py:172–175`

```python
def run():
    log_run_mode(config.mode, config.have_precomputed_routes, config.episodes_gui)
    if config.mode == RunMode.EVAL_GUI:
        run_final_simulation()
    main()
```

With only two branches for three modes, this is simple enough that a Strategy pattern would add indirection for no gain. Worth revisiting only if a fourth mode is added that requires substantially different orchestration.

---

## Patterns Not Present (and Whether They're Missed)

| Pattern | Verdict |
|---------|---------|
| **Observer** | Not needed — no event-driven logic |
| **Decorator** | Not needed — no middleware or composable behaviour |
| **Chain of Responsibility** | Not needed |
| **Command / Task queuing** | Not needed — episodes run synchronously |
| **Proxy / lazy loading** | Not applicable — data files are always fully loaded |
| **Builder** (explicit) | Would benefit `Scenario` — see DP1 |
| **Repository** | Would benefit data access — see DP6 |
