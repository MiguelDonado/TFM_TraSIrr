from pathlib import Path

from config.config import config

# ============================================================
# Project root
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# Main folders
# ============================================================

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
INTERNAL_DATA_DIR = DATA_DIR / "internal"
DUE_DATA_DIR = DATA_DIR / "DUE"
DUE_DATA_BM = DUE_DATA_DIR / "BM"
DUE_DATA_dueIterate = DUE_DATA_DIR / "dueIterate"

FIGURES_DIR = BASE_DIR / "output" / "figures"

SUMO_DIR = BASE_DIR / "sumo"


# ============================================================
# SUMO files
# ============================================================

NET = SUMO_DIR / "net" / "net.net.xml"  # netconvert script
ROUTES = SUMO_DIR / "routes" / "routes.rou.xml"

SUMO_CONF = SUMO_DIR / "config" / "basic.sumocfg"
GUI_SETTINGS = SUMO_DIR / "config" / "gui_settings.xml"  # Template
MEANDATA = SUMO_DIR / "config" / "meandata.xml"

MAP = config.network
YAML_CONF = BASE_DIR / "src" / "config" / "config.yaml"  # Is not SUMO file


# ============================================================
# Demand calibration
# ============================================================

DEMAND_CALIBRATION_DIR = SUMO_DIR / "demand_calibration"

TRIPS_DEMAND_CALIBRATION = DEMAND_CALIBRATION_DIR / "trips.xml"

ROUTES_DEMAND_CALIBRATION = DEMAND_CALIBRATION_DIR / "routes.xml"

SUMO_CONF_DEMAND_CALIBRATION = DEMAND_CALIBRATION_DIR / "basic.cfg"

# ============================================================
# SUMO raw outputs
# ============================================================

EDGEDATA_XML = RAW_DATA_DIR / "edgedata.xml"
STATISTICS_XML = RAW_DATA_DIR / "statistics.xml"
TRIPS_INFO_XML = RAW_DATA_DIR / "tripsinfo.xml"
VEHROUTE_XML = RAW_DATA_DIR / "vehroute.xml"
FCD_XML = RAW_DATA_DIR / "fcd-export.xml"
SUMMARY_XML = RAW_DATA_DIR / "summary.xml"


# ============================================================
# Processed outputs
# ============================================================

EDGEDATA_PARQUET = PROCESSED_DATA_DIR / "edgedata.parquet"
STATISTICS_PARQUET = PROCESSED_DATA_DIR / "statistics.parquet"
TRIPS_INFO_PARQUET = PROCESSED_DATA_DIR / "trips_info.parquet"
VEHROUTE_PARQUET = PROCESSED_DATA_DIR / "vehroute.parquet"
FCD_PARQUET = PROCESSED_DATA_DIR / "fcd.parquet"

OD_MATRIX_INTERVALS = PROCESSED_DATA_DIR / "od_matrix_intervals.csv"
OD_MATRIX_TOTAL = PROCESSED_DATA_DIR / "od_matrix_total.csv"


# ============================================================
# Internal agents data
# ============================================================

AGENTS_OD = INTERNAL_DATA_DIR / "agents_od.parquet"
OD_ROUTES = INTERNAL_DATA_DIR / "od_routes.parquet"
DEMAND_ODT = DUE_DATA_BM / "demand_odt.parquet"

ACTIONS = INTERNAL_DATA_DIR / "actions.parquet"
REWARDS = INTERNAL_DATA_DIR / "rewards.parquet"
BM_RESULTS = INTERNAL_DATA_DIR / "BM_results.parquet"

# ============================================================
# Internal environment data
# ============================================================

FREE_FLOW_TRAVEL_TIMES = INTERNAL_DATA_DIR / "free_flow_travel_times.parquet"
TIMES_INTERVAL = INTERNAL_DATA_DIR / "times_interval.parquet"

# ============================================================
# DUE data BM-specific
# ============================================================

TDSP_DIR = DUE_DATA_BM / "TDSP"
WEIGHTS_DIR = TDSP_DIR / "weights"
SHORTEST_PATHS_DIR = TDSP_DIR / "shortest_paths"

FLOWS_PATHS = DUE_DATA_BM / "flows_paths_odtp_k.parquet"
COST_PATHS = DUE_DATA_BM / "costs_paths_odtp_k.parquet"
COST_LINKS = TDSP_DIR / "costs_links_t_k.parquet"
COST_MIN_PATHS = TDSP_DIR / "costs_min_paths_t_k.parquet"

