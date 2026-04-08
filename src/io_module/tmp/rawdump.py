from lxml import etree

###############
# 1. Vehroutes
# Extract time of vehicle on each edge
###############

## First alternative
# Read xml
tree = etree.parse("rawdump.xml")

data = []

# Get timestep elements
timestep_elements = tree.xpath("//timestep")
# Iterate over timestep elements
for timestep_element in timestep_elements:
    # Timestep
    timestep = timestep_element.get("time")
    # Edges on timestep
    edge_elements = timestep_element.xpath("edge")
    edges_ids = []
    # Edge
    for edge_element in edge_elements:
        edge_id = edge_element.get("id")
        # Vehicles
        vehicles_elements = edge_element.xpath("lane/vehicle")
        # Number vehicles
        number_vehicles = len(vehicles_elements)
        edges_ids.append({"id": edge_id, "num_veh": number_vehicles})
    data.append({"timestep": timestep, "edges": edges_ids})

print(data)
