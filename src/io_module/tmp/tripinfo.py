from lxml import etree

###############
# 1. Vehroutes
# Extract time of vehicle on each edge
###############

## First alternative
# Read xml
tree = etree.parse("tripinfo.xml")

# Get all vehicles ids
vehicles_ids = tree.xpath("//tripinfo/@id")
# Get arrivals
arrivals = tree.xpath("//tripinfo/@arrival")
# Get duration
durations = tree.xpath("//tripinfo/@duration")
# Get routeLength
routeLengths = tree.xpath("//tripinfo/@routeLength")
# Get time loss
timeLosses = tree.xpath("//tripinfo/@timeLoss")

if (
    len(vehicles_ids)
    == len(arrivals)
    == len(durations)
    == len(routeLengths)
    == len(timeLosses)
):
    data = []

    for vid, arrival, duration, length, timeloss in zip(
        vehicles_ids, arrivals, durations, routeLengths, timeLosses
    ):
        data.append(
            {
                "vehicle_id": vid,
                "arrival": arrival,
                "duration": duration,
                "Routelength": length,
                "TimeLoss": timeloss,
            }
        )
    print(data)
else:
    print("Something is wrong. Length of lists doesnt match.")
