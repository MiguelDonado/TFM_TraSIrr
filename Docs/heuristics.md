- **Warm-up for Bush-Mosteller agents**:
    The motivations to introduce this warm-up are two fundamentally:
      1. *Exploration*: To ensure agents have initial experience with different routes before they start updating their preferences. 
      2. *Aspiration and PT initialization*: Since the BM-algorithm, is based on these two quantities, and these are based on previous travel times, on the first episodes we got errors because there were no past travel times. So delay learning, until having enough historical information avoids unstable or undefined updates during initialization. 
    We consider an adaptive version to set this warm-up:

    Basically this adaptive version would be based on the premise that **an agent can start learning (updating preferences) once they have visited all routes at least once**. Regarding this premise several approaches could be adopted:

    1. *Force exploration* (cycle through routes randomly without repetition until all visited once).  
       -  This idea has some gotchas, specially in a MARL setting. In a single-agent setting, forcing exploration of all actions is usually harmless. But in a traffic MARL environment, the cost of a route depends on how many other agents choose it. Therefore, if many agents are simultaneosly forced to explore the same route, the observed travel time become artifically inflated. As a result, the initial observations are no longer representative of the normal dynamics of the system. 

       - So the chosen strategy, is that agents select routes uniformly at random until all available routes have been experienced at least once. Learning updates are activated individually once this condition is satisfied. So, different agents may start learning at different times (because some may have explored all routes earlier by chance). It will also be combined with a minimum number of episodes. Because I dont want just to all routes have been visited once, but also to have a minimum number of episodes before learning. This minimum number of episodes will be the number of routes times 3. This way remains adaptive.

- **Min-distance heuristic**: This heuristic is used in randomTrips to generate the OD matrix. Basically, I wanna find an adaptive way of finding this parameter, such that it ensures that generated OD matrix are as realistic as possible, in the sense, that OD pairs are not contiguous edges, but edges that are a bit far from the other.
  - Several approaches could be used:
    1. *Ensure OD pairs have a route diversity*: Keep only OD pairs that have at least k routes.
    2. *Median of shortest path distances of OD routes*: Keep only those OD pairs whose shortest path distance is greater than this metric.
    3. *Scale minimum OD distance proportionally to the median edge length of the network*:  This is the approach that is actually used. So this filter is esentially saying trips should span at least several edges.
  - The first two approaches were discarded they required to do expensive computation on the whole OD space (and this OD space was a huge one, because it didnt have any constraints of min-distance...). 

- **Initial guess heuristic demand calibration**: 
  - The heuristic used is adaptive to network size, is pretty simple and easy to compute. Basically it captures the intuition that nº vehicles is proportional to the network length, and is reasonable because larger networks can accomodate more traffic.
  - N = p * L * T where 
    - N: nº vehicles
    - p: vehicles per km per hour
    - L: Total network length
    - T: simulation duration (hours) 

- **Demand calibration loop**:
  - Congestion metric: Observed average vehicle speed divided by Weighted free flow network speed. Smaller values correspond to higher congestion levels.
  - The weighted average free flow speed, the weights are based on edge length. Even though on our case is trivial, because all edges have the same length.
  - The observed average vehicle speed is computing using the average speed at each timestep t, and then averaging over time. (is only about post-warm up vehicles)
  - The proportional update rule is a great idea for stable convergence, because it allows for larger updates when the error is big, and smoother corrections when the error is small.
  - And clipping the updates is also very good stabilization mechanism.

- **Time interval heuristic**
  - Basically this is used as a temporal discretization parameter, that is used mainly when computing the r-gap and with the tdsp. I want the heuristic to be adaptive to the network, capturing the intuition that the time interval should be proportional to the median duration of the trips in the network (free-flow travel times)(we compute free flow travel time for all routes in the network). ChatGPT says that a typical trip duration should span 4-10 intervals, and so the alpha would be amongst [0.1-0.25]. The smaller intervals, the more computationally expensive, and better TDSP fidelity. In real life, 15 min is the minimum (because there is no more detailed OD matrices).

- **Generate departure times**
  - Randomly among interval of simulation
  
- **Ensure routes**
  - Try to construct for each OD k routes. The computation of routes is done for all ODs at the same time, until all ODs have k routes or until maximum nº tries.

- **Generate OD space**
  - Generate randomtrips for all agents (post-warm up)
  - Restrict the OD space to have <= k unique ODs
  - Pick the k most frequent ODs, according to the trips that randomtrips generated.
  - Sample ODs for all agents from that restricted OD space

- **Warm-up simulation time**
  - The program allows the possibility to introduce a warm-up period so we only take into account for analysis the agents generated after the warm-up period.
