from lxml import etree

###############
# 1. Vehroutes
# Extract time of vehicle on each edge
###############

## First alternative
# Read xml
tree = etree.parse("vehroute.xml")

# Get all vehicles
vehicles = tree.xpath("//vehicle/@id")
# Get all routes
routes = tree.xpath("//vehicle/route/@edges")
# Get all exit times
exit_times = tree.xpath("//vehicle/route/@exitTimes")

if len(vehicles) == len(routes) == len(exit_times):
    data = []

    for vid, edges, times in zip(vehicles, routes, exit_times):
        data.append(
            {
                "vehicle_id": vid,
                "edges": edges.split(),
                "exit_times": list(map(float, times.split())),
            }
        )
else:
    print("Something is wrong. Length of lists doesnt match.")
