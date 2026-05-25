# Research questions

This file will store potential research questions. Is more like a brainstorming notes rather than a final version of research questions.
Is is important to remember what the teacher told me. "Before doing an experiment is important to know what I want to answer". 
All people relates to traffic, so try formulate intuitive questions and plots, and
it will be a great thesis.


It will have the next structure:
- Question
- Why it matters
- Variables involved
- Possible plot/statistical method
- Expected insight

Basic concept: Coste generalizado y coste ponderado se refieren cuando ademas del travel time incluimos mas cosas en el coste percibido.


## Behavioral RL
1. **Question: Analyze how nonlinear RL mechanism in the BM probability update rules affect learning dynamics, route adaptation, and convergence towards DUE states.**
- Why it matters: The classical BM update mechanism assument that agents react linearly to stimulus. However, real human decision-making processes are often nonlinear. Drivers may tolerate small travel-time increases without significantly changing behavior, while reacting strongly congestion exceeds certain thresholds. Introducing nonlinear reinforcement mechanism allows studying whether more behaviorally realistic adaptation rules produce different traffic dynamics and convergence properties. In particular, is important for several reasons:
  - Behavioral realism: Human perception and reaction to travel time changes are rarely linear. Nonlinear may capture better.
  - Sensitivity to congestion: Different nonlinear update functions may alter how strongly agent react moderate versus severe congestion conditions.
  - Learning dynamics: May produce different convergence behavior, smoother adaptation, delayed reactions, stronger oscillations.
  - Emergence of equilibrium: May affect whether or not is capable of converging towards DUE state.
  - Formal version: Analyzing nonlinear reinforcement mechanisms helps understand how different ways of reacting to travel-time changes influence the learning dynamics and resulting traffic patterns.

- Variables involved: Learning rate, Reinforcement update function rule, R-gap

- Possible plots: Route-switching frequency analysis, Convergence stability, comparison of convergence speed, R-gap evolution for different functions, Visualization of the RL function themselves.

- Expected insight:  The analysis may reveal that nonlinear reinforcement mechanisms significantly alter the adaptation behavior of agents and the resulting traffic dynamics. In particular, threshold-like or weakly sensitive reinforcement functions may produce smoother and more stable adaptation by reducing overreaction to small travel-time fluctuations. Conversely, highly sensitive nonlinear responses may amplify route-switching behavior and generate stronger oscillatory dynamics. Additionally, the experiment may help determine whether more behaviorally realistic reinforcement mechanisms improve the plausibility and stability of the resulting equilibrium-like traffic states.

2. **Question: Analyze how incorporating travel-time variability (variance) into the perceived route cost affects route-choice behavior, learning dynamics, and convergence properties of BM model**.

- Why it matters: The current BM formulation assumes that agents evaluate routes exclusively based on the average past travel times. However, real drivers often consider not only expected travel time, but also the reliability and variability of a route. In practice, some drivers may prefer routes with slightly higher average travel times if those routes provide more predictable and stable travel conditions. Therefore, incorporating travel-time variance into the perceived route cost may produce more behaviorally realistic route-choice behavior. This analysis is important for several reasons:
  - Behavioral realism: Real-world route choice is often influenced by reliability and uncertainty, not only by average travel time. 
  - Risk-sensitivities
  - Learning dynamics: Reliability-sensitive agents may adapt differently potentially producing different convergence and oscillatory behaviors.
  - Formal version: Incorporating travel-time variability into the perceived route cost allows evaluating how route reliability influences adaptive route-choice behavior and the resulting traffic dynamics.

- Variables involved: Past travel times and its variance, reliability sensitivity parameter, R-gap, Perceived route cost

- Possible plots: R-gap evolution, Route-choice distributions under different relaibility sensitivities, Variance of experienced travel times across routes. Distribution of experienced travel-time variability. Path-flow evolution plots.

- Expected insight: The analysis may reveal that incorporating travel-time variability into the perceived route cost produces more conservative and reliability-oriented routing behavior. In particular, agents may avoid routes with highly unstable travel times even when those routes provide lower average travel costs. Additionally, the experiment may help determine whether reliability-sensitive decision-making generates smoother traffic distributions, different congestion structures, or more stable learning dynamics compared to purely average-cost-based adaptation mechanisms.

