This YAML contains all the chosen values of the hyperparameters
/home/miguel/6.Projects/Thesis/experiments/developer_modes/production.yaml

### Non-study hyperparameters

1. Perform sensitivity analysis on hyperparameters that directly influence the learning algorithm
   or the r-gap values:
   - min_distance_factor
   - random_factor
   - n_routes_per_od
   - threshold_density
   - warm_up_time
   - fixed_time_min
   - fixed_time_interval (yes)
  
2. Fix implementation/computational hyperparameters using reasonable choices (without the need to 
   perform sensitivity analysis), unless evidence that they materially affect the results:
   - network
   - tolerance_demand_calibration
   - max_size_od_space
   - simulation_time
   - routing_algorithm
   - max_attempts
   - n_threads
   - max_episodes
   - tolerance_stopping_rule
   - k_no_change
   - heuristic_veh_km_hour_initial_guess
   - fringe_factor
   - duaIterate_max_iterations
   - duaIterate_step_length

The first two points are relative to fixing non-study hyperparameters.

A principle of experimental design is to fix parameters in an order that respects their dependencies. Every parameter should be evaluated under the conditions in which it will actually be used. If one parameter depends on another, the latter should be fixed first.

In experiment evaluation, Im only gonna analyze Sioux Falls network.
In methodology or wherever is needed to illustrate concepts I will use toy network as well.

### Hyperparameters that will be investigated in research questions:
   - seed
   - learning_rate
   - memory_rate
   - target_congestion_metric

