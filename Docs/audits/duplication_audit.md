# Code Duplication Audit

**Date:** 2026-06-17  
**Scope:** All Python source files under `src/`

---

## Summary Table

| # | Category | Location | Importance | Effort |
|---|----------|----------|------------|--------|
| F1 | Exact | `scenario.py:227` / `DUE_convergence/utils.py:887` | 9/10 | Low |
| F2 | Exact | `DUE_convergence/utils.py:977` / `scenario.py:199` | 8/10 | Low |
| F3 | Structural | `DUE_convergence/utils.py:927,953,1028` | 8/10 | Low |
| F4 | Structural | `DUE_convergence/utils.py` — folder-path boilerplate | 8/10 | Low |
| F5 | Near | `DUE_convergence/utils.py:519,541,568,600` (rgap family) | 7/10 | Medium |
| F6 | Near | `DUE_convergence/utils.py:21,48` (actions+od init block) | 6/10 | Low |
| F7 | Near | `config/config.py:10` / `scripts/network_stats_edges_len.py:13` | 6/10 | Low |
| F8 | Data | `scenario.py:192` / `demand_calibration/demand_calibration.py:62` | 7/10 | Trivial |
| F9 | Structural | `scenario.py:167` / `demand_calibration/demand_calibration.py:46` | 5/10 | Medium |
| F10 | Data | `scripts/` — per-file hardcoded `NETWORK_PATH` | 4/10 | Low |
| F11 | Exact | `DUE_convergence/utils.py:6,16` — double import | 9/10 | Trivial |

---

## F1 — Exact Duplicate: `process_od_routes` logic

**Importance: 9/10**  
**Duplication: 100%**  
**Effort: Low**

### Locations
- `src/scenario.py:227–247` → `Scenario.process_od_routes(self)`
- `src/DUE_convergence/utils.py:887–907` → `__process_od_routes(od_routes)`

### Evidence

`scenario.py:227–247`:
```python
def process_od_routes(self):
    rows = []
    for (origin, dest), routes in self.od_routes.items():
        for route_id, route in enumerate(routes):
            for step, edge in enumerate(route):
                rows.append({
                    "origin": origin, "dest": dest,
                    "route_id": route_id, "step": step, "edge": edge,
                })
    return rows
```

`DUE_convergence/utils.py:887–907`:
```python
def __process_od_routes(od_routes):
    rows = []
    for (origin, dest), routes in od_routes.items():
        for route_id, route in enumerate(routes):
            for step, edge in enumerate(route):
                rows.append({
                    "origin": origin, "dest": dest,
                    "route_id": route_id, "step": step, "edge": edge,
                })
    return rows
```

The only difference is that the method closes over `self.od_routes` while the function takes `od_routes` explicitly.

### Fix

Create `src/utils/od_routes.py`:

```python
def od_routes_to_rows(od_routes: dict) -> list[dict]:
    rows = []
    for (origin, dest), routes in od_routes.items():
        for route_id, route in enumerate(routes):
            for step, edge in enumerate(route):
                rows.append({
                    "origin": origin, "dest": dest,
                    "route_id": route_id, "step": step, "edge": edge,
                })
    return rows
```

Then in `scenario.py`:
```python
from utils.od_routes import od_routes_to_rows

def process_od_routes(self):
    return od_routes_to_rows(self.od_routes)
```

And in `DUE_convergence/utils.py` replace `__process_od_routes` body with:
```python
from utils.od_routes import od_routes_to_rows

def __process_od_routes(od_routes):
    return od_routes_to_rows(od_routes)
```

---

## F2 — Exact Duplicate: `generate_meandata_file` XML body

**Importance: 8/10**  
**Duplication: ~85%**  
**Effort: Low**

### Locations
- `src/scenario.py:199–208` → `Scenario.generate_meandata_file(self)`
- `src/DUE_convergence/utils.py:977–999` → `generate_meandata_file(max_iterations)`

### Evidence

Both write the same SUMO `<additional><edgeData .../></additional>` XML block using manual string concatenation. The only differences are the output file path and the `file=` attribute value.

