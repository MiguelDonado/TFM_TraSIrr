from .utils import (
    compute_flows_odtp_k,
    compute_travel_time_paths_odtp_k,
    compute_travel_time_links_t_k,
    compute_time_dependent_shortest_paths,
    compute_cost_min_paths_odt_k,
    generate_weights_xmls,
    generate_trips_odt_file,
    generate_time_intervals_table,
    delete_files_DUE_convergence,
    compute_rgap_and_refined_rgap,
    generate_demand_odt,
    call_dueIterate,
    generate_trips_file_duaIterate,
    run_simulation_dueIterate,
    delete_dueIterate_folders,
    compute_od_routes_table,
    extract_routes_file_dueiterate,
    compute_actions_table,
)
from config.config import config

from paths import Path


def generate_generic_files_DUE_convergence():
    end_time = config.end_time
    time_interval = config.time_interval

    # 1. Generate essential files
    ## Parquet
    generate_time_intervals_table(end_time, time_interval)
    generate_demand_odt()

    ## XML
    generate_trips_odt_file()


def check_DUE_convergence():
    end_time = config.end_time
    time_interval = config.time_interval

    # 2. Compute the path flows for all origin–destination pairs and all time intervals across all episodes
    compute_flows_odtp_k()

    # 3. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k()

    # 4. TIME DEPENDENCE SHORTEST PATH
    # 4.1. Compute avg link travel time for all time intervals across all episodes
    compute_travel_time_links_t_k(
        network=config.network,
        time_interval=time_interval,
        threshold_density=config.threshold_density,
    )
    # 4.2. Transform the parquet travel time links file into a XML file for duarouter TDSP
    generate_weights_xmls()
    # 4.3. Compute the time dependence shortest paths
    compute_time_dependent_shortest_paths(config.network, config.seed)
    # 4.4. Compute cost time dependence shortest paths for all time intervals and for all episodes
    compute_cost_min_paths_odt_k(time_interval)
    # 4.5. Delete some files generated on DUE convergence check
    delete_files_DUE_convergence()

    # Computation Rgap
    rgap, redefined_rgap = compute_rgap_and_refined_rgap()
    print("--- Bush-Mosteller algorithm ---")
    print(rgap)
    print(redefined_rgap)


def check_dueIterate(scen):
    ########################
    # Check dueIterate Rgap
    ########################
    print("--- dueIterate ---")

    # 1. Generate trips file used by dueIterate (only ODs, no routes)
    generate_trips_file_duaIterate(scen.agents)

    # 2. Execute dueIterate
    call_dueIterate(config.network, config.dueIterate_max_iterations)

    # 3. Run simulation
    run_simulation_dueIterate(config.dueIterate_max_iterations)

    # 4. Extract routes file last iteration dueIterate
    routes_file = extract_routes_file_dueiterate(config.dueIterate_max_iterations)

    # 5. Compute od routes table
    dict_agent_routes, od_routes = compute_od_routes_table(
        scen.unique_ods, routes_file, config.dueIterate_max_iterations
    )

    # 6. Compute actions table
    compute_actions_table(scen.agents, dict_agent_routes, od_routes)

    # 7. Delete dueIterate folders
    delete_dueIterate_folders(config.dueIterate_max_iterations)

    # # COMPUTATION RGAP
