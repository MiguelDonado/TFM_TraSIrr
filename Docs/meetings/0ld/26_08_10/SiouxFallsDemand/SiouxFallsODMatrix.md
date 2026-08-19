**After doing a search with DeepResearch I got the following. Basically in the papers they talk about traffic assignment (static models) that use BPR functions. But on my case Im using a microsimulator. Hence is not the same, I cannot introduce as much vehicles as they say.**

## Static assignment model vs Microsimulator
- In static assignment model:
  - Vehicles are treated as continuous flow
  - Links have cost functions (BPR functions)
  - A link can carry arbitrarily large flows as long as the cost function is evaluated
  
- Microsimulator:
  - Every vehicle is simulated individually
  - A 100 m, one-lane road can physically hold only about:
  - Vehicle length ≈ 5 m
  - Gap ≈ 2.5 m
  - Total space ≈ 7.5 m/vehicle
    So the road stores roughly 13 vehicles.
    Even with movement, a one-lane urban road typically has a capacity on the order of **1,500–2,000 vehicles/hour** under ideal conditions.
  - If we use a large demand it represents the physical consequences of that excess demand through queues and potentially gridlock.

# Executive Summary  
For day-to-day RL routing on the Sioux Falls test network, the **standard OD matrix (LeBlanc et al. 1975)** (as provided in TNTP/Bar-Gera) should be the baseline. This matrix has **24 zones, 76 links, and 552 O–D pairs, with total flow 360,600 trips** (treated as hourly flows).  We recommend testing at **low, medium, and high demand levels**: e.g. ~72,120 (20%), ~180,300 (50%), and 360,600 (100%) vehicles (relative to the base OD) to span uncongested to heavily congested regimes.  This spans light traffic (no queues) through saturated conditions (significant delays).  The experimental design should run **several hundred day-to-day iterations** (e.g. 100–500) with mixed initial conditions (e.g. all travelers start with shortest-paths or random routes), allowing stochasticity (e.g. random travel time errors or exploration) to be introduced.  Use standard DUE convergence metrics: **network relative gap, flow stability, travel-time variance**, etc., as well as statistical tests on final-day metrics (e.g. confirm travel times/flows stabilize).  In simulation, use fine **time granularity** (e.g. 1-minute or smaller sub-intervals for the 1‑hour peak) and standard **link performance functions** (e.g. BPR-type functions \(t=a+b\,(f/c)^4\) with \(b=0.15\)) consistent with the Sioux Falls parameters.  Enforce realistic **capacity constraints** and queuing (e.g. FIFO) on links.  Include a brief **warm-up** phase (e.g. 5–10 min) each day to let flows build. 

For RL implementation, define **state** as the traveler’s experienced travel times or route utilities from previous days, and **actions** as choosing among a small set of alternative routes (e.g. top-3 shortest paths).  Use a cost-based reward (e.g. negative travel time) and consider **reward shaping** (e.g. baseline subtraction) to speed learning.  Use an exploration schedule (e.g. ε-greedy decaying from ε≈1.0 to ≈0.1 over initial days, or Boltzmann exploration) to ensure sufficient exploration.  Ensure sample efficiency: for example, initialize Q-values optimistically or use experience replay (in DQN) to stabilize learning.  As baselines, compare against a **static UE solution (Frank–Wolfe)** and a classic day-to-day learning model (e.g. Logit-based day-to-day adaptation).   

Finally, we recommend visualizing results with tables (e.g. OD summary), convergence plots (e.g. gap vs. day), and a workflow diagram.  A **flowchart** of the experimental loop (below) can guide implementation. In summary, use the **LeBlanc (1975) OD matrix** (total 360,600 trips) as base; test scaled versions (~72k, 180k, 360k trips) to cover low/medium/high demand; and run ~200–300 days of RL iterations, measuring convergence via gap and stability.  This setup is most likely to reveal whether the RL algorithm approaches Dynamic User Equilibrium.  

```mermaid
flowchart TD
    A[Initialize network (Sioux Falls, base OD)] --> B[Start Day i];
    B --> C[Each agent selects route (policy ε-exploration)];
    C --> D[Simulate 1-hour traffic (dynamic loading)];
    D --> E[Record link flows & travel times];
    E --> F[Each agent updates Q-values / policy (reward = -travel time)];
    F --> G{Convergence?};
    G -- No --> B;
    G -- Yes --> H[Analyze final flows vs. DUE (calculate gap, variances)];
    H --> I[End];
```

## 1. Sioux Falls OD Matrices in Literature  
The classic Sioux Falls test network originates from Morlok et al. (1973) and LeBlanc et al. (1975). The **standard OD matrix** (LeBlanc 1975, often used via TNTP/Bar-Gera) has **24 zones and 76 links**.  In this matrix each entry was given in *thousands of vehicles per day* and was scaled by 100 in the TNTP data, yielding total trips 360,600 (treated as hourly peak demand).  This is the “full” or **100% demand** level. In practice, many studies test scaled versions: for example, some authors set “low demand” to ~20% of base (~72,120 vehicles) and “medium” to ~50% (~180,300).  (These percentages are common in robustness studies.)  

