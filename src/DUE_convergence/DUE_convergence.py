from shutil import copy2
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
    compute_od_routes_table_dueIterate,
    extract_routes_file_dueIterate,
    compute_actions_table_dueIterate,
    process_trips_info_dueiterate,
    process_vehroute_dueIterate,
    generate_meandata_file,
    generate_edgedata_file,
    process_edgedata_file,
)
from config.config import config

from paths import (
    Path,
    RGAP,
    RGAP_DUEITERATE,
    REFINED_RGAP,
    RGAP_BY_OD,
    REFINED_RGAP_BY_OD,
    REFINED_RGAP_DUEITERATE,
    RGAP_BY_OD_DUEITERATE,
    REFINED_RGAP_BY_OD_DUEITERATE,
    WEIGHTS_DIR,
    COST_MIN_PATHS_DUEITERATE,
    SHORTEST_PATHS_DIR_DUEITERATE,
    SHORTEST_PATHS_DIR,
    WEIGHTS_DIR_DUEITERATE,
    COST_LINKS,
    ACTIONS,
    ROUTES_DUEITERATE,
    COST_LINKS_DUEITERATE,
    ACTIONS_DUEITERATE,
    FLOWS_PATHS,
    TRIPS_INFO_PROCESSED_DUEITERATE,
    FLOWS_PATH_DUEITERATE,
    TRIPS_INFO_PARQUET,
    COST_PATHS,
    OD_ROUTES_DUEITERATE,
    TRIPS_INFO_PROCESSED_DUEITERATE,
    COST_PATHS_DUEITERATE,
    COST_MIN_PATHS,
    COST_MIN_PATHS_DUEITERATE,
    VEHROUTE_DUEITERATE_PROCESSED,
    EDGEDATA_DUEITERATE_PROCESSED,
    AGENTS_OD,
    MISSINGNESS_DUEITERATE_INT,
    MISSINGNESS_DUEITERATE_EDGE,
    MISSINGNESS_DUEITERATE_EPISODE,
    MISSINGNESS_DUEITERATE_REPORT,
    VEHROUTE_PARQUET,
    EDGEDATA_PARQUET,
    MISSINGNESS_EDGE,
    MISSINGNESS_EPISODE,
    MISSINGNESS_INT,
    MISSINGNESS_REPORT,
    UNDESIRED_DUEITERATE_FILES,
)


def run_DUE_convergence_checks(scen, end_time, time_interval):
    generate_generic_files_DUE_convergence()

    check_DUE_convergence_dueIterate(
        scen, end_time=end_time, time_interval=time_interval
    )

    check_DUE_convergence_BM(end_time=end_time, time_interval=time_interval)


def generate_generic_files_DUE_convergence():
    end_time = config.end_time
    time_interval = config.time_interval

    # 1. Generate essential files
    ## Parquet
    generate_time_intervals_table(end_time, time_interval)
    generate_demand_odt()

    ## XML
    generate_trips_odt_file()


def check_DUE_convergence_BM(end_time, time_interval):
    print("--- Bush-Mosteller algorithm ---")

    # 2. Compute the path flows for all origin–destination pairs and all time intervals across all episodes
    compute_flows_odtp_k(actions_path=ACTIONS, output_file=FLOWS_PATHS)

    # 3. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k(
        actions_path=ACTIONS,
        trips_info_processed_path=TRIPS_INFO_PARQUET,
        output_file=COST_PATHS,
    )

    # 4. TIME DEPENDENCE SHORTEST PATH
    # 4.1. Compute avg link travel time for all time intervals across all episodes
    compute_travel_time_links_t_k(
        time_interval=time_interval,
        network=config.network,
        threshold_density=config.threshold_density,
        output_file=COST_LINKS,
        agents_od_file=AGENTS_OD,
        vehroute_file=VEHROUTE_PARQUET,
        edgedata_file=EDGEDATA_PARQUET,
        missingness_edge_file=MISSINGNESS_EDGE,
        missingness_episode_file=MISSINGNESS_EPISODE,
        missingness_interval_file=MISSINGNESS_INT,
        missingness_report_file=MISSINGNESS_REPORT,
    )
    # 4.2. Transform the parquet travel time links file into a XML file for duarouter TDSP
    generate_weights_xmls(cost_links=COST_LINKS, weights_dir=WEIGHTS_DIR)
    # 4.3. Compute the time dependence shortest paths
    compute_time_dependent_shortest_paths(
        config.network,
        config.seed,
        weights_dir=WEIGHTS_DIR,
        shortest_path_dir=SHORTEST_PATHS_DIR,
    )
    # 4.4. Compute cost time dependence shortest paths for all time intervals and for all episodes
    compute_cost_min_paths_odt_k(
        time_interval=time_interval,
        cost_min_paths=COST_MIN_PATHS,
        shortest_path_dir=SHORTEST_PATHS_DIR,
    )
    # 4.5. Delete some files generated on DUE convergence check
    delete_files_DUE_convergence(
        weights_dir=WEIGHTS_DIR, shortest_paths_dir=SHORTEST_PATHS_DIR
    )

    # Computation Rgap
    compute_rgap_and_refined_rgap(
        flow_paths=FLOWS_PATHS,
        cost_paths=COST_PATHS,
        cost_min_paths=COST_MIN_PATHS,
        rgap_path=RGAP,
        refined_rgap_path=REFINED_RGAP,
        rgap_by_od_path=RGAP_BY_OD,
        refined_rgap_by_od_path=REFINED_RGAP_BY_OD,
    )


