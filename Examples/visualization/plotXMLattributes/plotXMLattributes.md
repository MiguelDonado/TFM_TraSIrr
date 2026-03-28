```sh
# https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html
# https://sumo.dlr.de/docs/Tools/Visualization.html

# 1. Change directory
cd /home/miguel/6.Projects/ReplicateSongThesis/Examples/visualization/plotXMLattributes

# 2. Plot: Draw the paths of selected vehicles in the network based on fcd-output. 
plotXMLAttributes.py -x x -y y fcd-export.parquet

# Other interesting plots:
# 1. Histogram of timeLoss values from two simulation runs
# plotXMLAttributes.py tripinfos.xml tripinfos2.xml -x timeLoss -y @COUNT -i @NONE --legend  --barplot --xbin 20 --xclamp :300
# ...
```
