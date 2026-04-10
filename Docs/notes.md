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

## Pending
- Luego visualizarla (Quiero hacer grafica con las rutas)
- Grafica thesis Mari Paz (nº de caminos)
- Leer paper "Where does this road go"
- How to incorporate DRL, experience replay...
- Check experiment evaluation in papers
- Entender lo de preventivo y reactivo
- OD-matriz de una hora. Centroid. Cuadricula. Todos contra todos. (zonificacion)
- Guardar self.p, self.history, self.ET, self.PT (he guardado el resto de internal data (rewards, actions...) pero este no lo he guardado porque es especifico de este algoritmo. En el futuro si uso otro algoritmo no me servira el codigo que escriba).
- State space (informacion historica de mi camino y tambien estaria bien ver que links fueron problematicos)
- En la del asiatico, la decision_zone length estaba mal la formula
- Mirar lo de behavioral, bandit...
- Leer Parquet files libro R.
- Think about interesting plots
- Anotar la logica dle algoritmo
- Quiero que ellos tambien lo puedan tocar el proyecto y jugar.