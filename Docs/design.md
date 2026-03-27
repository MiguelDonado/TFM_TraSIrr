**Purpose**: Track implementation decisions done in my project. 
**Structure of the document** : sections + bullet points + short reasoning blocks

# Design Decisions

## 1. Vehicle heterogeinity

- Vehicle type: DEFAULT_VEHTYPE

**Reasoning**

I wanna focus on behavioral heterogeinity (aversion traffic lights...) instead of vehicle heterogeinity (truck, car, acceleration...)

## 2. Demand generation

- Number of OD-pairs: 1
- Number of route choices (k): 3-5
- Departure time: All vehicles at once 
- Number of agents: 50
- All drivers are agents: True

**Pending**
- For simplicity, all agents will start from same OD-pair. Must be extended in the future 
- For simplicity, all agents will have same departure time. Must be extended in the future
  - In SUMO, many vehicles can be scheduled at the same time, but insertion may be delayed if there is congestion. SUMO handles it.
- Implement a check to verify that I have at least k routes for od-pair.
- In library **Flow**, check in the Github, because they several files with popular research networks (copy them) and another automatic generation of networks files.

**To verify**
- `scenario.compute_k_routes(od)` has been implemented by calling duarouter multiple times and using option `--weights.random-factor <float>`. This option modifies the edge costs randomly by $x \in [1,<float>]$. Another option would be to use duaIterate.py.
- ¿The generated set of k routes for an OD-pair, needs to be filtered in order to ensure that we get "decent" routes (we are using duarouter and modifying cost of edges by a random factor)?

**Scalability**
- Vehicles are inserted one by one with Traci (not sure if that causes big overhead). Could be more efficient to write a xml file and insert them by reading the xml file. 

## 3. SUMO value retrieval

- Mechanism: TripInfo (output files)

**Reasoning**
- Tripinfo output is used instead of Traci because I am doing day-to-day learning (episodic learning). Decisions are only taken before simulation and we do not need mid-simulation control. We gain a lot of scalability with this approach.

**To verify**
- SUMO writes TripInfo output to `tripsInfoOutput.xml` (overwrites if already existed). I could include the timestamp as a prefix in the name of the file. That way I would have a history of all the files. Can be changed if needed

**Scalability**
- If I were to used Traci, `Object Variable Subscription` could make the use of Traci more scalable. Also libsumo is similar to Traci (mid-simulation control) but more efficient. 


## 4. RL

### 4.1. Reward space

- Reward: Negative travel time of the chosen route

**Pending**
- Incorporate irrationalities in the future...
- Other SUMO output parameters that also look interesting for the reward: 
  - getWaitingTime          # time stopped (traffic lights, jams)
  - getTimeLoss             # delay compared to free-flow travel  (recommended strongly by ChatGPT)
  - VehRoutes file output   # Output that contains time on each edge


**FINAL DECISION: BEHAVIORAL STATELESS RL (DAY-TO-DAY LEARNING). THE OTHER OPTIONS WERE POMDP OR MDP (during episode learning).**