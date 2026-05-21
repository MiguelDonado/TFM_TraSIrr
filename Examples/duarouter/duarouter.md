```sh
# https://sumo.dlr.de/docs/Demand/Shortest_or_Optimal_Path_Routing.html
# https://sumo.dlr.de/docs/duarouter.html
º

# 1. Change directory
cd /home/miguel/6.Projects/Thesis/Examples/duarouter

# 2. Execute duarouter (shortest-path)
duarouter -n input.net.xml -r input.trips.xml -o output_shortest_path.routes.xml --write-costs

# 2.1 Execute duarouter (shortest-path) with Thesis example
duarouter -n /home/miguel/6.Projects/Thesis/sumo/net/Popular/Sioux_Falls.net.xml -r thesis.trips.xml --alternatives-output test.xml   -o thesis.routes.xml

# 3. Run SUMO-GUI
sumo-gui -n input.net.xml -r output_shortest_path.routes.xml --delay 500 --step-length 0.1

# 4. Execute duarouter (DUE)
duaIterate.py -n input.net.xml -t input.trips.xml --last-step 10 sumo--vehroute-output vehroute.xml sumo--vehroute-output.exit-times true

# 5. Run SUMO-GUI
sumo-gui -c 009/iteration_009.sumocfg --delay 500 --step-length 0.1
```