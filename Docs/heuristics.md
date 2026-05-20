- **Warm-up for Bush-Mosteller agents**:
    The motivations to introduce this warm-up are two fundamentally:
      1. *Exploration*: To ensure agents have initial experience with different routes before they start updating their preferences. 
      2. *Aspiration and PT initialization*: Since the BM-algorithm, is based on these two quantities, and these are based on previous travel times, on the first episodes we got errors because there were no past travel times. So delay learning, until having enough historical information avoids unstable or undefined updates during initialization. 
    Regarding the number of episodes used as warm-up, because the number of feasible routes per od pair is relatively small, 10 is considered a good heuristic. Even though, we consider that an adaptive version could be better and more scalable.

    Basically this adaptive version would be based on the premise that **an agent can start learning (updating preferences) once they have visited all routes at least once**. Regarding this premise several approaches could be adopted:

    1. *Force exploration* (cycle through routes randomly without repetition until all visited once).  
       -  This idea has some gotchas, specially in a MARL setting. In a single-agent setting, forcing exploration of all actions is usually harmless. But in a traffic MARL environment, the cost of a route depends on how many other agents choose it. Therefore, if many agents are simultaneosly forced to explore the same route, the observed travel time become artifically inflated. As a result, the initial observations are no longer representative of the normal dynamics of the system. 

       - So the chosen strategy, is that agents select routes uniformly at random until all available routes have been experienced at least once. Learning updates are activated individually once this condition is satisfied. It will also be combined with a minimum number of episodes. Because I dont want just to all routes have been visited once, but also to have a minimum number of episodes before learning. This minimum number of episodes will be the number of routes times 3. This ways remains adaptive.