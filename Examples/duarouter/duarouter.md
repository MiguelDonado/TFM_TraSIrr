```sh
# https://sumo.dlr.de/docs/Demand/Shortest_or_Optimal_Path_Routing.html
# https://sumo.dlr.de/docs/duarouter.html


# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/duarouter

# 2. Execute duarouter (shortest-path)
duarouter -n input.net.xml -r input.trips.xml -o output_shortest_path.routes.xml --write-costs

# 3. Run SUMO-GUI
sumo-gui -n input.net.xml -r output_shortest_path.routes.xml --delay 500 --step-length 0.1

# 4. Execute duarouter (DUE)
duaIterate.py --disable-summary --disable-tripinfos -n input.net.xml -t input.trips.xml -l 100 --first-step 0 --last-step 10 -o Output/

# 5. Run SUMO-GUI
sumo-gui -c 009/iteration_009.sumocfg --delay 500 --step-length 0.1
```