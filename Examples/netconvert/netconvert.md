```sh
# https://sumo.dlr.de/docs/netconvert.html

# 0. Set right directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/netconvert
# 1. Download OSM from web
# 2. Use netconvert
netconvert --osm tibidabo.osm \
--geometry.remove \
--geometry.min-dist 1.0 \
--geometry.avoid-overlap \
--junctions.join \
--junctions.join-dist 15 \
--junctions.corner-detail 10 \
--junctions.internal-link-detail 10 \
--osm.turn-lanes \
--tls.guess \
--tls.guess-signals \
--tls.join \
--ramps.guess \
--output-file net.net.xml

# 3. Visualize in netedit
netedit net.net.xml
```