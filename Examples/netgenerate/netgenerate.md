```sh
# https://sumo.dlr.de/docs/Networks/Abstract_Network_Generation.html

# 1. Change directory
cd /home/miguel/6.Projects/Thesis/sumo/net/random

# 2. Generate first random network
# Explanation arguments:
# --rand: Generates a random network
# --rand.grid: Additional grid structure is enforced during random network generation
# --seed: Reproducibility
# --rand.iterations: The higher it is, the bigger the network
# --rand.connectivity: Probability nodes are connected
# --rand.min-distance: Minimum distance among nodes
# --rand.max-distance: Maximum distance among nodes
# --rand.min-angle: Minimum angle between edges that go the same node
# --rand.bidi-probability: Chance a street has opposite direction
# --default-junction-type: All intersections will have traffic lights
netgenerate --rand --rand.grid -o FirstRandom.net.xml \
    --seed 42 \
    --rand.iterations=350 \
    --rand.connectivity=0.85 \
    --rand.min-distance=80 \
    --rand.max-distance=250 \
    --rand.bidi-probability=0.7 \
    --rand.min-angle=25 \
    --default-junction-type=traffic_light
```