- Possible extensions: Another decision to take, is how many of our agents wil be reliability-sensitive agents. That would lead to heteregeneous risk preferences, which is very realistic. Real drivers are not identical.


## DUE convergence
1. **Question: Analyze whether a Multi-Agent reinforcement learning approach, like Bush-Mosteller, is capable of converging towards a Dynamic User Equilibrium (DUE) state within a microscopic traffic simulation environmnet**

- Why it matters: Classical DUE approaches are typically based on iterative flow assignment procedures combined with dynamic network loading methods. In constrast, BM model represents a RL model in which agents adapt their route choices based on past experienced travel costs. Veryfing if such approach can converge towards a DUE state is important for several reasons:
  - Behavioral realism: Real drivers do not solve optimization problems. Instead, they adapt based on past experiences. Therefore, RL approaches may provide a more behaviorally plausible representation of day-to-day route choice adaptation.
  - Microscopic simulation complexity: Previous studies based on analytical travel-time functions such as BPR formulas, showed convergence of BM model towards a DUE state. The present work considers a microscopic traffic simulator. Showing convergence under these conditions would strengthen the relevance of learning-based approaches.
  - Alternative to classical asignment methods
  - Formal version: "Evaluating whether a decentralized reinforcement-learning-based approach converges towards a DUE state provides insight into the extent to which equilibrium traffic patterns may emerge from local adaptive behavior within realistic microscopic traffic simulation environments."

- Variables involved: R-gap

- Possible plots: R-gap evolution across episodes, comparison final r-gap against duaIterate. Analyze different r-gap formulations (aggregated, interval specific, od specific). Convergence speed analysis. Variance analysis across episodes.

- Expected insight: The analysis may reveal whether RL approaches can converge to a DUE state using a traffic microsimulator.

2. **Question: Analyze whether the learning rate parameter affects the convergence speed of the BM model without significantly altering the final ability of the system to approach a DUE state.**

- Why it matters: The learning rate controls how strongly agents adapt their route-choice probabilities in response to the stimulus (experienced travel costs - baseline). Therefore it directly influences the dynamics of the learning process. Understanding the impact of learning rate is important for several reasons:
  - Convergence dynamics: Different learning rates may affect how quickly the system stabilizes. Low learning rates may produce slow adaptation, whereas large learning rates may generate oscillatory behavior.
  - Stability of the learning process
  - Separation between convergence speed and equilibrium state: If different learning rates lead to similar R-gap values but different convergence speeds, this would suggest that the learning rate primarily affects the transient dynamics of the system rather than the equilibrium state itself.
  - Sensitivity analysis: The experiment may help identify ranges of learning-rate values that provide a good balance between convergence speed and stability, while still allowing the system to approach DUE-like traffic states.

  - Formal version: Analyzing the influence of the learning rate parameter allows evaluating how strongly the adaptation speed of agents affects the convergence dynamics and stability of the Bush--Mosteller learning process.

- Variables involved: Learning rate, R-gap

- Possible plots: R-gap evolution across episodes for different learning rates. Convergence speed comparison. Sensitivity analysis over learning-rate values.

- Expected insight: The analysis may reveal that the learning rate primarily influences the speed and stability of the learning dynamics rather than the final equilibrium state reached by the system. In particular, smaller learning rates may produce smoother but slower convergence, whereas larger learning rates may accelerate adaptation at the cost of increased oscillatory behavior. Additionally, the experiment may help identify ranges of learning-rate values that provide a good balance between convergence speed and stability, while still allowing the system to approach DUE-like traffic states.

3. **Question: Analyze whether reducing the memory level of agents prevents the BM model from converging towards a DUE state**

