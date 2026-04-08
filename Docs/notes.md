**Purpose**: Informal reasoning of secondary decisions in my project
**Structure of the document** : sections + bullet points + short reasoning blocks

## 1. Flowchart

- Layers: Conceptual

**Reasoning**

Instead of each layer refer to one python file, each layer refers to some concept, i.e. scenario, agent (contains all agent-related code)

## 2. Algorithm

- Weighted average: np.average(array, weights)

**Reasoning**

We can compute a weighted average using `np.average(array, weights = weights)`

## 3. Efficiency

- Parse XML output files: Parse inmediately and store only the metrics

**Reasoning**
I had two options:
1. Parse inmediately: Better. Memory efficient, faster, scales well for many episodes
2. Stores all XMLs output files, parse at the end

## 4. Plots

- Plot library: Plotnine
- Experiment evaluation plots: Mean travel time

**Reasoning**
- I know pretty well ggplot and tidyverse ecosystem in R. That's why I will use **Plotnine** as the library to make the plots in Python. It has the same syntax than ggplot. Normally in Python is used matplotlib, but I will stick with Plotnine.

## 5. Programming style

- Programming paradigm: OOP

**Reasoning**
- I prefer to use OOP instead of functional programming, because a class is better if we want to extend functionality in the future. For example, for the `io_module` I had the doubt of using functions instead of classes (Parser, Plotter...) but for the sake of being able to easily extend it I sticked to OOP.