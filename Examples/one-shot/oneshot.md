```sh
# https://sumo.dlr.de/docs/Demand/Dynamic_User_Assignment.html
# https://sumo.dlr.de/docs/Tools/Assign.html#one-shotpy

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/one-shot

# 2. Generate trips
one-shot.py -f 50 -n input.net.xml -t input.trips.xml

# 3. Run SUMO-GUI
sumo-gui -c one_shot_50.sumocfg
```