from pathlib import Path

# Root of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Folders
SUMO_DIR = BASE_DIR / "sumo"

# Files
NET_FILE = SUMO_DIR / "net" / "net.net.xml"  # For saving
TRIP_FILE = SUMO_DIR / "trips" / "trips.trips.xml"
ROUTE_FILE = SUMO_DIR / "routes" / "routes.rou.xml"
SUMO_CONF = SUMO_DIR / "config" / "basic.cfg"
VTYPE_FILE = SUMO_DIR / "additional" / "vtype.add.xml"
MAP_FILE = SUMO_DIR / "net" / "thesisToyNetwork.net.xml"  # For using
TRIPSINFO_OUTPUT_FILE = SUMO_DIR / "output" / "tripsInfoOutput.xml"
UNDESIRED_ROUTE_FILE = BASE_DIR / "src" / "routes.rou.xml"  # Extra file not needed