- Why it matters: The memory parameter determines how strongly past travel times influence future route-choice decisions. When memory is perfect, agents accumulate stable long-term knowledge of network conditions, which may faciTraffic scenario analysis: 
      - Link capacity degradation: Check that initial network equilibrium can be restored after link recovers.  litate convergence towards DUE. However, when memory decreases, agents progressively forget past experiences and rely more heavily on recent observations. Studying the impact of lower memory levels is important for several reasons:
  - Stability of the learning process: Lower memory levels may introduce stronger fluctuations in route-choice behavior, preventing to reach a DUE state.
  - Role of historical information: Evaluate whether long-term accumulation of travel experience is necessary for equilibrium emergence.
  - Behavioral realism: Real drivers rarely possess perfect memory. Therefore, understanding how imperfect memory affects convergence is important to assess the realism and limitations of the model.
  - Formal version: Analyzing the effect of lower memory levels provides insight into the role of historical experience retention in the convergence and stability properties of decentralized reinforcement-learning-based traffic assignment models.

- Variables involved: Memory decay parameter, R-gap

- Possible plots: R-gap evolution across episodes for different memory levels. Comparison final R-gap values. Sensitivity analysis over memory parameter values.

4. **Question: Analyze whether aggregate performance metrics, such as travel times or R-gap (aggregate rewards), stabilize earlier and more smoothly than path flows (policies/route choices) during BM learning process**

- Why it matters: In MARL, different variables may converge at different temporal scales. Aggregate performance indicators may stabilize relatively quickly, while agents policies continue adapting for a larger number of iterations. Understanding this phenomenom is important for several reasons:
  - Performance vs policy convergence: Stable travel times do not necessarily imply policies have converged. Agents may continue redistributing themselves among alternative routes with similar costs.
  - Learning dynamics: Oscillatory path flow behavior may naturally emerge from small travel-time differences between competing routes, bounded rationality, exploration.
  - Interpretation of equilibrium: Small R-gap values and stable travel times may indicate macroscopic equilibrium-like behavior even when microscopic route-choice adaptation is still ongoing.
  - Formal version: Analyzing the convergence of both aggregate traffic metrics and route-choice distributions provides insight into how the learning process stabilizes at both the network and agent levels.

- Variables involved: Path flows, route choice probabilities, r-gap, travel times.

- Possible plots: Path-flow evolution across episodes. Travel-time evolution, R-gap evolution. Comparison of stabilization times for flows and travel costs.

- Expected insight: The analysis may reveal that aggregate performance metrics such as travel times and R-gap stabilize relatively quickly, while microscopic variables such as path flows continue exhibiting stronger oscillatory behavior before eventual convergence. In particular, the experiment may help identify whether route-choice adaptation persists primarily among routes with similar travel costs, where small variations in experienced costs continuously redistribute traffic without substantially affecting overall network performance. This would suggest that macroscopic equilibrium-like behavior may emerge earlier than full microscopic stabilization of the agents' routing policies.

## Paths/edge comparison
Introduction: To do this comparison I take into account the last episode BM and the last iteration of dueIterate. 
The SUMO plots are already implemented in "/home/miguel/6.Projects/Thesis/src/analysis/sumo_edges_visualization.py"

1. **Question: Compare if the paths used by DUE (dueIterate) are the same than the ones used by BM algorithm.**
  
- Why it matters: 
  Multiple traffic distributions may produce similar aggregate performance. So comparin paths help understand the following areas.
  - **Route diversity**: One method may concentrate most traffic on very few routes, while another distributes traffic across many alternatives. Excessive concentration may produce unrealistic congestion, and excessive dispersion unrealistic exploratory behavior. This aspect provides insight into how traffic is distributed over the network. Also look at the traffic concentration on each route.
  - **Behavioral realism**: Allows evaluating whether the chosen routes are plausible, and the resulting behavior resembles realistic navigation patterns.
  - **Spatial traffic distribution**: Even if aggregate metrics are similar, congestion may appear in different areas, different corridors may become dominat.
  - Formal version: "Comparing the paths utilized by both approaches provides insight not only into convergence towards a DUE state, but also into the qualitative traffic distribution patterns generated by each method. In particular, this analysis allows evaluating differences in route diversity, traffic concentration across alternative paths, and the behavioral realism of the resulting route choices."

- Variables involved: "Entered"

- Possible plot: SUMO plot overall edge usage, SUMO plot interval specific, R/Tidyverse OD-specific, R/Tidyverse temporal evolution route choice

- Quantitative path-comparison metric: 

