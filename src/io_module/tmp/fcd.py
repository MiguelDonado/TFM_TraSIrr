from lxml import etree

###############
# 1. Vehroutes
# Extract time of vehicle on each edge
###############

## First alternative
# Read xml
tree = etree.parse("fcd.xml")

timesteps_elements = tree.xpath("//timestep")
data = []
for timestep_element in timesteps_elements:
    timestep = timestep_element.get("time")
    vehicles_elements = timestep_element.xpath("vehicle")

    # Make sure simulation is still running vehicles
    if not vehicles_elements:
        continue
    vehicles = []
    for vehicle_element in vehicles_elements:
        vehicle_id = vehicle_element.get("id")
        vehicle_x = vehicle_element.get("x")
        vehicle_y = vehicle_element.get("y")
        info = {"id": vehicle_id, "x": vehicle_x, "y": vehicle_y}
        vehicles.append(info)
    data.append({"timestep": timestep, "vehicles": vehicles})
print(data)
