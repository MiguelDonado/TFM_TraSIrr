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

## Suggested networks for DUE
- Avoid perfectly symmetric networks. 
- Example:
  - Instead, build a **4-node network with two parallel routes that differ slightly** in length or capacity. It will have:
    - one OD pair,
    - two possible paths
      - **Route 1:** shorter but with a traffic light/priority junction (lower effective capacity),
      - **Route 2:** longer but uninterrupted.
    - At low demand, everyone prefers Route 1 because it's shorter. As demand increases, queues develop at the traffic light, making Route 2 competitive. The equilibrium then shifts naturally, giving your algorithm something meaningful to converge to.

## Congestion in SUMO
- Congestion only appears when the demand exceeds the discharge capacity of some bottleneck
- Common bottlenecks:
  - Traffic lights
  - Priority junctions (vehicles yield)
  - Lane drops
  - Merges
  - Turns
