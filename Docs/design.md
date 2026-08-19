**Purpose**: Track implementation decisions done in my project. 
**Structure of the document** : sections + bullet points + short reasoning blocks

# Design Decisions

## 1. Data science

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

## 2. Vehicle heterogeinity

- Vehicle type: DEFAULT_VEHTYPE

**Reasoning**

I wanna focus on behavioral heterogeinity (aversion traffic lights...) instead of vehicle heterogeinity (truck, car, acceleration...)

## 3. Demand generation
- All vehicles are agents: True
- Zonification: No (edge-based)
- Demand generation (OD-matrix): Random 
- Departures times: Random (uniform)

**Reasoning**
- Regarding **zonification**, as I have written down in **theory.md**, there are multiple options. Among all the options, the only ones that are reasonable for our case, would be the grid-based, voronoi-based (only for BCN, only place where we might have some counters data), administrative, and graph. 
  - But, in our case to keep it simple, and because the other methods also have their cons, we are not gonna do any zonification. So we would not group edges into zones.

- Regarding the demand generation (OD-matrix), is random. **We will stick with generating demand using randomTrips.py and passing some additional options to make it more "realistic"**. Those options are:
  - --fringe-factor: increases the probability that trips will start/end at the fringe of the network
  - --min-distance: geneted trips must have a minimum distance, ensuring that generated trips are not trivially short while maintaining simplicity in the parameter selection.

- We restrict the OD space to have size k. We generate with randomTrips for all agents, and we use the k most common ods as our restricted OD space, and force all the agents to sample from those restricted OD space, not uniformly random but according the normalized weights of those ods on initial distribution.
  
**Verified**
- `scenario.compute_k_routes(od)` has been implemented by calling duarouter multiple times and using option `--weights.random-factor <float>`. This option modifies the edge costs randomly by $x \in [1,<float>]$. Another option would be to use duaIterate.py.
- ¿The generated set of k routes for an OD-pair, needs to be filtered in order to ensure that we get "decent" routes (we are using duarouter and modifying cost of edges by a random factor)?
  - **Solution**: The answer to both questions, after asking the teachers, is that they have told me that using duarouter is fine and we want to discover random routes, even if they are not "efficient". This way we would check that our agents are able to learn and distinguish efficient from not efficient routes. Also when using duaIterate.py, we could be biasing somehow our algorithm to converge to DUE (because the set of k routes, would be the set of routes that we get when iterating on DUE.)
- The function `scenario.compute_k_routes(od)` guarantees in most situations that k routes are generated for od-pair.

**Scalability**
- At first we used Traci in the project to insert the vehicles. But now, we already refactor the project so that Traci does not have to be used because each episode we write a xml file with the trips and pass is as argument when calling `sumo` command. I have notice that now the simulations goes much faster.

## 4. Networks
- All edges have constant speed
- No traffic lights
- Any node of my network can be an origin/destination.
  
## 5. Simulation outputs
- Output files: vehroutes, tripinfo, fcdoutput, summary, statitics

**Reasoning**
- *vehroutes* contains info for one simulation episode about which route (all the edges) a vehicle took, and all the exit times of each edge, allowing hence to know the travel time on each edge of the route
- *tripinfo* contains summary information about one simulation episode for each vehicle about several metrics (duration, routeLength...)
- *statistics* contains summary information about one simulation episode for all the vehicles about several metrics (totalTravelTime, totalrouteLength)
- *fcdoutput* contains information for each timestep and for each vehicle. For example some metrics like speed...
- *summary* contains summary information for each timestep (about all the vehicles) 

## 6. Algorithm Convergence
- Criteria used: Upper bound, policy stability.

**Reasoning**
- *Upper bound* on number of episodes to guarantee termination of the algorithm. Ensures simulation does not run indefinetely in cases where convergence is slow or not achieved.
- *Policy stability*: To monitor evolution of agent behavior. To ensure robustness, is declared policy stable when the mean of individual policy changes remain below a predefined threshold for several consecutive iterations, thereby capturing a persistent absence of learning dynamics. We basically check for each agents its policy change between consecutive episodes. Because policies are a probability distribution over possible routes, we basically take the L1 norm of vector of probabilities for episode t and t-1. We do that for all agents. And then we take the mean of all those agents policy change. If the mean is below a predefined threshold then we considered the algorithm converged.
 
## 7. DUE convergence
- Metric used: Rgap

**Reasoning**
- Rgap is computed for the BM-algorithm across all episodes. It is also computed for the final iteration of duaIterate (SUMO tool that tries to achieve a DUE state). **Rgap it is computed for final iteration of duaIterate because we wanna verify that a DUE is actually attainable for the given network and demand**. For example, imagine that our algorithm BM cannot achieve a DUE, maybe it is not is fault, and not even duaIterate can achive a DUE for that network and demand. 
- I had the doubt, if we should compute the rgap for all the iterations of duaIterate, but I reached the conclusion that it is not worth it, and it would only be useful if we where analyzing the duaIterate tool itself, which is not the case, since it is a SUMO tool. **Hence we only compute rgap for the last iteration of duaIterate.**