def check_DUE_convergence_dueIterate(scen, end_time, time_interval):
    ########################
    # Check dueIterate Rgap
    ########################
    print("--- dueIterate ---")

    # 1. Generate trips file used by dueIterate (only ODs, no routes)
    generate_trips_file_duaIterate(scen.agents)

    # 2. Execute dueIterate
    call_dueIterate(config.network, config.dueIterate_max_iterations)

    # 3. Run simulation
    if config.last_episode_gui_dueIterate:
        run_simulation_dueIterate(config.dueIterate_max_iterations)

    # 4. Extract routes file last iteration dueIterate
    routes_file = extract_routes_file_dueIterate(config.dueIterate_max_iterations)
    copy2(routes_file, ROUTES_DUEITERATE)
    # 5. Compute od routes table
    dict_agent_routes, od_routes = compute_od_routes_table_dueIterate(
        routes_file=routes_file, output_file=OD_ROUTES_DUEITERATE
    )

    # 6. Compute actions table
    compute_actions_table_dueIterate(
        agents=scen.agents,
        dict_agent_routes=dict_agent_routes,
        od_routes=od_routes,
        output_file=ACTIONS_DUEITERATE,
    )

    # 7. Compute the path flows for all origin–destination pairs and all time intervals across all episodes
    compute_flows_odtp_k(
        actions_path=ACTIONS_DUEITERATE, output_file=FLOWS_PATH_DUEITERATE
    )

    # 8. Process trips_info file
    process_trips_info_dueiterate(
        max_iterations=config.dueIterate_max_iterations,
        output_file=TRIPS_INFO_PROCESSED_DUEITERATE,
    )

    # 9. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k(
        actions_path=ACTIONS_DUEITERATE,
        trips_info_processed_path=TRIPS_INFO_PROCESSED_DUEITERATE,
        output_file=COST_PATHS_DUEITERATE,
    )

    # 10. Process vehroute dueIterate
    process_vehroute_dueIterate(
        max_iterations=config.dueIterate_max_iterations,
        output_file=VEHROUTE_DUEITERATE_PROCESSED,
    )

    # 11. Generate meandata_file
    meandata_dueiterate_file = generate_meandata_file(
        max_iterations=config.dueIterate_max_iterations
    )

    # 12. Generate edgedata file
    generate_edgedata_file(
        max_iterations=config.dueIterate_max_iterations,
        meandata_dueiterate_file=meandata_dueiterate_file,
    )

    # 13. Process edgedata file
    process_edgedata_file(
        max_iterations=config.dueIterate_max_iterations,
        output_file=EDGEDATA_DUEITERATE_PROCESSED,
    )

    ######
    # 14. TIME DEPENDENCE SHORTEST PATH
    # 14.1. Compute avg link travel time for all time intervals across all episodes
    compute_travel_time_links_t_k(
        time_interval=time_interval,
        network=config.network,
        threshold_density=config.threshold_density,
        output_file=COST_LINKS_DUEITERATE,
        agents_od_file=AGENTS_OD,
        vehroute_file=VEHROUTE_DUEITERATE_PROCESSED,
        edgedata_file=EDGEDATA_DUEITERATE_PROCESSED,
        missingness_edge_file=MISSINGNESS_DUEITERATE_EDGE,
        missingness_episode_file=MISSINGNESS_DUEITERATE_EPISODE,
        missingness_interval_file=MISSINGNESS_DUEITERATE_INT,
        missingness_report_file=MISSINGNESS_DUEITERATE_REPORT,
    )

    # 14.2. Transform the parquet travel time links file into a XML file for duarouter TDSP
    generate_weights_xmls(
        cost_links=COST_LINKS_DUEITERATE, weights_dir=WEIGHTS_DIR_DUEITERATE
    )

    # 14.3. Compute the time dependence shortest paths
    compute_time_dependent_shortest_paths(
        config.network,
        config.seed,
        weights_dir=WEIGHTS_DIR_DUEITERATE,
        shortest_path_dir=SHORTEST_PATHS_DIR_DUEITERATE,
    )

    # 14.4. Compute cost time dependence shortest paths for all time intervals and for all episodes
    compute_cost_min_paths_odt_k(
        time_interval=time_interval,
        shortest_path_dir=SHORTEST_PATHS_DIR_DUEITERATE,
        cost_min_paths=COST_MIN_PATHS_DUEITERATE,
    )

    # 14.5. Delete some files generated on DUE convergence check
    delete_files_DUE_convergence(
        weights_dir=WEIGHTS_DIR_DUEITERATE,
        shortest_paths_dir=SHORTEST_PATHS_DIR_DUEITERATE,
    )

    # Computation Rgap
    compute_rgap_and_refined_rgap(
        flow_paths=FLOWS_PATH_DUEITERATE,
        cost_paths=COST_PATHS_DUEITERATE,
        cost_min_paths=COST_MIN_PATHS_DUEITERATE,
        rgap_path=RGAP_DUEITERATE,
        refined_rgap_path=REFINED_RGAP_DUEITERATE,
        rgap_by_od_path=RGAP_BY_OD_DUEITERATE,
        refined_rgap_by_od_path=REFINED_RGAP_BY_OD_DUEITERATE,
    )

    ################
    # 15. Delete dueIterate folders
    delete_dueIterate_folders(config.dueIterate_max_iterations)
    for file in UNDESIRED_DUEITERATE_FILES:
        file.unlink()
