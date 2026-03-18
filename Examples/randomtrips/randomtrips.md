```sh
# https://sumo.dlr.de/docs/Tools/Trip.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/randomtrips

# 2. Generate trips
randomTrips.py -n net.net.xml --trip-attributes="type=\"vehDist\"" -b 0 -e 50 -p 2 --prefix veh_ -o trips.trips.xml
```