Another variant appears in continuous simulation scenarios: Rieser et al. (2014) develop an agent-based Sioux Falls with only **home–work trips**, totaling ~168,220 vehicles (daily).  This is roughly half the LeBlanc OD (since it omits other trip types).  Also, the network has known “CNDP variants” (Suwansirikul 1987) where OD flows were multiplied by 0.11 (≈36,060) – these are mostly used in design literature, not day-to-day studies.  

In summary, **the primary dataset** is the LeBlanc 1975 matrix (360,600 trips, TNTP format).  Secondary references (for context) include barrier references: Peeta & Ziliaskopoulos (2001) for DTA history, and Wardrop (1952) for the UE principle, but for OD data we rely on LeBlanc’s legacy.  

## 2. Candidate OD Matrices for Testing  

| **OD Matrix (Source)**  | **Total OD Trips (1‑hour)** | **% of Base** | **Notes/Ref.**  |
|-----------------------|-----------------------------|---------------|----------------|
| LeBlanc et al. (1975) / TNTP | 360,600 | 100%  | Standard base matrix (values×100 from LeBlanc’s paper; peak-hour flows) |
| “Low demand” (scaled) | ~72,120 | 20%  | 20% of base (e.g. to represent light traffic, used in robustness tests) |
| “Medium demand” (scaled) | ~180,300 | 50%  | 50% of base (moderate congestion regime) |
| ETHZ (Rieser 2014, home–work) | ~168,220 | ~47% | Agent-based home–work trips only (synthesized), about half of base OD |
| Suwansirikul (1987) variant | ~39,660 | 11%  | Scaled by 0.11 of LeBlanc (used in CNDP lit), **very low demand** |

*Table:* Summary of common Sioux Falls OD matrices. The **LeBlanc (1975) matrix** (bottom row in TNTP data) is the standard benchmark.  We recommend using this as the base, and testing scaled versions (e.g. 20% and 50%) to explore congestion regimes. The ETHZ/MATSim matrix (168k) and Suwansirikul variant are noted for completeness. 

## 3. Demand Scaling for One-Hour Simulation  
To cover **low/medium/high congestion** in a one‑hour peak scenario, we suggest **three demand levels**: about **0.2×, 0.5×, and 1.0×** the base OD. Numerically, this means roughly **72,000**, **180,000**, and **360,000** vehicles (per peak hour).  - **Low (≈72k)**: Under this demand, all links are typically under capacity, so flow is smooth and travel times are near free‐flow. This serves as an uncongested baseline.  - **Medium (≈180k)**: Links will begin to experience queues and delays on some critical paths; this regime often produces moderate congestion.  - **High (360k)**: This is the standard Sioux Falls peak demand; it typically drives the network into heavy congestion (experiments show widespread delays at 100% demand).  

These levels bracket the commonly used “20%/50%/100%” scaling in Sioux Falls studies. For example, Sohouenou *et al.* (2021) studied network robustness over 20–100% of base demand, finding 360,600 as the congested high case. We adopt similar values. Concrete test values might be 72,120 (20%), 180,300 (50%), and 360,600 (100%), or similar round numbers.  This range ensures the RL algorithm is tested in under-, near-, and over-congested regimes.  

## 4. Experimental Design  
- **Iterations (Days):** Day-to-day learning typically requires many iterations for convergence. We suggest on the order of **100–500 days**. The exact number depends on convergence speed; prior studies (Wei *et al.*, 2014) found flow patterns settling within a few hundred iterations under ideal conditions. Plan to run until gap metrics level off (e.g. <1% day-to-day change).  
- **Initial Conditions:** Try different seeds: e.g. all travelers start on the (static) shortest-time routes, or all randomly distributed. Diverse initials check robustness. For fairness, average results over a few runs with different random seeds or initial route assignments.  
- **Stochasticity:** Include day-to-day randomness so the system doesn’t deterministically oscillate. This can be done via (a) small random noise in perceived travel times, (b) random tie-breaking when multiple equal routes, or (c) randomized portion of travelers exploring vs. exploiting each day.  
- **Route-Choice Model:** Each agent (traveler) can use a simple RL algorithm (e.g. Q‑learning) to choose a route among 2–5 alternatives (the top shortest paths). Agents update their utility estimates from experienced travel times (i.e. reward = –travel time). You may implement **multiagent RL** (each traveler learns independently) or a population-level RL (fraction on each route is state). As baselines, also implement a **logit day-to-day model** (discrete choice based on past travel times) and the traditional **static UE solution** (Frank–Wolfe) for comparison.  
- **Convergence Metrics:** Measure convergence to DUE using **gap measures and stability criteria**. For example, compute the *relative gap* 
  \[
    \text{RelativeGap} = \frac{\sum_{OD} f_{OD} (t_{\text{used}}-t_{\text{min}})}{\sum_{OD} f_{OD}\, t_{\text{used}}},
  \] 
  where \(t_{\text{min}}\) is the shortest possible time.  Also track **network-wide flow changes** (e.g. RMSE of link flows between consecutive days) and **variance of travel times**.  Convergence to DUE implies these metrics approach zero (all used routes equal cost and flows stop changing).  According to FHWA guidance, a relative gap threshold ≲0.01 often ensures stable flows.  
