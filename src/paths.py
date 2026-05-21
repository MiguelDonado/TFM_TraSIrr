from pathlib import Path

from config.config import config

# Root of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Folders
SUMO_DIR = BASE_DIR / "sumo"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
INTERNAL_DATA_DIR = BASE_DIR / "data" / "internal"
FIGURES_DIR = BASE_DIR / "output" / "figures"

DUE_DIR = BASE_DIR / "data" / "DUE"
TDSP_DIR = DUE_DIR / "TDSP"
MISSINGNESS_DIR = DUE_DIR / "missingness"
WEIGHTS_DIR = TDSP_DIR / "weights"
SHORTEST_PATHS_DIR = TDSP_DIR / "shortest_paths"
DUEITERATE_DIR = DUE_DIR / "dueIterate"

# Parquet files (outputs that will be analyzed in R)
STATISTICS_PROCESSED = PROCESSED_DATA_DIR / "statistics.parquet"
VEHROUTE_PROCESSED = PROCESSED_DATA_DIR / "vehroute.parquet"
TRIPS_INFO_PROCESSED = PROCESSED_DATA_DIR / "trips_info.parquet"
FCD_PROCESSED = PROCESSED_DATA_DIR / "fcd.parquet"
EDGEDATA_PROCESSED = PROCESSED_DATA_DIR / "edgedata.parquet"

# Internal data
AGENTS_OD = INTERNAL_DATA_DIR / "agents_od.parquet"
OD_ROUTES = INTERNAL_DATA_DIR / "od_routes.parquet"
ACTIONS = INTERNAL_DATA_DIR / "actions.parquet"
REWARDS = INTERNAL_DATA_DIR / "rewards.parquet"
BM_RESULTS = INTERNAL_DATA_DIR / "BM_results.parquet"
TIMES_INTERVAL = INTERNAL_DATA_DIR / "times_interval.parquet"
FREE_FLOW_TRAVEL_TIMES = INTERNAL_DATA_DIR / "free_flow_travel_times.parquet"

# DUE
FLOWS_PATHS = DUE_DIR / "flows_paths_odtp_k.parquet"
COST_PATHS = DUE_DIR / "costs_paths_odtp_k.parquet"
DEMAND_ODT = DUE_DIR / "demand_odt.parquet"

# TDSP (Time-dependence shortest path related files)
COST_LINKS = TDSP_DIR / "costs_links_t_k.parquet"
TRIPS_TDSP = TDSP_DIR / "trips" / "trips.xml"
COST_MIN_PATHS = TDSP_DIR / "costs_min_paths_t_k.parquet"
MISSINGNESS_INT = MISSINGNESS_DIR / "missingness_by_int.parquet"
MISSINGNESS_EDGE = MISSINGNESS_DIR / "missingness_by_edge.parquet"
MISSINGNESS_EPISODE = MISSINGNESS_DIR / "missingness_by_episode.parquet"
MISSINGNESS_REPORT = MISSINGNESS_DIR / "missingness_report.txt"
TRIPS_DUEITERATE = DUEITERATE_DIR / "trips_dueIterate.xml"
OD_ROUTES_DUEITERATE = DUEITERATE_DIR / "od_routes_dueiterate.parquet"
ACTIONS_DUEITERATE = DUEITERATE_DIR / "actions_dueiterate.parquet"
FLOWS_PATH_DUEITERATE = DUEITERATE_DIR / "flows_path_dueiterate.parquet"
TRIPS_INFO_PROCESSED_DUEITERATE = (
    DUEITERATE_DIR / "trips_info_processed_duaiterate.parquet"
)
COST_PATHS_DUEITERATE = DUEITERATE_DIR / "costs_paths_odtp_k_dueIterate.parquet"

# Output files
EDGEDATA = RAW_DATA_DIR / "edgedata.xml"
STATISTICS = RAW_DATA_DIR / "statistics.xml"
TRIPS_INFO = RAW_DATA_DIR / "tripsinfo.xml"
VEHROUTE = RAW_DATA_DIR / "vehroute.xml"
FCD = RAW_DATA_DIR / "fcd-export.xml"
SUMMARY = RAW_DATA_DIR / "summary.xml"
OD_MATRIX_INTERVALS = PROCESSED_DATA_DIR / "od_matrix_intervals.csv"
OD_MATRIX_TOTAL = PROCESSED_DATA_DIR / "od_matrix_total.csv"

# Files
MAP = config.network  # For using (NETEDIT)
NET = SUMO_DIR / "net" / "net.net.xml"  # For saving (if OSM file is provided)
ROUTES = SUMO_DIR / "routes" / "routes.rou.xml"
SUMO_CONF = SUMO_DIR / "config" / "basic.cfg"
YAML_CONF = BASE_DIR / "src" / "config" / "config.yaml"
# Additional file used when generating file edgedata.xml
MEANDATA = SUMO_DIR / "config" / "meandata.xml"

# Demand calibration
TRIPS_DEMAND_CALIBRATION = SUMO_DIR / "demand_calibration" / "trips.xml"
ROUTES_DEMAND_CALIBRATION = SUMO_DIR / "demand_calibration" / "routes.xml"
SUMO_CONF_DEMAND_CALIBRATION = SUMO_DIR / "demand_calibration" / "basic.cfg"

# File automatically generated (used to delete it)
UNDESIRED_ROUTE_FILE = BASE_DIR / "routes.rou.xml"
