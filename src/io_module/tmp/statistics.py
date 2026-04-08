from lxml import etree

###############
# 1. Vehroutes
# Extract time of vehicle on each edge
###############

## First alternative
# Read xml
tree = etree.parse("statistics.xml")

routeLength = tree.xpath("//vehicleTripStatistics/@routeLength")
speed = tree.xpath("//vehicleTripStatistics/@speed")
duration = tree.xpath("//vehicleTripStatistics/@duration")
totalTravelTime = tree.xpath("//vehicleTripStatistics/@totalTravelTime")
timeLoss = tree.xpath("//vehicleTripStatistics/@timeLoss")

print(routeLength)
print(speed)
print(duration)
print(totalTravelTime)
print(timeLoss)