`scenario.py:199–208`:
```python
with open(MEANDATA, "w+") as meandata:
    meandata.write("<additional>\n")
    meandata.write("\t<edgeData\n")
    meandata.write(f"\t\tid='density_{config.time_interval}s'\n")
    meandata.write(f"\t\tfile='{EDGEDATA_XML}'\n")
    meandata.write(f"\t\tperiod='{config.time_interval}'\n")
    meandata.write(f"\t\texcludeEmpty='true'\n")
    meandata.write(f"\t\twriteAttributes='entered density'/>\n")
    meandata.write("</additional>\n")
```

`DUE_convergence/utils.py:989–998`:
```python
with open(meandata_duaIterate_path, "w+") as meandata:
    meandata.write("<additional>\n")
    meandata.write("\t<edgeData\n")
    meandata.write(f"\t\tid='density_{config.time_interval}s'\n")
    meandata.write(f"\t\tfile='../edgedata_duaIterate.xml'\n")
    meandata.write(f"\t\tperiod='{config.time_interval}'\n")
    meandata.write(f"\t\texcludeEmpty='true'\n")
    meandata.write(f"\t\twriteAttributes='entered density'/>\n")
    meandata.write("</additional>\n")
```

### Fix

Add to `src/utils/od_routes.py` (or a new `src/utils/sumo_xml.py`):

```python
def write_meandata_file(output_path, edgedata_file, time_interval):
    with open(output_path, "w+") as f:
        f.write("<additional>\n")
        f.write("\t<edgeData\n")
        f.write(f"\t\tid='density_{time_interval}s'\n")
        f.write(f"\t\tfile='{edgedata_file}'\n")
        f.write(f"\t\tperiod='{time_interval}'\n")
        f.write(f"\t\texcludeEmpty='true'\n")
        f.write(f"\t\twriteAttributes='entered density'/>\n")
        f.write("</additional>\n")
```

`scenario.py`:
```python
from utils.sumo_xml import write_meandata_file

def generate_meandata_file(self):
    write_meandata_file(MEANDATA, EDGEDATA_XML, config.time_interval)
```

`DUE_convergence/utils.py`:
```python
from utils.sumo_xml import write_meandata_file

def generate_meandata_file(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)
    folder_path = BASE_DIR / folder_number
    path = folder_path / "meandata_duaIterate.xml"
    write_meandata_file(path, "../edgedata_duaIterate.xml", config.time_interval)
    return path
```

---

## F3 — Structural Duplicate: three `process_*_dueIterate` functions

**Importance: 8/10**  
**Duplication: ~80%**  
**Effort: Low**

### Locations

`src/DUE_convergence/utils.py`:
- `process_trips_info_duaIterate` (lines 927–950)
- `process_vehroute_dueIterate` (lines 953–974)
- `process_edgedata_file` (lines 1028–1049)

All three functions follow this skeleton:

```python
def process_X_dueIterate(max_iterations, output_file):
    folder_number = max_iterations - 1
    folder_number = str(folder_number).zfill(3)
    folder_path = BASE_DIR / folder_number
    raw_path = folder_path / "<raw_filename>"
    processed_data = parse_X(episode=1, X_path=raw_path)
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")
```

The only differences per function: raw filename, parse function called.

### Fix

```python
def _process_dueIterate_output(max_iterations, output_file, raw_filename, parse_fn):
    folder_number = str(max_iterations - 1).zfill(3)
    raw_path = BASE_DIR / folder_number / raw_filename
    processed_data = parse_fn(episode=1, **{parse_fn.__name__.split('_')[1] + '_path': raw_path})
    pd.DataFrame(processed_data).to_parquet(output_file, engine="pyarrow")
```

Or more explicitly (preferred for clarity):

```python
def _process_dueIterate_output(max_iterations, output_file, raw_path_fn, parse_fn):
    folder_number = str(max_iterations - 1).zfill(3)
    folder_path = BASE_DIR / folder_number
    raw_path = raw_path_fn(folder_path, folder_number)
    processed = parse_fn(episode=1, path=raw_path)
    pd.DataFrame(processed).to_parquet(output_file, engine="pyarrow")

def process_trips_info_duaIterate(max_iterations, output_file):
    _process_dueIterate_output(
        max_iterations, output_file,
        lambda fp, fn: fp / f"tripinfo_{fn}.xml",
        lambda episode, path: parse_trips_info(episode, path),
    )

def process_vehroute_dueIterate(max_iterations, output_file):
    _process_dueIterate_output(
        max_iterations, output_file,
        lambda fp, fn: fp / "vehroute.xml",
        lambda episode, path: parse_vehroute(episode, path),
    )

def process_edgedata_file(max_iterations, output_file):
    _process_dueIterate_output(
        max_iterations, output_file,
        lambda fp, fn: fp / "edgedata_duaIterate.xml",
        lambda episode, path: parse_edgedata(episode, path),
    )
```

