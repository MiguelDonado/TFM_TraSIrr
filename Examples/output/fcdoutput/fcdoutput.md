```sh
# https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html
# https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#devices   (# For devices documentacion, in section devices)

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/output/fcdoutput

# 2. Compute shortest paths
duarouter -n input.net.xml -r input.trips.xml -o output_shortest_path.routes.xml

# 3. Example: Run simulation (only write attribute "x,y" instead of default attributes)  (several agents) and parquet output
sumo-gui -n input.net.xml --fcd-output fcd-export.parquet --device.fcd.explicit agent_01,agent_02,agent_03 --fcd-output.attributes x,y -r output_shortest_path.routes.xml
```
