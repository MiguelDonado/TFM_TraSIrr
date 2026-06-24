"""
Compute post-warm-up average vehicle speed from a SUMO summary output file.

Used by demand calibration as a congestion proxy:
    congestion_ratio = avg_speed / free_flow_speed

The warm-up period is excluded because on that window there are few vehicles
on the network, and the avg speed for those timesteps is higher, hence our final average speed
would be overestimated, leading to think the network is less congested than what really is.

SUMO's summary.xml reports a network-wide meanSpeed per timestep.
Steps with meanSpeed <= 0 are filtered out — SUMO emits -1 at the
final timestep as a sentinel value.
"""

import numpy as np
from lxml import etree


def get_avg_speed(warmup_seconds, summary_filepath):
    ###########
    # SCRIPT
    ###########

    document = summary_filepath
    tree = etree.parse(document)

    # Filter avg speeds of post warmup timesteps and check they are positive (because I saw that last timestep has meanSpeed = -1)
    avg_speeds_post_warmup = tree.xpath(
        f"//step[@time>{warmup_seconds}][@meanSpeed>0]/@meanSpeed"
    )
    avg_speeds_post_warmup = [float(avg_speed) for avg_speed in avg_speeds_post_warmup]

    avg_speed_post_warmup = round(np.average(a=avg_speeds_post_warmup), 2)
    return avg_speed_post_warmup