---

## F4 — Structural Duplicate: last-iteration folder-path boilerplate

**Importance: 8/10**  
**Duplication: 100% of the 3-line block**  
**Effort: Trivial**

### Location

`src/DUE_convergence/utils.py` — the following three lines appear **7 times** across these functions:

```python
folder_number = max_iterations - 1
folder_number = str(folder_number).zfill(3)
folder_path = BASE_DIR / folder_number
```

Functions affected (line numbers of first occurrence of the pattern):
- `run_simulation_dueIterate` (781–783)
- `extract_routes_file_dueIterate` (797–802)
- `process_trips_info_duaIterate` (930–934)
- `process_vehroute_dueIterate` (956–960)
- `generate_meandata_file` (979–983)
- `generate_edgedata_file` (1003–1005)
- `process_edgedata_file` (1031–1035)

### Fix

Add near the top of `DUE_convergence/utils.py`:

```python
def _last_iteration_folder(max_iterations: int):
    """Return zero-padded folder name for the last dueIterate iteration."""
    return str(max_iterations - 1).zfill(3)
```

Then replace every occurrence of the 3-line block with:

```python
folder_number = _last_iteration_folder(max_iterations)
folder_path = BASE_DIR / folder_number
```

---

## F5 — Near Duplicate: four `compute_rgap*` functions

**Importance: 7/10**  
**Duplication: ~75%**  
**Effort: Medium**

### Locations

`src/DUE_convergence/utils.py`:
- `compute_rgap` (519–538)
- `compute_redefined_rgap` (541–565)
- `compute_rgap_by_od` (568–597)
- `compute_redefined_rgap_by_od` (600–634)

All four share the skeleton:

```python
df = df.copy()
df["gap_term"] = df["flow"] * (df["cost"] - df["min_cost"])

numerator = df.groupby(<GROUP_KEYS>)["gap_term"].sum()

denominator_df = df[["episode","origin","destination","time_interval","demand","min_cost"]].drop_duplicates()
denominator = (denominator_df["demand"] * denominator_df["min_cost"]
               .groupby(<GROUP_KEYS_DENOM>).sum())

result = (numerator / denominator).reset_index(name=<COL_NAME>)
result.to_parquet(output_path)
```

The only variation is which dimensions are grouped (episode-only, episode+interval, episode+OD, episode+OD+interval) and the output column name.

### Fix

```python
def _compute_rgap_generic(df, group_keys, output_col, output_path):
    df = df.copy()
    df["gap_term"] = df["flow"] * (df["cost"] - df["min_cost"])

    numerator = df.groupby(group_keys)["gap_term"].sum()

    denom_df = df[
        ["episode", "origin", "destination", "time_interval", "demand", "min_cost"]
    ].drop_duplicates()
    denominator = (
        (denom_df["demand"] * denom_df["min_cost"])
        .groupby([denom_df[k] for k in group_keys])
        .sum()
    )

    result = (numerator / denominator).reset_index(name=output_col)
    result.to_parquet(output_path)


def compute_rgap(df, rgap_path):
    _compute_rgap_generic(df, ["episode"], "rgap", rgap_path)

def compute_redefined_rgap(df, refined_rgap_path):
    _compute_rgap_generic(df, ["episode", "time_interval"], "refined_rgap", refined_rgap_path)

def compute_rgap_by_od(df, rgap_by_od_path):
    _compute_rgap_generic(df, ["episode", "origin", "destination"], "rgap", rgap_by_od_path)

def compute_redefined_rgap_by_od(df, refined_rgap_by_od_path):
    _compute_rgap_generic(df, ["episode", "origin", "destination", "time_interval"], "refined_rgap", refined_rgap_by_od_path)
```

---

## F6 — Near Duplicate: `actions + agents_od` initialization block

**Importance: 6/10**  
**Duplication: 100% of 4-line block**  
**Effort: Low**

### Locations

`src/DUE_convergence/utils.py`:
- `compute_flows_odtp_k` (lines 27–35)
- `compute_travel_time_paths_odtp_k` (lines 56–61)

