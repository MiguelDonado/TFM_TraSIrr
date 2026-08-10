# Meeting 18/03/2026

## Differences of Human driver agent or RL agent

- Human drivers follow a **policy** (a decision strategy). That policy is based on **past experience**. But human experience is limited and biased. Humans tend to **exploit** familiar routes. They rarely **explore** new routes. Because of this, their policy may be suboptimal.

- A DRL model (like DQN) can learn a **better policy** by systematically exploring routes. Once trained, it approximates the **true value of actions and states**. Therefore, it can suggest better routing decisions. DQN explicitly balances: **Exploration** (trying new routes) **Exploitation** (using known best routes) This allows it to discover potentially better paths.

## Relevant images

![image-20260318134804549](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318134804549.png)

Figura 0: Pagina 76 de la thesis

Flow:

1. We get an observation from the environment
2. Vehicle pass the observation to the NN and takes an action
3. After the action, we get a new observation and a reward
4. Go back to step 1

![image-20260318135114526](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318135114526.png)

Figura 1: Pagina 78 de la thesis

1. In Decision zone, it passes the observation to the NN, does a forward pass, and gets an action
2. Executes the action, when it gets to the new edge, it computes new observation and reward

![image-20260318135321020](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318135321020.png)

Figura 2: Pagina 78 de la thesis

![image-20260318135450710](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318135450710.png)

Figura 3: Pagina 80 de la thesis

1. In decision zone vehicle gets observation, and pass it to the NN (feedforward pass). Then it takes an action
2. Vehicle applies the action, gets to new edge and computes reward and new observation
3. Stores transition

![image-20260318134833091](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318134833091.png



![image-20260318122737683](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318122737683.png)

Figura 4: Pagina 73 de la thesis

<img src="/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318122751360.png" alt="image-20260318122751360" style="zoom:150%;" />

Figura 5: Pagina 90 de la thesis

**Pseudocode:**

1. Initialize scenario class

   1. Convert map .osm or use SUMO network (.net.xml) 
   2. Use vType function to create a VTypeDistribution or use default.
   3. Generate trips (depends on nºvehicles and duration)
   4. Generate routes (using shortest-path)
   5. Generate configuration file

2. Initialize environment class

   1. Get all network info (edges and its connections)
   2. Get euclidean distance of all the edges to destination

3. Initialize agent class

   1. Build NN structure (network dependent)

4. Start training (N number of episodes)            # episode finish when agent get to destination

   1. For each episode 

      1. Reset environment (.reset())

         1. Add vehicle (.add_veh())
         2. Run simulation until vehicle is IN ZONE (.run_simulation())
            1. Advances one step, and check status. 
            2. Return when vehicle is IN ZONE. (Return state)

      2. Loop until agent gets to destination

         **(BEGINNING LOOP)**

         1. Remember, agent was IN ZONE, so now it has to choose an action (feedforward pass) 
         2. Call run_simulation() and apply action. Keeps simulating inside run_simulation() until NEW
            1. After apply action, vehicle is gonna be several steps on NONE (while is turning)
            2. When vehicle in NEW, return run_simulation (computed reward and new state)

         3. Store transition (Ot,At,Rt,Ot+1)
         4. Because not enough stored transitions, I cannot learn yet
         5. Call run_simulation until DONE or IN_ZONE
            1. If I get DONE, episodio is finished **(EXIT POINT)**
            2. If I get IN_ZONE, go back to **(BEGINNING LOOP)**

## Interaction between driver and RL agent (goal of Song)

![image-20260318134557270](/home/miguel/.var/app/io.typora.Typora/config/Typora/typora-user-images/image-20260318134557270.png)

## Questions