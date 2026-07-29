**Purpose**: Informal reasoning of secondary decisions in my project
**Structure of the document** : sections + bullet points + short reasoning blocks

## 3. Efficiency

- Parse XML output files: Parse inmediately and store metrics

**Reasoning**
I had two options:
1. Parse inmediately: Better. Memory efficient, faster, scales well for many episodes. Overwrite the file on each iteration. (recommended)
2. Stores all XMLs output files, parse at the end

## 4. Data science

- Programming language: R
- Format in which data is stored for later analysis in R (tidyverse): Flat/tabular structure rather than hierarchical format

**Reasoning**
- SUMO generates several output files. Some of them generate **aggregated data** (episode-level), that is total travel time of all vehicles per episode... Other files generate vehicle-level data, i.e. travel time of each vehicle per episode
- I know pretty well ggplot and tidyverse ecosystem in R. I find it pretty easy to perform data wrangling and I like a lot ggplot for visualization. 
- Is important to highlight the concept of **tidy data**. When working with tidyverse, data is easiest to manipulate when it is flat and tabular, rather than deeply nested (hierarchical).
```python
'''
Example:
1. Hierarchical (WRONG):
{
  "user_1": {
    "age": 25,
    "purchases": [
      {"product": "A", "price": 10},
      {"product": "B", "price": 20}
    ]
  }
}
2. Tabular (flat table) (RIGHT):
-------------------------------
user_id | age | product | price
-------------------------------
user_1    25       A        10
user_1    25       B        20
'''
```
   - This align with the tidy data principles:
     - Each variable = one column (user_id, age, product, price)
     - Each observation = one row
 - Flat/tabular data works seamlessly with (dplyr, ggplot2, tidyr)
 - So, although hierarchical representations (nested dictionaries, JSON structure) are common in data storage and transmission, they introduce additional complexity when performing data analysis in environments such as tidyverse in R.


## 7. Format output files

- Format: Parquet

**Reasoning**
Parquet format is more efficient than csv or similar formats. There are some techniques to make them even more efficient. 

**Scalability**
If when using a network that is very big, I have some scalability issue when writing or reading parquet files, see See https://r4ds.hadley.nz/arrow.html. There are techniques to manage more efficiently parquet files.


## Pending

**PARALLELIZE**
3. Don't parallelize combinations naively — I checked config/paths.py: every output path (data/DUE/BM/R-gap/rgap.parquet, etc.) is fixed, not per-run. Two main.py processes running concurrently would clobber each other's scratch files mid-simulation. Real parallelism would need those paths made run-scoped (e.g. per-PID temp dirs) — a nontrivial refactor, so only worth it if the nightly batch keeps growing and single-machine wall-clock becomes the actual bottleneck.
- That's a reasonable call — the risk isn't really about RAM headroom, it's that every output path in config/paths.py is fixed and shared, so two simulations running at once would overwrite each other's intermediate files mid-run in ways that could be hard to notice (wrong data silently mixed together) rather than a clean crash. Not worth that risk for a thesis where correctness of the numbers matters more than shaving off wall-clock time.
If you ever want to revisit it, the lower-risk route isn't refactoring all those paths — it'd be running a second full copy of the repo (e.g. git worktree) so each process gets its own BASE_DIR and therefore its own isolated data/, mlruns/, etc. for free, no code changes. The catch is your local mlflow.db (SQLite) doesn't handle concurrent writers well, so you'd need a shared MLflow tracking server instead of the file-based DB — a separate piece of setup. Given the dev-config + --prepare-only caching we already have, I'd say leave it as sequential for now.




- SUMO docker
- **To write**:
  - Let clear, what it means a simulation, an episode, a time interval, experiment run (some explanatory figure may ease understanding)
  - Explian what I saw in the paper where does this road go, that we trust more the information that we got from experience, than from Google Maps, internal information
  - Briefly acknowledge on the thesis that Im applying TDSP on a non-FIFO table. Example paragraph:
    - The time-dependent shortest-path calculations were performed on discretized average link travel-time tables extracted from SUMO. Due to temporal aggregation, some link travel-time profiles do not strictly satisfy the FIFO property. Consequently, the TDSP computations should be interpreted as approximate shortest paths. However, the resulting Rgap values exhibited the expected convergence behavior, both during Bush-Mosteller learning and during DUA iterations, suggesting that the impact of these violations is limited for the studied scenarios.

- **To read**:
  1. Important conversation about applying modern RL instead of Bush-Mosteller: https://chatgpt.com/c/69e5ffba-c078-8333-a234-3301f406e233

- **R**:
  1. Arreglar large parquet files, no puedo cargarlos todo en R. open_dataset instead Cargar solo por episodio...
  2. Arreglar en script R, que cuando commputo el travel time utilizando vehroutes no esta bien. Porque para la primera fila de acda vehiculo y cada episodio, estoy asumiento que el entry travel time es 0, y eso ahora no es cierto, puesto que los vehiculos tienen departure_time distinto de 0. Lo que deberia hacer es utilizar el departure time de cada vehiculo.
  3. When using R combine with sf package (represent networks greatly)


