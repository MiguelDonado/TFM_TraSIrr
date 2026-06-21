from shutil import copy2

from config.config import config
from paths import (
    ACTIONS,
    AGENTS_OD,
    COST_LINKS,
    COST_MIN_PATHS,
    COST_PATHS,
    EDGEDATA_PARQUET,
    FLOWS_PATHS,
    MISSINGNESS_EDGE,
    MISSINGNESS_EPISODE,
    MISSINGNESS_INT,
    MISSINGNESS_REPORT,
    REFINED_RGAP,
    REFINED_RGAP_BY_OD,
    RGAP,
    RGAP_BY_OD,
    SHORTEST_PATHS_DIR,
    TRIPS_INFO_PARQUET,
    VEHROUTE_PARQUET,
    WEIGHTS_DIR,
    ACTIONS_duaIterate,
    COST_LINKS_duaIterate,
    COST_MIN_PATHS_duaIterate,
    COST_PATHS_duaIterate,
    EDGEDATA_duaIterate_PROCESSED,
    FLOWS_PATH_duaIterate,
    MISSINGNESS_duaIterate_EDGE,
    MISSINGNESS_duaIterate_EPISODE,
    MISSINGNESS_duaIterate_INT,
    MISSINGNESS_duaIterate_REPORT,
    OD_ROUTES_duaIterate,
    Path,
    REFINED_RGAP_BY_OD_duaIterate,
    REFINED_RGAP_duaIterate,
    RGAP_BY_OD_duaIterate,
    RGAP_duaIterate,
    ROUTES_duaIterate,
    SHORTEST_PATHS_DIR_duaIterate,
    TRIPS_INFO_PROCESSED_duaIterate,
    UNDESIRED_duaIterate_FILES,
    VEHROUTE_duaIterate_PROCESSED,
    WEIGHTS_DIR_duaIterate,
)

from .aggregation import compute_flows_odtp_k, compute_travel_time_paths_odtp_k
from .duaiterate import (
    call_duaIterate,
    compute_actions_table_duaIterate,
    compute_avg_tt_duaIterate,
    compute_od_routes_table_duaIterate,
    delete_duaIterate_folders,
    extract_routes_file_duaIterate,
    generate_edgedata_file,
    generate_meandata_file,
    generate_trips_file_duaIterate,
    process_edgedata_duaIterate,
    process_trips_info_duaIterate,
    process_vehroute_duaIterate,
    run_simulation_duaIterate,
)
from .rgap import (
    compute_rgap_and_refined_rgap,
    generate_demand_odt,
    generate_time_intervals_table,
    generate_trips_odt_file,
)
from .tdsp import run_tdsp_pipeline


def run_due_convergence_checks(scen, end_time, time_interval):
    _generate_generic_files_due_convergence()

    _check_due_convergence_duaIterate(
        scen, end_time=end_time, time_interval=time_interval
    )

    _check_due_convergence_BM(end_time=end_time, time_interval=time_interval)


def _generate_generic_files_due_convergence():
    end_time = config.end_time
    time_interval = config.time_interval

    # 1. Generate essential files
    ## Parquet
    generate_time_intervals_table(end_time, time_interval)
    generate_demand_odt()
    ## XML
    generate_trips_odt_file()


