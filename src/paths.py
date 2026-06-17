from pathlib import Path

from config.config import config

# ============================================================
# Project root
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# MLFlow database
# ============================================================
BACKEND_DB = BASE_DIR / "mlflow_db" / "mlflow.db"
ARTIFACTS_STORAGE = BASE_DIR / "mlruns" / "mlruns"

# ============================================================
# Main folders
# ============================================================

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OD_MATRIX_DIR = DATA_DIR / "od_matrix"
INTERNAL_DATA_DIR = DATA_DIR / "internal"
DUE_DATA_DIR = DATA_DIR / "DUE"
DUE_DATA_BM = DUE_DATA_DIR / "BM"
DUE_DATA_duaIterate = DUE_DATA_DIR / "duaIterate"

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

OD_MATRIX_INTERVALS = OD_MATRIX_DIR / "od_matrix_intervals.csv"
OD_MATRIX_TOTAL = OD_MATRIX_DIR / "od_matrix_total.csv"


# ============================================================
# Internal agents data
# ============================================================

AGENTS_OD = INTERNAL_DATA_DIR / "agents_od.parquet"
OD_ROUTES = INTERNAL_DATA_DIR / "od_routes.parquet"
POLICY_CHANGE_BM = INTERNAL_DATA_DIR / "policy_change_BM.parquet"
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
RGAP_DIR = DUE_DATA_BM / "R-gap"

FLOWS_PATHS = DUE_DATA_BM / "flows_paths_odtp_k.parquet"
COST_PATHS = DUE_DATA_BM / "costs_paths_odtp_k.parquet"
COST_LINKS = TDSP_DIR / "costs_links_t_k.parquet"
COST_MIN_PATHS = TDSP_DIR / "costs_min_paths_t_k.parquet"


RGAP = RGAP_DIR / "rgap.parquet"
REFINED_RGAP = RGAP_DIR / "refined_rgap.parquet"
RGAP_BY_OD = RGAP_DIR / "rgap_by_od.parquet"
REFINED_RGAP_BY_OD = RGAP_DIR / "refined_rgap_by_od.parquet"

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
# DUE data duaIterate-specific
# ============================================================
TDSP_DIR_duaIterate = DUE_DATA_duaIterate / "TDSP"
WEIGHTS_DIR_duaIterate = TDSP_DIR_duaIterate / "weights"
SHORTEST_PATHS_DIR_duaIterate = TDSP_DIR_duaIterate / "shortest_paths"
RGAP_DIR_duaIterate = DUE_DATA_duaIterate / "R-gap"

FLOWS_PATH_duaIterate = DUE_DATA_duaIterate / "flows_path_duaIterate.parquet"
COST_PATHS_duaIterate = DUE_DATA_duaIterate / "costs_paths_odtp_k_duaIterate.parquet"
COST_LINKS_duaIterate = TDSP_DIR_duaIterate / "costs_links_duaIterate_t_k.parquet"
COST_MIN_PATHS_duaIterate = (
    DUE_DATA_duaIterate / "costs_min_paths_odtp_k_duaIterate.parquet"
)
TRIPS_duaIterate = TDSP_DIR_duaIterate / "trips_duaIterate.xml"
OD_ROUTES_duaIterate = DUE_DATA_duaIterate / "od_routes_duaIterate.parquet"
ACTIONS_duaIterate = DUE_DATA_duaIterate / "actions_duaIterate.parquet"
TRIPS_INFO_PROCESSED_duaIterate = (
    DUE_DATA_duaIterate / "trips_info_processed_duaIterate.parquet"
)
VEHROUTE_duaIterate_PROCESSED = DUE_DATA_duaIterate / "vehroute_duaIterate.parquet"
EDGEDATA_duaIterate_PROCESSED = (
    DUE_DATA_duaIterate / "edgedata" / "edgedata_duaIterate.parquet"
)

RGAP_duaIterate = RGAP_DIR_duaIterate / "rgap.parquet"
REFINED_RGAP_duaIterate = RGAP_DIR_duaIterate / "refined_rgap.parquet"
RGAP_BY_OD_duaIterate = RGAP_DIR_duaIterate / "rgap_by_od.parquet"
REFINED_RGAP_BY_OD_duaIterate = RGAP_DIR_duaIterate / "refined_rgap_by_od.parquet"

ROUTES_duaIterate = SUMO_DIR / "routes" / "routes_duaIterate.rou.xml"

# =============
# Missingness duaIterate-specific
# =============
MISSINGNESS_DIR_duaIterate = DUE_DATA_duaIterate / "missingness"
MISSINGNESS_duaIterate_INT = (
    MISSINGNESS_DIR_duaIterate / "missingness_duaIterate_by_int.parquet"
)
MISSINGNESS_duaIterate_EDGE = (
    MISSINGNESS_DIR_duaIterate / "missingness_duaIterate_by_edge.parquet"
)
MISSINGNESS_duaIterate_EPISODE = (
    MISSINGNESS_DIR_duaIterate / "missingness_duaIterate_by_episode.parquet"
)
MISSINGNESS_duaIterate_REPORT = (
    MISSINGNESS_DIR_duaIterate / "missingness_duaIterate_report.txt"
)


# ============================================================
# Temporary/generated files
# ============================================================

UNDESIRED_ROUTE_FILE = BASE_DIR / "routes.rou.xml"

UNDESIRED_duaIterate_FILES = [
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