Both start with:

```python
df_actions = pd.read_parquet(actions_path)
df_actions.rename(columns={"action": "path"}, inplace=True)
df_agents_od = pd.read_parquet(AGENTS_OD)
df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)
```

### Fix

```python
def _load_actions_and_agents(actions_path):
    df_actions = pd.read_parquet(actions_path)
    df_actions.rename(columns={"action": "path"}, inplace=True)
    df_agents_od = pd.read_parquet(AGENTS_OD)
    df_agents_od.rename(columns={"id": "agent_id"}, inplace=True)
    return df_actions, df_agents_od
```

Then in both callers:
```python
df_actions, df_agents_od = _load_actions_and_agents(actions_path)
```

---

## F7 — Near Duplicate: `get_edges_lengths` logic

**Importance: 6/10**  
**Duplication: ~80%**  
**Effort: Low**

### Locations
- `src/config/config.py:10–24` → `get_edges_lengths_program(net)` — returns **median**
- `src/scripts/network_stats_edges_len.py:13–34` → `get_edges_lengths_script(net)` — returns **mean** and saves CSV

Both parse the same XPath `//edge[not(@function='internal')]/lane/@length` and produce a numpy array.

### Fix

Extract the shared parsing into a utility, parameterize the aggregation:

```python
# src/utils/network.py
from lxml import etree
import numpy as np

def get_edge_lengths(net) -> np.ndarray:
    tree = etree.parse(net)
    lengths = tree.xpath("//edge[not(@function='internal')]/lane/@length")
    return np.array([float(l) for l in lengths])
```

`config/config.py`:
```python
from utils.network import get_edge_lengths

def get_edges_lengths_program(net):
    return round(float(np.median(get_edge_lengths(net))), 2)
```

`scripts/network_stats_edges_len.py`:
```python
from utils.network import get_edge_lengths

def get_edges_lengths_script(net=NETWORK_PATH):
    data = get_edge_lengths(net)
    np.savetxt(..., data, ...)
    return round(float(np.mean(data)), 2)
```

---

## F8 — Data Duplication: hardcoded `seed value='42'` in SUMO config writers

**Importance: 7/10**  
**Duplication: Exact literal in 2 places**  
**Effort: Trivial**

### Locations
- `src/scenario.py:192` — `conf.write(f"\t\t<seed value='42'/>\n")`
- `src/demand_calibration/demand_calibration.py:62` — `conf.write(f"\t\t<seed value='42'/>\n")`

`config.seed` is already defined as `42` in `config/config.py:49`. Both of these hardcode the literal `42` instead of reading from config.

### Fix

Replace the literal in both files:

```python
# scenario.py:192
conf.write(f"\t\t<seed value='{config.seed}'/>\n")

# demand_calibration/demand_calibration.py:62
conf.write(f"\t\t<seed value='{config.seed}'/>\n")
```

---

## F9 — Structural Duplicate: SUMO config XML written as string concatenation

**Importance: 5/10**  
**Duplication: ~50%**  
**Effort: Medium**

### Locations
- `src/scenario.py:167–197` → `Scenario.generate_conf()`
- `src/demand_calibration/demand_calibration.py:46–65` → `DemandCalibration.generate_conf()`

Both write SUMO config XML by calling `conf.write(...)` repeatedly with manually crafted strings. The `<configuration><input><net-file .../></input></configuration>` skeleton is identical in both.

The demand calibration version is a strict subset of the scenario version (fewer output options). The shared boilerplate is ~8 lines out of 12–28.

### Fix

Extract a builder using `lxml.etree`:

```python
# src/utils/sumo_xml.py
from lxml import etree

def write_sumo_conf(output_path, net_file, seed,
                    route_files=None, additional_files=None,
                    report_outputs=None, device_outputs=None):
    root = etree.Element("configuration")
    inp = etree.SubElement(root, "input")
    etree.SubElement(inp, "net-file", value=str(net_file))
    if route_files:
        etree.SubElement(inp, "route-files", value=str(route_files))
    if additional_files:
        etree.SubElement(inp, "additional-files", value=str(additional_files))
    if report_outputs:
        rep = etree.SubElement(root, "report")
        for tag, val in report_outputs.items():
            etree.SubElement(rep, tag, value=str(val))
    rnd = etree.SubElement(root, "random")
    etree.SubElement(rnd, "seed", value=str(seed))
    if device_outputs:
        dev = etree.SubElement(root, "device")
        for tag, val in device_outputs.items():
            etree.SubElement(dev, tag, value=str(val))
    etree.ElementTree(root).write(
        str(output_path), pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )
```

