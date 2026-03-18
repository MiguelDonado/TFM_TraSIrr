```sh
# https://sumo.dlr.de/docs/Simulation/Output/RawDump.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/output/rawdump

# 2. Execute duarouter (shortest-path)
duarouter -n input.net.xml -r input.trips.xml -o output_shortest_path.routes.xml --write-costs

# 3. Run SUMO-GUI
sumo-gui -n input.net.xml -r output_shortest_path.routes.xml --delay 500 --step-length 0.1 --netstate-dump netstate.xml --output-prefix TIME 
```