- **Statistical Tests:** Once the system appears stable, apply simple tests to verify. For instance, use a paired t-test or ANOVA on daily total travel times (or link flows) over the last 50 days to confirm no significant trend. A stationary sequence (e.g. via an Augmented Dickey–Fuller test) would indicate equilibrium. Checking that the *distribution* of experienced times is steady also helps. 

## 5. Simulation Considerations  
- **Time Granularity:** For a 1‑hour peak simulation, subdivide time into sufficiently small steps (e.g. 1-minute or smaller) if running a dynamic simulator. If using static assignment, you can break the hour into few sub-intervals (e.g. 4×15-min) to approximate dynamic effects.  
- **Link Performance:** Use the Sioux Falls link data from LeBlanc: free-flow times and capacity. The common formulation is BPR-type: \(t = a + b\,(f/c)^4\) with \(b\) chosen so that \(B=0.15\). (In TNTP data, the free-flow \(a\) is given, and \(b\) is set so that at capacity, travel time = \(a + a*0.15\).) These parameters ensure realistic congestion growth.  
- **Capacity & Queuing:** Enforce link capacities (vehicles/hour). If flow attempts to exceed capacity, include queuing delays. In a microsimulator, use FIFO or Daganzo’s cell-transmission model. In a macroscopic DTA, ensure flows do not exceed capacity, and model spillback via increased travel time.  
- **Warm-Up:** If dynamic, allow an initial warm-up (e.g. 5–10 minutes) to let vehicles enter the network before collecting data. For the day-to-day setup, you might simulate a short pre-trip period with no agents to clear any residual. This avoids initialization bias.

## 6. RL Implementation Tips  
- **State & Reward:** Each traveler’s state can be as simple as “last travel time on chosen route.”  A richer state could include history (e.g. moving average of travel times). The **reward** should reflect travel time (e.g. \(r=-t_{\text{travel}}\)).  You may shape the reward (subtracting a baseline) to avoid large negatives.  
- **Action Space:** Pre-compute a small set of feasible routes per OD (e.g. k-shortest paths) and let the agent pick one each day.  Represent actions in a Q-table or policy network if using function approximation.  
- **Exploration:** Use an exploration schedule: e.g. ε-greedy with ε starting high (≈0.5–1.0) and decaying to a low value (e.g. 0.05) over the first 50–100 days.  Alternatively use a softmax (Boltzmann) policy where the “temperature” decays. Ensure enough exploration so that all routes are tried.  
- **Learning Rates:** If Q-learning, set a learning rate \(\alpha\approx0.1–0.5\). A higher \(\alpha\) can cause oscillations (Wei *et al.* 2014 noted high learning rate leads to oscillations). You might reduce \(\alpha\) over time to stabilize.   
- **Sample Efficiency:** Day-to-day RL can be slow (each agent gets 1 reward per day). To improve, consider experience replay (storing recent experiences and replaying them) or multi-agent updates (if each OD group learns collectively). You can also pre-fill Q-values (optimistic init) to speed early learning.  
- **Baselines:** Compare the RL outcome to: (a) Static UE flows (computed by Frank–Wolfe) and (b) a simple **Imitative Logit** day-to-day model (choosing routes by a logit of experienced costs). If RL fails to converge to UE, these baselines will highlight the gap. Studies like Mao & Shen (2018) and Zhou *et al.* (2022) use RL in similar adaptive routing contexts.  

## 7. Visualization of Workflow and Results  
- **Tables:** As above, include a table of OD totals and scaling, and summary of parameter choices.  
- **Convergence Plots:** Plot **Relative Gap vs. Day** and **std. dev. of link flows vs. Day** to illustrate convergence. Plot each demand scenario separately.  
- **Workflow Diagram:** The experimental loop (shown above in mermaid) helps clarify the day-to-day process.  
- **Flowcharts:** You can also illustrate the network or an agent’s decision process. (For example, a diagram of the Sioux Falls network with illustrative flows could be helpful; one is provided in [27].)  

  
## 8. Key Sources and Final Recommendation  
**Sources:** The primary data source is LeBlanc *et al.* (1975) as presented in Bar-Gera’s TNTP repository.  Seminal DUE references include Wardrop (1952) and Peeta & Ziliaskopoulos (2001) (review), while recent day-to-day learning studies include Wei *et al.* (2014) and the RL works cited above.  For convergence metrics see FHWA’s DTA guide.  

**Recommendation:** For your thesis experiments, **use the original Sioux Falls OD matrix (360,600 trips)** as the base. Test scaled versions at about **0.2× and 0.5×** (≈72k and 180k trips) in addition to the full demand. Simulate each for **100–300 day-to-day iterations**, measuring the network relative gap and flow stability.  Start with free-flow route initialization, include exploration, and compare RL-driven flows against static UE flows.  This concrete setup (base OD + 20%/50% scaling) is most likely to reveal whether the RL algorithm converges to the expected Dynamic User Equilibrium.