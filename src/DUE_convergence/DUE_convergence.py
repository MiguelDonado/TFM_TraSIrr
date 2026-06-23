from shutil import copy2

from config.config import config
from config.paths import (
    ACTIONS,
    AGENTS_OD,
    BM_PATHS,
    DUA_EXTRA,
    DUA_PATHS,
    EDGEDATA_PARQUET,
    TRIPS_INFO_PARQUET,
    VEHROUTE_PARQUET,
    Path,
    UNDESIRED_duaIterate_FILES,
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
    compute_flows_odtp_k(actions_path=ACTIONS, output_file=BM_PATHS.flows_paths)

    # 3. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k(
        actions_path=ACTIONS,
        trips_info_processed_path=TRIPS_INFO_PARQUET,
        output_file=BM_PATHS.cost_paths,
    )

    # 4. TIME DEPENDENCE SHORTEST PATH
    run_tdsp_pipeline(
        time_interval=time_interval,
        vehroute_file=VEHROUTE_PARQUET,
        edgedata_file=EDGEDATA_PARQUET,
        agents_od_file=AGENTS_OD,
        missingness_edge_file=BM_PATHS.missingness_edge,
        missingness_episode_file=BM_PATHS.missingness_episode,
        missingness_interval_file=BM_PATHS.missingness_int,
        missingness_report_file=BM_PATHS.missingness_report,
        cost_links=BM_PATHS.cost_links,
        weights_dir=BM_PATHS.weights_dir,
        shortest_path_dir=BM_PATHS.shortest_paths_dir,
        cost_min_paths=BM_PATHS.cost_min_paths,
    )

    # Computation Rgap
    compute_rgap_and_refined_rgap(
        flow_paths=BM_PATHS.flows_paths,
        cost_paths=BM_PATHS.cost_paths,
        cost_min_paths=BM_PATHS.cost_min_paths,
        rgap_path=BM_PATHS.rgap,
        refined_rgap_path=BM_PATHS.refined_rgap,
        rgap_by_od_path=BM_PATHS.rgap_by_od,
        refined_rgap_by_od_path=BM_PATHS.refined_rgap_by_od,
    )


def _check_due_convergence_duaIterate(scen, end_time, time_interval):
    ########################
    # Check duaIterate Rgap
    ########################
    print("--- duaIterate ---")

    # 1. Generate trips file used by dueIterate (only ODs, no routes)
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
    copy2(routes_file, DUA_EXTRA.routes)
    # 5. Compute od routes table
    dict_agent_routes, od_routes = compute_od_routes_table_duaIterate(
        routes_file=routes_file, output_file=DUA_EXTRA.od_routes
    )

    # 6. Compute actions table
    compute_actions_table_duaIterate(
        agents=scen.agents,
        dict_agent_routes=dict_agent_routes,
        od_routes=od_routes,
        output_file=DUA_EXTRA.actions,
    )

    # 7. Compute the path flows for all origin–destination pairs and all time intervals across all episodes
    compute_flows_odtp_k(
        actions_path=DUA_EXTRA.actions, output_file=DUA_PATHS.flows_paths
    )

    # 8. Process trips_info file
    process_trips_info_duaIterate(
        max_iterations=config.duaIterate_max_iterations,
        output_file=DUA_EXTRA.trips_info_processed,
    )

    # 9. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k(
        actions_path=DUA_EXTRA.actions,
        trips_info_processed_path=DUA_EXTRA.trips_info_processed,
        output_file=DUA_PATHS.cost_paths,
    )

    # 10. Process vehroute duaIterate
    process_vehroute_duaIterate(
        max_iterations=config.duaIterate_max_iterations,
        output_file=DUA_EXTRA.vehroute_processed,
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
        output_file=DUA_EXTRA.edgedata_processed,
    )

    ######
    # 14. TIME DEPENDENCE SHORTEST PATH
    run_tdsp_pipeline(
        time_interval=time_interval,
        vehroute_file=DUA_EXTRA.vehroute_processed,
        edgedata_file=DUA_EXTRA.edgedata_processed,
        agents_od_file=AGENTS_OD,
        missingness_edge_file=DUA_PATHS.missingness_edge,
        missingness_episode_file=DUA_PATHS.missingness_episode,
        missingness_interval_file=DUA_PATHS.missingness_int,
        missingness_report_file=DUA_PATHS.missingness_report,
        cost_links=DUA_PATHS.cost_links,
        weights_dir=DUA_PATHS.weights_dir,
        shortest_path_dir=DUA_PATHS.shortest_paths_dir,
        cost_min_paths=DUA_PATHS.cost_min_paths,
    )

    # Computation Rgap
    compute_rgap_and_refined_rgap(
        flow_paths=DUA_PATHS.flows_paths,
        cost_paths=DUA_PATHS.cost_paths,
        cost_min_paths=DUA_PATHS.cost_min_paths,
        rgap_path=DUA_PATHS.rgap,
        refined_rgap_path=DUA_PATHS.refined_rgap,
        rgap_by_od_path=DUA_PATHS.rgap_by_od,
        refined_rgap_by_od_path=DUA_PATHS.refined_rgap_by_od,
    )

    # Compute and print mean tt duaIterate
    compute_avg_tt_duaIterate(max_iterations=config.duaIterate_max_iterations)

    ################
    # 15. Delete duaIterate folders
    delete_duaIterate_folders(config.duaIterate_max_iterations)
    for file in UNDESIRED_duaIterate_FILES:
        file.unlink()
