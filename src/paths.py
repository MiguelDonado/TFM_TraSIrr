from pathlib import Path

# Root of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Folders
SUMO_DIR = BASE_DIR / "sumo"
PLOTS_DIR = SUMO_DIR / "output"

# Files
NET_FILE = SUMO_DIR / "net" / "net.net.xml"  # For saving
SUMO_CONF = SUMO_DIR / "config" / "basic.cfg"
YAML_CONF = BASE_DIR / "src" / "config" / "config.yaml"
MAP_FILE = SUMO_DIR / "net" / "thesisToyNetwork.net.xml"  # For using
TRIPSINFO_OUTPUT_FILE = SUMO_DIR / "output" / "tripsInfoOutput.xml"
VEHROUTE_OUTPUT_FILE = SUMO_DIR / "output" / "vehrouteOutput.xml"
STATISTICSINFO_OUTPUT_FILE = SUMO_DIR / "output" / "statisticsInfoOutput.xml"
UNDESIRED_ROUTE_FILE = BASE_DIR / "src" / "routes.rou.xml"  # Extra file not needed

# Plots
PLOT_STATISTICS_OUTPUT = PLOTS_DIR / "statistics_output.png"
