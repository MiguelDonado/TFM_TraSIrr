from pathlib import Path

from config.config import config

# Root of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Folders
SUMO_DIR = BASE_DIR / "sumo"
OUTPUT_DIR = SUMO_DIR / "output"

# Parquet files (outputs that will be analyzed in R)
STATISTICS_PLOT = OUTPUT_DIR / "statistics_output" / "statistics.parquet"

# Output files
STATISTICS = OUTPUT_DIR / "statistics.xml"
TRIPS_INFO = OUTPUT_DIR / "tripsinfo.xml"
VEHROUTE = OUTPUT_DIR / "vehroute.xml"
OD_MATRIX = OUTPUT_DIR / "od_matrix.csv"

# Files
MAP = SUMO_DIR / "net" / config.network  # For using
NET = SUMO_DIR / "net" / "net.net.xml"  # For saving (if OSM file is provided)
ROUTES = SUMO_DIR / "routes" / "routes.rou.xml"
SUMO_CONF = SUMO_DIR / "config" / "basic.cfg"
YAML_CONF = BASE_DIR / "src" / "config" / "config.yaml"

# File automatically generated (used to delete it)
UNDESIRED_ROUTE_FILE = BASE_DIR / "routes.rou.xml"
