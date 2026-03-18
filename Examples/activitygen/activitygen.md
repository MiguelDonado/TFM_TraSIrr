```sh
# https://sumo.dlr.de/docs/Demand/Activity-based_Demand_Generation.html
# https://sumo.dlr.de/docs/activitygen.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/activitygen

# 2. Generate trips
activitygen --net-file input.net.xml --stat-file activitygen-example.stat.xml --output-file routes.xml --random

# 3. Run SUMO-GUI
sumo-gui -n input.net.xml -r routes.xml
```

