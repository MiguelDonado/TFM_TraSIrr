```sh
# https://sumo.dlr.de/docs/Simulation/SaveAndLoad.html
# Used for the warm-up problem that Mari Paz told me

# 1. Change directory
cd /home/miguel/6.Projects/Thesis/Examples/SaveAndLoad

# 2. Saved state
sumo -c basic.cfg --route-files routes.rou.xml --save-state.times 600 --save-state.files /home/miguel/6.Projects/Thesis/Examples/SaveAndLoad/my_state_600.00.xml

# 3. Load state
sumo-gui -c basic.cfg --load-state my_state_600.00.xml -r routes.rou.xml
```