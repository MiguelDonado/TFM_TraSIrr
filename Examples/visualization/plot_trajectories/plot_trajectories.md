```sh
# https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html
# https://sumo.dlr.de/docs/Tools/Visualization.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/visualization/plot_trajectories

# 2. Compute shortest paths
duarouter -n input.net.xml -r input.trips.xml -o output_shortest_path.routes.xml

# 3. Example: Run simulation (default attributes)  (several agents) and parquet output
sumo-gui -n input.net.xml --fcd-output fcd-export.parquet --device.fcd.explicit agent_01,agent_02,agent_03 -r output_shortest_path.routes.xml

# 4. Plot time vs distance driven by each vehicle
plot_trajectories.py fcd-export.parquet -t td -o TimeDistance.png

# 5. Plot vehicles paths
plot_trajectories.py -t xy -o allLocations_output.png fcd-export.parquet
```
