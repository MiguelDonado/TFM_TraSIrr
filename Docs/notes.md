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

- Parse XML output files: Parse inmediately and store metrics

**Reasoning**
I had two options:
1. Parse inmediately: Better. Memory efficient, faster, scales well for many episodes. Overwrite the file on each iteration. (recommended)
2. Stores all XMLs output files, parse at the end

## 4. Data science

- Programming language: R

**Reasoning**
- I know pretty well ggplot and tidyverse ecosystem in R. I find it pretty easy to perform data wrangling and I like a lot ggplot for visualization. 

## 5. Programming style

- Programming paradigm: OOP

**Reasoning**
- I prefer to use OOP instead of functional programming, because a class is better if we want to extend functionality in the future. For example, for the `io_module` I had the doubt of using functions instead of classes (Parser, Plotter...) but for the sake of being able to easily extend it I sticked to OOP.

## 6. Parsing outputs

- Programming language: Python

**Reasoning**
For simplicity has to be done in Python, because we have to parse the outputs files after each episode.

## Pending
- Anotar lo de ChatGPT. Quiero devolver dict planos, en lugar de hierarchical structures. (tidy data)







- Luego visualizarla (Quiero hacer grafica con las rutas)
- En un futuro no guardar lo de "agent_", solamente guardar el numero. Ocupa menos y mas eficiente. Asi luego en R no tengo que eliminarlo
- Grafica thesis Mari Paz (nº de caminos)
- Write down ChatGPT rowwise() logic. Work on rows not on columns
- Anotar todo lo relativo a TAZ (--junction-taz)
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
- I have two kinds of data (vehicle-level, episode-level)
- Think about interesting plots
- Send to R data of ageents, actions...?
- Anotar la logica dle algoritmo
- Quiero que ellos tambien lo puedan tocar el proyecto y jugar.