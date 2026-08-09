I already check with ChatGPT that Im right in both of these.

1. First, if a meandata file is loaded in which we specify an aggregation interval for the edgedata, then the color by live edgedata is gonna take into account the aggregation interval, and is gonna compute the values of the metric for that agggreagation interval, that is if i say aggreagtion interval 900seconds, and the metric is "entered", if I advance the simulation to 900 seconds, is gonna show me the metric entered aggregated for those 900seconds, and during 0-900 i will see how rhe aggreagted metric evolves. 
2. Thee rainbow color, is to make the scale color, to adapt to the data rnage of the aggreagated metric. For example beause the data range is not the same at the second 100, only 100 seconds, aggregated, than at the second 900, I should click again onn rainbow color at 900, to get the right scale.

Im using "color by live edgeData" instead of loading an edgeData file, because this last option does not work.