---

## F10 — Data Duplication: per-script hardcoded `NETWORK_PATH`

**Importance: 4/10**  
**Effort: Low**

### Locations

Each standalone script under `src/scripts/` defines its own `NETWORK_PATH` constant pointing to a development network file. These are not used in production (the runtime reads `config.network`), but they diverge silently when the canonical network changes.

| File | Hardcoded path |
|------|---------------|
| `scripts/get_free_flow_speed.py:10` | `…/Koh/FirstNetwork_Koh.net.xml` |
| `scripts/get_total_length_network.py:8` | `…/Koh/FirstNetwork_Koh.net.xml` |
| `scripts/network_stats.py:9` | `…/Koh/1st_koh_v2.net.xml` |
| `scripts/network_stats_edges_len.py:9` | `…/Koh/1st_koh_v2.net.xml` |

### Fix

Replace each with a reference to `config.network` used as the default:

```python
# scripts/get_free_flow_speed.py
import sys; sys.path.insert(0, str(Path(__file__).parents[1]))
from config.config import config

def get_free_flow_speed(net=config.network): ...
```

Or, since these are dev-only scripts, at minimum consolidate the constant into one place per script instead of letting them drift independently.

---

## F11 — Exact Duplicate: `lxml` imported twice

**Importance: 9/10**  
**Duplication: 100% — trivially fixed**  
**Effort: Trivial**

### Location

`src/DUE_convergence/utils.py`:
- Line 6: `from lxml import etree`
- Line 16: `from lxml import etree`

### Fix

Delete line 16.

---

## Proposed Utilities Module

Based on findings F1–F7, create `src/utils/` with:

```
src/utils/
├── __init__.py
├── od_routes.py      # od_routes_to_rows()          (F1)
├── sumo_xml.py       # write_meandata_file(),        (F2, F9)
│                     # write_sumo_conf()
└── network.py        # get_edge_lengths()            (F7)
```

Internal to `DUE_convergence/utils.py`, add two private helpers:

```python
def _last_iteration_folder(max_iterations: int) -> str:   # F4
    return str(max_iterations - 1).zfill(3)

def _load_actions_and_agents(actions_path):               # F6
    ...
```

And one private helper for the rgap family:

```python
def _compute_rgap_generic(df, group_keys, output_col, output_path):  # F5
    ...
```

---

## Refactoring Priority Order

1. **F11** — double import (1 line, zero risk)
2. **F8** — hardcoded seed (2 lines, zero risk)
3. **F4** — folder-path boilerplate (extract 1 function, touch 7 call sites)
4. **F1** — `process_od_routes` (extract 1 function, touch 2 callers)
5. **F2** — `generate_meandata_file` (extract 1 function, touch 2 callers)
6. **F6** — actions+agents init block (extract 1 helper, touch 2 callers)
7. **F3** — three `process_*_dueIterate` (needs careful lambda/callback design)
8. **F5** — four rgap variants (needs groupby-key parameterization)
9. **F7** — edge-lengths parsing (new `utils/network.py`)
10. **F9** — SUMO conf XML builder (most invasive, use lxml)


## Audit Review Summary
### Implemented changes
F1 — Exact Duplicate: `process_od_routes` logic
F2 — Exact Duplicate: `generate_meandata_file` XML body
F4 — Structural Duplicate: last-iteration folder-path boilerplate
F5 — Near Duplicate: four `compute_rgap*` functions
F6 — Near Duplicate: `actions + agents_od` initialization block
F7 — Near Duplicate: `get_edges_lengths` logic
F8 — Data Duplication: hardcoded `seed value='42'` in SUMO config writers
F9 — Structural Duplicate: SUMO config XML written as string concatenation
F11 — Exact Duplicate: `lxml` imported twice

### Rejected changes
F3 — Structural Duplicate: three `process_*_dueIterate` functions (reason it worse readability a lot, the proposed refactoring was pretty complex code)
F10 — Data Duplication: per-script hardcoded `NETWORK_PATH` (I want to manually define the network path, so claude logic is not correct)