# All grid of combinations odt, to generate TDSP for all of them
TRIPS_TDSP = TDSP_DIR / "trips" / "trips.xml"

# =============
# Missingness BM-specific
# =============

MISSINGNESS_DIR = DUE_DATA_BM / "missingness"
MISSINGNESS_INT = MISSINGNESS_DIR / "missingness_by_int.parquet"
MISSINGNESS_EDGE = MISSINGNESS_DIR / "missingness_by_edge.parquet"
MISSINGNESS_EPISODE = MISSINGNESS_DIR / "missingness_by_episode.parquet"
MISSINGNESS_REPORT = MISSINGNESS_DIR / "missingness_report.txt"

# ============================================================
# DUE data dueIterate-specific
# ============================================================
TDSP_DIR_DUEITERATE = DUE_DATA_dueIterate / "TDSP"
WEIGHTS_DIR_DUEITERATE = TDSP_DIR_DUEITERATE / "weights"
SHORTEST_PATHS_DIR_DUEITERATE = TDSP_DIR_DUEITERATE / "shortest_paths"

FLOWS_PATH_DUEITERATE = DUE_DATA_dueIterate / "flows_path_dueiterate.parquet"
COST_PATHS_DUEITERATE = DUE_DATA_dueIterate / "costs_paths_odtp_k_dueIterate.parquet"
COST_LINKS_DUEITERATE = TDSP_DIR_DUEITERATE / "costs_links_dueiterate_t_k.parquet"
COST_MIN_PATHS_DUEITERATE = (
    DUE_DATA_dueIterate / "costs_min_paths_odtp_k_dueIterate.parquet"
)
TRIPS_DUEITERATE = TDSP_DIR_DUEITERATE / "trips_dueIterate.xml"
OD_ROUTES_DUEITERATE = DUE_DATA_dueIterate / "od_routes_dueiterate.parquet"
ACTIONS_DUEITERATE = DUE_DATA_dueIterate / "actions_dueiterate.parquet"
TRIPS_INFO_PROCESSED_DUEITERATE = (
    DUE_DATA_dueIterate / "trips_info_processed_duaiterate.parquet"
)
VEHROUTE_DUEITERATE_PROCESSED = DUE_DATA_dueIterate / "vehroute_dueiterate.parquet"
EDGEDATA_DUEITERATE_PROCESSED = (
    DUE_DATA_dueIterate / "edgedata" / "edgedata_dueiterate.parquet"
)

ROUTES_DUEITERATE = SUMO_DIR / "routes" / "routes_dueiterate.rou.xml"

# =============
# Missingness dueIterate-specific
# =============
MISSINGNESS_DIR_DUEITERATE = DUE_DATA_dueIterate / "missingness"
MISSINGNESS_DUEITERATE_INT = (
    MISSINGNESS_DIR_DUEITERATE / "missingness_dueiterate_by_int.parquet"
)
MISSINGNESS_DUEITERATE_EDGE = (
    MISSINGNESS_DIR_DUEITERATE / "missingness_dueiterate_by_edge.parquet"
)
MISSINGNESS_DUEITERATE_EPISODE = (
    MISSINGNESS_DIR_DUEITERATE / "missingness_dueiterate_by_episode.parquet"
)
MISSINGNESS_DUEITERATE_REPORT = (
    MISSINGNESS_DIR_DUEITERATE / "missingness_dueiterate_report.txt"
)


# ============================================================
# Temporary/generated files
# ============================================================

UNDESIRED_ROUTE_FILE = BASE_DIR / "routes.rou.xml"

UNDESIRED_DUEITERATE_FILES = [
    BASE_DIR / "dua.log",
    BASE_DIR / "stdout.log",
    BASE_DIR / "edgedata.add.xml",
]

# ============================================================
# Edge visualization
# ============================================================

EDGE_VISUALIZATION_DIR = SUMO_DIR / "config" / "edge_visualization"

SUMO_CONF_AGGREGATED = EDGE_VISUALIZATION_DIR / "aggregated.sumocfg"

GUI_SETTINGS_AGGREGATED = EDGE_VISUALIZATION_DIR / "gui_settings_aggregated.xml"

MEANDATA_AGGREGATED = EDGE_VISUALIZATION_DIR / "meandata_aggregated.xml"