- **Expected insight:** The analysis may reveal differences in how traffic is distributed across alternative routes. In particular, it may help identify whether one approach concentrates traffic on fewer dominant paths, while the other produces a more dispersed routing pattern. Additionally, the comparison may provide insight into the realism and plausibility of the generated route choices, as well as into the spatial distribution of congestion over the network.

  
2. **Question: Compare whether the congestion patterns generated by dueIterate are similar to those produced by BM algorithm.**
- Why it matters: Similar aggregate performance metrics do not necessarily imply similar congestion dynamics over the network. Compare congestion patterns helps understand the following aspects:
  - Spatial concentration of congestion: One method may concentrate congestion on a few critical bottlenecks, while another may distribute congestion more evenly across the network.
  A more balanced distribution of congestion may suggest better utilization of the network infrastructure.
  - Behavioral realism: Inspecting congestion spatially helps evaluate whether the resulting traffic dynamics appear behaviorally plausible.
  - Temporal evolution of congestion: Even if overall congestion levels are similar, congestion may emerge, propagate, and dissispate differently over time.
  - Formal version: "Comparing the congestion patterns generated by both approaches provides insight not only into aggregate network performance, but also into the spatial and temporal   - decay distinto por agente ?distribution of traffic congestion. In particular, this analysis allows evaluating differences in bottleneck formation, congestion propagation, network utilization, and the behavioral realism of the resulting traffic dynamics."

- Variables involved: "density"

- Possible plots: SUMO overall congestion, SUMO interval-specific congestion, SUMO temporal congestion evolution, Peak-congestion interval comparison

- Expected insight: The analysis may reveal whether both approaches generate similar congestion structures over the network, or whether substantial differences emerge in terms of bottleneck formation, congestion intensity, and spatial traffic accumulation. In particular, it may help identify whether one approach produces more concentrated or unstable congestion patterns, while the other distributes traffic more evenly across alternative corridors. Additionally, the comparison may provide insight into the realism and plausibility of the resulting traffic dynamics.
  
## Heterogeneous agents
1. **Question: Analyzing how introducing heterogeneous memory decay parameter values across agents affects the convergence behavior, traffic distribution patterns, and congestion dynamics of BM model.**

- Why it matters: Original formulation assumes a homogeneous population in which all agents share the same memory decay parameter. However, in realistic traffic systems, drivers may differ substantially in how strongly past experiences influence future route choices. Introducing heterogeneous memory decay parameters allows studying the impact of behavioral diversity on the resulting traffic dynamics. May help understand the following aspects.
  - Behavioral heterogeinity: Some drivers may strongly rely on historical experience, while others react primarily to recent traffic conditions. Modeling heterogeneous memory decay introduces variability in the adaptation behavior of agents.
  - Convergence stability: Homogeneous populations with perfect memory are known to converge to DUE-like states. What would happen under heterogeneous memory.
  - Route diversity and exploration: Agents with lower memory may adapt more aggresively to congestion, potentially increasing exploration of alternative routes.
  - Realism of traffic behavior: Real traffic systems are inherently heterogeneous. Allowing different memory decay values may generate more behaviorally plausible traffic dynamics compared to assuming identical learning behavior for all drivers.
  - Formal version: "Introducing heterogeneous memory decay parameters allows evaluating how behavioral diversity among agents influences convergence properties, route adaptation, and the resulting traffic distribution patterns generated by the Bush--Mosteller model."

- Variables involved: Memory decay parameter distribution, R-gap, Overall edge usage, Route diversity, Congestion metrics

- Possible plots: 
  - R-gap evolution across episodes for different heterogeinity levels
  - SUMO edge usage comparison
  - Congestion map (density)
  - Distribution of route choices under heterogeneous vs homogeneous populations
  - Variance of experienced travel times across agents

- Expected insight: The analysis may reveal whether introducing heterogeneous memory decay parameters significantly alters the convergence behavior of the Bush--Mosteller model. In particular, heterogeneous populations may produce more diverse routing patterns, different congestion structures, and potentially less stable convergence dynamics compared to homogeneous populations with identical memory mechanisms. Additionally, the experiment may help determine whether behavioral heterogeneity leads to more realistic traffic distributions and route adaptation patterns, or whether excessive variability in agent memory introduces instability and persistent oscillatory behavior in the network.


## Congestion regimes
Introduction: Congestion level fundamentally changes the difficulty of the routing problem, the stability of learning, and even whether DUE is easy or hard to reach. 

