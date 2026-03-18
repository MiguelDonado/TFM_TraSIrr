```sh
# https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/output/tripinfo

# 2. Execute duarouter (shortest-path)
duarouter -n input.net.xml -r input.trips.xml -o output_shortest_path.routes.xml --write-costs

# 3. Run SUMO-GUI
sumo-gui -n input.net.xml -r output_shortest_path.routes.xml --delay 500 --step-length 0.1 --tripinfo-output tripinfo-output.xml --statistic-output statistics-output.xml --output-prefix TIME 
```