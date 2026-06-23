from dataclasses import dataclass
from pathlib import Path

"""
Create a blueprint (to avoid duplication)
Previously I had to create explicitly the same paths for every algorithm
"""


@dataclass(frozen=True)
class DuePaths:
    root: Path
    tdsp_dir: Path
    rgap_dir: Path
    missingness_dir: Path
    weights_dir: Path
    shortest_paths_dir: Path
    flows_paths: Path
    cost_paths: Path
    cost_links: Path
    cost_min_paths: Path
    rgap: Path
    refined_rgap: Path
    rgap_by_od: Path
    refined_rgap_by_od: Path
    missingness_int: Path
    missingness_edge: Path
    missingness_episode: Path
    missingness_report: Path


# Create a factory
# It builds all paths automatically for a given algorithm
def _due_paths(root: Path) -> DuePaths:
    tdsp = root / "TDSP"
    rgap = root / "R-gap"
    missingness = root / "missingness"
    return DuePaths(
        root=root,
        tdsp_dir=tdsp,
        rgap_dir=rgap,
        missingness_dir=missingness,
        weights_dir=tdsp / "weights",
        shortest_paths_dir=tdsp / "shortest_paths",
        flows_paths=root / "flows_paths_odtp_k.parquet",
        cost_paths=root / "costs_paths_odtp_k.parquet",
        cost_links=tdsp / "costs_links_t_k.parquet",
        cost_min_paths=tdsp / "costs_min_paths_t_k.parquet",
        rgap=rgap / "rgap.parquet",
        refined_rgap=rgap / "refined_rgap.parquet",
        rgap_by_od=rgap / "rgap_by_od.parquet",
        refined_rgap_by_od=rgap / "refined_rgap_by_od.parquet",
        missingness_int=missingness / "missingness_by_int.parquet",
        missingness_edge=missingness / "missingness_by_edge.parquet",
        missingness_episode=missingness / "missingness_by_episode.parquet",
        missingness_report=missingness / "missingness_report.txt",
    )


@dataclass(frozen=True)
class DuaIteratePaths:
    mean_tt: Path
    trips: Path
    routes: Path
    od_routes: Path
    actions: Path
    trips_info_processed: Path
    vehroute_processed: Path
    edgedata_processed: Path


# ============================================================
# Project root
# ============================================================

# It points to ~/6.Projects/Thesis
BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
AGENT_STATE_DIR = DATA_DIR / "agent_state"
ENVIRONMENT_DIR = DATA_DIR / "environment"
DUE_DATA_DIR = DATA_DIR / "DUE"
DUE_DATA_generic = DATA_DIR / "DUE" / "generic"
DUE_DATA_BM = DUE_DATA_DIR / "BM"
DUE_DATA_duaIterate = DUE_DATA_DIR / "duaIterate"

FIGURES_DIR = BASE_DIR / "output" / "figures"

SUMO_DIR = BASE_DIR / "sumo"

PROFILING_DIR = BASE_DIR / "profiling"


# ============================================================
# SUMO files
# ============================================================

NET = SUMO_DIR / "net" / "net.net.xml"  # netconvert script
ROUTES = SUMO_DIR / "routes" / "routes.rou.xml"

SUMO_CONF = SUMO_DIR / "config" / "basic.sumocfg"
GUI_SETTINGS = SUMO_DIR / "config" / "gui_settings.xml"  # Template
MEANDATA = SUMO_DIR / "config" / "meandata.xml"

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

AGENTS_OD = ENVIRONMENT_DIR / "agents_od.parquet"
OD_ROUTES = ENVIRONMENT_DIR / "od_routes.parquet"
POLICY_CHANGE_BM = AGENT_STATE_DIR / "policy_change_BM.parquet"
DEMAND_ODT = DUE_DATA_generic / "demand_odt.parquet"

ACTIONS = AGENT_STATE_DIR / "actions.parquet"
REWARDS = AGENT_STATE_DIR / "rewards.parquet"
BM_RESULTS = AGENT_STATE_DIR / "BM_results.parquet"

# ============================================================
# Internal environment data
# ============================================================

FREE_FLOW_TRAVEL_TIMES = ENVIRONMENT_DIR / "free_flow_travel_times.parquet"
TIMES_INTERVAL = ENVIRONMENT_DIR / "times_interval.parquet"

# ============================================================
# Algorithms paths
# ============================================================
BM_PATHS = _due_paths(DUE_DATA_BM)
DUA_PATHS = _due_paths(DUE_DATA_duaIterate)
DUA_EXTRA = DuaIteratePaths(
    mean_tt=DUE_DATA_duaIterate / "mean_tt.parquet",
    trips=DUE_DATA_duaIterate / "trips.xml",
    routes=SUMO_DIR / "routes" / "routes_duaIterate.rou.xml",
    od_routes=DUE_DATA_duaIterate / "od_routes.parquet",
    actions=DUE_DATA_duaIterate / "actions.parquet",
    trips_info_processed=DUE_DATA_duaIterate / "trips_info_processed.parquet",
    vehroute_processed=DUE_DATA_duaIterate / "vehroute.parquet",
    edgedata_processed=DUE_DATA_duaIterate / "edgedata" / "edgedata.parquet",
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


# ============================================================
# MLFLOW
# ============================================================
MLFLOW = DATA_DIR / "MLflow"

# ============================================================
# EXPERIMENTS
# ============================================================
EXPERIMENTS_TMP = BASE_DIR / "experiments" / "tmp"


TRIPS_TDSP = DATA_DIR / "DUE" / "generic" / "trips.xml"