1. **Question: Analyze how different congestion levels affect the learning dynamics, convergence behavior, and resulting traffic patterns of BM model.**
   
- Why it matters: The level of congestion affects the complexity of the traffic assignment problem and the information available to agents during the learning process. In uncongested networks, travel times are relatively stable and route choices straightforward, whereas in congested networks, travel times become highly interintependent and sensitive to the collective behavior of agents. Evaluating the BM model under different congestion regimes, allows studying how the algorithm behaves as the traffic environment becomes increseangly complex. It may help understand the following aspects:
   - Learning difficulty: Higher congestion levels may produce noisier and less stable travel-time feeedback, making route learning and convergence more difficult.
   - Convergence behavior: The model may converge rapidly under low congestion but exhibit oscillatory or unstable behavior in highly congested scenarios.
   - Route diversity: Increasing congestion may force agents to explore and utilize a larger number of alternative routes
   - Sensitivity to network conditions: Some learning mechanism may perform well under moderate congestion but degrade significantly when congestion becomes severe.
   - Behavioral realism: Studying different congestion regimes helps evaluate whether the model generates plausible traffic dynamics under both stable and highly congested conditions.
   - Formal version: "Analyzing the Bush--Mosteller model under different congestion regimes allows evaluating how network conditions influence learning dynamics, convergence properties, route adaptation behavior, and the resulting traffic distribution patterns."

- Variables involved: R-gap, target congestion level, route diversity, variance of experienced travel times, congestion metrics

- Possible plots: R-gap evaluation for different congestion levels, congestion map, route diversity vs congestion level, convergence speed vs congestion level, boxplots of experienced travel times, average travel time vs congestion level.

- Expected insight: Expected insight: The analysis may reveal whether the Bush--Mosteller model remains stable and capable of approaching DUE-like states under increasing congestion levels. In particular, higher congestion regimes may produce slower convergence, increased oscillatory behavior, and greater route diversity due to stronger interactions among agents. Additionally, the experiment may help identify congestion regimes under which the learning mechanism performs robustly, as well as scenarios where the complexity of the traffic dynamics significantly affects the stability and realism of the resulting traffic patterns.



## Traffic scenarios
- **Question: Analyze whether the BM model is capable of readapting and recovering the initial equilibrium traffic state after a temporary degradation of link capacity**

- Why it matters: Real transporation networks are subject to temporary disruptions such as accidents, road works, or reductions in infrastructue capacity. Therefore, a realistic day-to-day learning model should not only be capable of converging under stationary conditions, but also of adapting dynamically when network conditions change. Studying link-capacity degradation and recovery is important for several reasons:
  - Adaptability of the learning process: Agents can successfully adapt their route choices after significant changes in network conditions
  - Resilience of equilibrium states: Helps determine whether the traffic system is capable of recovering its original equilibrium after disruption dissapears.
  - Behavioral realism: Real drivers continously adapt to incidents and changing network conditions. Thefore, recovery experiments provide insight into the realism of the proposed learning dynamics.
  - Robustness of RL-based traffic assignment
  - Formal version: Analyzing the response of the Bush--Mosteller model to temporary link-capacity degradation provides insight into the adaptability, resilience, and stability properties of decentralized learning-based traffic assignment under dynamically changing network conditions.

- Variables involved: R-gap, Path flows, Route Choice Probabilities, Link capacity reduction level 

- Possible plots: R-gap evolution before, during, and after disruption. OD-specific rerouting visualization. Recovery-time analysis. Edge usage evolution. Path-flow redistribution plots.

- Expected insight: The analysis may reveal whether the Bush--Mosteller model is capable of dynamically re-adapting to temporary disruptions and subsequently recovering equilibrium-like traffic conditions once the degraded link capacity is restored. In particular, the experiment may help identify: how rapidly agents adapt their route choices after the disruption, whether the original traffic distribution is recovered, whether persistent oscillations remain after restoration, and how strongly temporary disruptions affect the stability of the learning dynamics.

Other not revelant questions: 
- Effect of memory level and learning rate is opposite on flow evolution (higher memory levels more stable flow evolution, while higher learning rate more oscillations).