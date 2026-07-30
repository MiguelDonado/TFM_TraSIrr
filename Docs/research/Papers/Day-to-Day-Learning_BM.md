## Goal
This file analyzes the study the paper does about the memory level and learning rate and its impact on the traffic and the network.

## Methodology
It studies the impact of the hyperparameters by considering 3 values.

## Metrics
The paper uses two metrics to measure if the model converges to equilibrium (UE).

1. **Flow of each route**
2. **Travel time of each route**. (it uses the BPR functions, so I guess that given the users on that route, it gives you back the travel time, 
   even though here it does not seem to take into account all the dynamic component given by the time).
   
## Networks
It uses 3 test networks.

- The first network has 3 paths and 1 OD.
- The second network has 1 OD (is a 3x3 grid network)
- The third network is bigger.

## Basic understanding of each hyperparameter
- Memory level: Higher values lead to more weight of past travel times when computing the ET and PT. Lower values the opposite.

## Simulations

### Memory level = 1 and learning rate = 0.3

#### First network
- Flow fluctuations very weak on 60th day. 
- Network flow converges to equilibrium on 210th day (travel time of all used paths is the same)
- It is illustrated in Figure 5.

#### Second network
- It also converges.
- It is illustrated in Figure 6.

#### Third network
- It also converges
- It is illustrated in Figure 7,8 (for two OD pairs)
- It is illustrated in Figure 9,10 (for other two OD pairs)

### Impact learning rate
- Figure 11, 12
- The larger the learning rate, the greater the adjustments on path probabilities, and hence greater flow fluctuations. 
  Memory is helpful to weaken the flow fluctuations
- When memory is not perfect, e.g. 0.6, higher values in the learning rate lead to cyclical oscillations in flow and travel time.
  (it approximately converges but then it does not).

### Impact memory level
- As it takes lower values the fluctuations in flow is bigger. 
- As it takes lower values the network flow does not converge to UE.
- Figure 13, 14
  
### Flow standard deviation (FSD)
- The flow standard deviation in the last 100 days, is a statistic used to measure flow deviations.
- Figure 15
  