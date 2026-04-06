https://sumo.dlr.de/docs/Simulation/Output/index.html

### Section: Commandline Output (step-log)
Sumo will print some "heartbeat" information to indicate that it is still running. The following information will be printed every 100 simulation steps:
**Example:**
`Step #0.00 (6ms ~= 166.67*RT, ~166.67UPS, TraCI: 70234ms, vehicles TOT 1 ACTStep #100.00 (0ms ?*RT. ?UPS, TraCI: 0ms, vehicles TOT 34 ACT 16 BUF 16)`    
- Step #0.00: Current simulation time
- 6ms: Duration of the latest step
- 166.67*RT: 
- ~166.67UPS: 
- TraCI: 70234ms: time spent with TraCI processing in the current step (including external script)
- vehicles TOT 1: number of vehicles that departed so far
- ACT 16: number of currently running vehicles
- BUF 16: number of vehicles with delayed insertion