"""
Purpose of this script is to get the avg speed of the vehicles in the network.
It does so, by:
1. Get all  avg speed at timestep t of all the vehicles
2. Filter by the timesteps we are interested on (post-warmup)
3. Take avg of those

avg_speed = avg of avg_speed_t (only for t after warmup)
"""

import numpy as np
from lxml import etree

# CONSTANTS
WARMUP_SECONDS = 600
SUMMARY_FILE_PATH = (
    "/home/miguel/6.Projects/Thesis/src/scripts/2026-03-26-19-42-13summary.xml"
)


def get_avg_speed(warmup_seconds, summary_filepath=SUMMARY_FILE_PATH):
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


if __name__ == "__main__":
    get_avg_speed(WARMUP_SECONDS)
