**Purpose**: Informal reasoning of secondary decisions in my project
**Structure of the document** : sections + bullet points + short reasoning blocks

## 1. Flowchart

- Layers: Conceptual

**Reasoning**

Instead of each layer refer to one python file, each layer refers to some concept, i.e. scenario, agent (contains all agent-related code)

## 2. Functions learned during the project 

- Weighted average: np.average(array, weights)
- rowwise(): Change tidyverse behavior to apply logic per row instead of per column

**Reasoning**

- We can compute a weighted average using `np.average(array, weights = weights)`
- rowwise() explanation:
```r
# 1. In dplyr, operations normally work on whole columns at once
df %>%
    mutate(x2 = x * 2)
# Here x is a vector (entire column)
# R does vectorized computation
# Internally:
x2 = [x1*2, x2*2, x3*2, ...]

# 2. In our case:
rowwise() %>%
  mutate(time = list(seq(entry_time, exit_times))) 

# entry_time is a vector (column)
# exit_times is a vector (column)

# So R tries to do:
seq(c(5,10,3,...), c(9,12,7,...))
# So is not taking just the entry_time and the exit_times of the actual row, but instead it takes the whole column

# 3. What rowwise() does:
# Change behavior to: 
# Treat each row as a mini dataframe of size 1
# With rowwise()
for each row:
    seq(entry_time_i, exit_time_i)
```

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


## 5. Programming style

- Programming paradigm: OOP

**Reasoning**
- I prefer to use OOP instead of functional programming, because a class is better if we want to extend functionality in the future. For example, for the `io_module` I had the doubt of using functions instead of classes (Parser, Plotter...) but for the sake of being able to easily extend it I sticked to OOP.

## 6. Parsing outputs

- Programming language: Python

**Reasoning**
For simplicity has to be done in Python, because we have to parse the outputs files after each episode.

## 7. Format output files

- Format: Parquet

**Reasoning**
Parquet format is more efficient than csv or similar formats. There are some techniques to make them even more efficient. 

**Scalability**
If when using a network that is very big, I have some scalability issue when writing or reading parquet files, see See https://r4ds.hadley.nz/arrow.html. There are techniques to manage more efficiently parquet files.


## Pending
- c/p:
  - Sumo docker








  - Network Santiago y BCN similar in size to Mari Paz network
  - ESCRIBIR (Koh (decision zone was bad), BM)
  - Grabar video editado con como funciona
  - Preguntar lo de cuando los genero los vehiculos todos en 0, o cambio
  - Ensure reproducibility in my simulations, for that I guess that I have to store as well the hyperparameters that I used, maybe using MLFlow or lets see how its done
  - Heuristica generar demanda para una network en concreto

- l/p:
  - Bottlenecks large networks:
    - compute_k_routes: The problem is that because the trips are generated randomly, we end up having a lot of different od pairs, and so we end up having to call compute_k_routes a lot of times. If the network is small, we do not have any problem because each call goes very fast. But if network is large, calling duarouter to compute shortest path takes a considerable amount of time. Possible solutions:
      - Reduce number of different od pairs, so that we have to make less calls to duarouter. Maybe instead of generating random trips for all agents, generate random trips for a fraction of the agents, and then assign the rest of the agents proportionally to the generated od pairs.
      - Find another SUMO tool instead of duarouter that computes shortest path or at least some heuristic/approximation.
      - Use a network of small/medium size (doenst look like a great solution)
  - Pytorch RL snake
  - Leer paper "Where does this road go"
  - How to incorporate DRL, experience replay...
  - Check experiment evaluation in papers
  - Mirar lo de behavioral, bandit...
  - Grafica thesis Mari Paz (nº de caminos)
  - Entender lo de preventivo y reactivo
  - State space (informacion historica de mi camino y tambien estaria bien ver que links fueron problematicos)