def _check_due_convergence_BM(end_time, time_interval):
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
    run_tdsp_pipeline(
        time_interval=time_interval,
        vehroute_file=VEHROUTE_PARQUET,
        edgedata_file=EDGEDATA_PARQUET,
        agents_od_file=AGENTS_OD,
        missingness_edge_file=MISSINGNESS_EDGE,
        missingness_episode_file=MISSINGNESS_EPISODE,
        missingness_interval_file=MISSINGNESS_INT,
        missingness_report_file=MISSINGNESS_REPORT,
        cost_links=COST_LINKS,
        weights_dir=WEIGHTS_DIR,
        shortest_path_dir=SHORTEST_PATHS_DIR,
        cost_min_paths=COST_MIN_PATHS,
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


def _check_due_convergence_duaIterate(scen, end_time, time_interval):
    ########################
    # Check duaIterate Rgap
    ########################
    print("--- duaIterate ---")

    # 1. Generate trips file used by duaIterate (only ODs, no routes)
    generate_trips_file_duaIterate(scen.agents)

    # 2. Execute duaIterate
    call_duaIterate(
        config.network, config.duaIterate_max_iterations, config.duaIterate_step_length
    )

    # 3. Run simulation
    if config.last_episode_gui_duaIterate:
        run_simulation_duaIterate(config.duaIterate_max_iterations)

    # 4. Extract routes file last iteration duaIterate
    routes_file = extract_routes_file_duaIterate(config.duaIterate_max_iterations)
    copy2(routes_file, ROUTES_duaIterate)
    # 5. Compute od routes table
    dict_agent_routes, od_routes = compute_od_routes_table_duaIterate(
        routes_file=routes_file, output_file=OD_ROUTES_duaIterate
    )

    # 6. Compute actions table
    compute_actions_table_duaIterate(
        agents=scen.agents,
        dict_agent_routes=dict_agent_routes,
        od_routes=od_routes,
        output_file=ACTIONS_duaIterate,
    )

    # 7. Compute the path flows for all origin–destination pairs and all time intervals across all episodes
    compute_flows_odtp_k(
        actions_path=ACTIONS_duaIterate, output_file=FLOWS_PATH_duaIterate
    )

    # 8. Process trips_info file
    process_trips_info_duaIterate(
        max_iterations=config.duaIterate_max_iterations,
        output_file=TRIPS_INFO_PROCESSED_duaIterate,
    )

    # 9. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k(
        actions_path=ACTIONS_duaIterate,
        trips_info_processed_path=TRIPS_INFO_PROCESSED_duaIterate,
        output_file=COST_PATHS_duaIterate,
    )

    # 10. Process vehroute duaIterate
    process_vehroute_duaIterate(
        max_iterations=config.duaIterate_max_iterations,
        output_file=VEHROUTE_duaIterate_PROCESSED,
    )

    # 11. Generate meandata_file
    meandata_duaIterate_file = generate_meandata_file(
        max_iterations=config.duaIterate_max_iterations
    )

    # 12. Generate edgedata file
    generate_edgedata_file(
        max_iterations=config.duaIterate_max_iterations,
        meandata_duaIterate_file=meandata_duaIterate_file,
    )

    # 13. Process edgedata file
    process_edgedata_duaIterate(
        max_iterations=config.duaIterate_max_iterations,
        output_file=EDGEDATA_duaIterate_PROCESSED,
    )

    ######
    # 14. TIME DEPENDENCE SHORTEST PATH
    run_tdsp_pipeline(
        time_interval=time_interval,
        vehroute_file=VEHROUTE_duaIterate_PROCESSED,
        edgedata_file=EDGEDATA_duaIterate_PROCESSED,
        agents_od_file=AGENTS_OD,
        missingness_edge_file=MISSINGNESS_duaIterate_EDGE,
        missingness_episode_file=MISSINGNESS_duaIterate_EPISODE,
        missingness_interval_file=MISSINGNESS_duaIterate_INT,
        missingness_report_file=MISSINGNESS_duaIterate_REPORT,
        cost_links=COST_LINKS_duaIterate,
        weights_dir=WEIGHTS_DIR_duaIterate,
        shortest_path_dir=SHORTEST_PATHS_DIR_duaIterate,
        cost_min_paths=COST_MIN_PATHS_duaIterate,
    )

    # Computation Rgap
    compute_rgap_and_refined_rgap(
        flow_paths=FLOWS_PATH_duaIterate,
        cost_paths=COST_PATHS_duaIterate,
        cost_min_paths=COST_MIN_PATHS_duaIterate,
        rgap_path=RGAP_duaIterate,
        refined_rgap_path=REFINED_RGAP_duaIterate,
        rgap_by_od_path=RGAP_BY_OD_duaIterate,
        refined_rgap_by_od_path=REFINED_RGAP_BY_OD_duaIterate,
    )

    # Compute and print mean tt duaIterate
    compute_avg_tt_duaIterate(max_iterations=config.duaIterate_max_iterations)

    ################
    # 15. Delete duaIterate folders
    delete_duaIterate_folders(config.duaIterate_max_iterations)
    for file in UNDESIRED_duaIterate_FILES:
        file.unlink()
