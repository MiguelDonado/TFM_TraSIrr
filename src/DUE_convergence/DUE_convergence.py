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
)


def check_DUE_convergence():
    # 1. Generate essential files
    ## Parquet
    generate_time_intervals_table()

    ## XML
    generate_trips_odt_file()

    # 2. Compute the path flows for all origin–destination pairs and all time intervals across all episodes
    compute_flows_odtp_k()

    # 3. Compute avg path travel times for all od-pairs and all time intervals across all episodes
    compute_travel_time_paths_odtp_k()

    # 4. TIME DEPENDENCE SHORTEST PATH
    # 4.1. Compute avg link travel time for all time intervals across all episodes
    compute_travel_time_links_t_k()
    # 4.2. Transform the parquet travel time links file into a XML file for duarouter TDSP
    generate_weights_xmls()
    # 4.3. Compute the time dependence shortest paths
    compute_time_dependent_shortest_paths()
    # 4.4. Compute cost time dependence shortest paths for all time intervals and for all episodes
    compute_cost_min_paths_odt_k()
    # 4.5. Delete some files generated on DUE convergence check
    delete_files_DUE_convergence()
