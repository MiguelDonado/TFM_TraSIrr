```sh
# https://sumo.dlr.de/docs/marouter.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/marouter

# 2. Generate trips
# -i: Iterations
marouter \
-n input.net.xml \
-r input.trips.xml \
--assignment-method SUE \
--route-choice-method logit \
--paths 3 \
-i 20 \
-o routes.xml

# 3. Run SUMO-GUI
sumo-gui -n input.net.xml -r routes.xml
```

