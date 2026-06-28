"""
Generates the agent list (OD pairs + departure times) from a network.

Shared by Scenario (called once at startup) and the demand calibration
loop (called each iteration with a different n_agents), so both use the
same OD distribution.
"""

import os
import subprocess
import tempfile
from collections import Counter

from lxml import etree

from config.config import config
from utils.network import get_median_edge_lengths


def generate_agents(n_agents_warmup, n_agents_post_warmup, rng):
    n_agents = n_agents_warmup + n_agents_post_warmup

    agents = []
    od_pairs, unique_ods = generate_od_for_agents(n_agents, n_agents_post_warmup, rng)
    departure_times = generate_departure_times(n_agents, rng)
    for i in range(n_agents):
        origin, dest = od_pairs[i]
        departure_time = departure_times[i]
        agents.append(
            {
                "id": f"agent_{i+1}",
                "origin": origin,
                "destination": dest,
                "departure_time": departure_time,
            }
        )
    return agents, unique_ods


def generate_od_for_agents(n_agents, n_agents_post_warmup, rng):
    with tempfile.TemporaryDirectory() as tmpdir:
        trips_file = os.path.join(tmpdir, "trips.xml")
        # Generate random ods for agents
        generate_random_trips_agents(n_agents_post_warmup, trips_file)
        # OD space
        od_space = parse_od_agents(trips_file)
        # Restricted/bounded OD space
        restricted_od_space_counter = restrict_od_space(
            od_space, config.max_size_od_space
        )
        # Sample ods for all the agents from the restricted OD space
        od_pairs, unique_ods = sample_od_space(
            restricted_od_space_counter,
            n_agents,
            rng,
        )
    return (od_pairs, unique_ods)


def generate_random_trips_agents(n_agents_post_warmup, output_file):
    min_distance = int(2 * get_median_edge_lengths(config.network))
    config.min_distance = min_distance

    cmd = [
        "randomTrips.py",
        "-n",
        config.network,
        "-b",
        str(0),
        "-e",
        str(config.end_time),
        "-p",
        str(((config.end_time - 0) / (n_agents_post_warmup))),
        "--fringe-factor",
        str(config.fringe_factor),
        "--min-distance",
        # str(config.min_distance),
        "100",
        "--seed",
        str(config.seed),
        "--validate",
        "-o",
        output_file,
    ]

    subprocess.run(cmd, check=True)


def parse_od_agents(trips_file):
    tree = etree.parse(trips_file)
    origins = tree.xpath("//trip/@from")
    destinations = tree.xpath("//trip/@to")
    od_pairs = list(zip(origins, destinations))
    return od_pairs


def restrict_od_space(od_list, k):
    """
    Make sure to restrict/bound the OD pool to <= k unique ODs
    """
    counter = Counter(od_list)

    # Limit pool to k ODs (e.g., most frequent)
    # .most_common() returns [(('A','B'), 3), (('C','D'), 2)]
    most_common = counter.most_common(k)
    return most_common


def sample_od_space(od_space_counter, n_agents, rng):
    """
    Sample from a OD space counter object. That is [((A,B),3),((A,C),2)]
    It will receive the reduced OD space counter object
    """

    unique_ods = [od for od, _ in od_space_counter]
    counts = [count for _, count in od_space_counter]

    # Step 2: Probabilities within reduced pool
    total = sum(counts)
    probs = [c / total for c in counts]

    # Step 3: sample MANY agents from FEW ODs
    ods = rng.choice(len(unique_ods), size=n_agents, p=probs)
    ods = [unique_ods[i] for i in ods]
    return (ods, unique_ods)


def generate_departure_times(n_agents, rng):
    departure_times = rng.integers(
        0,
        config.end_time,
        size=n_agents,
    )

    departure_times = [int(departure_time) for departure_time in departure_times]
    # Sort departure times, to avoid problems in SUMO simulation and for clarity. The agent_1 should be the first to departure, the agent_2 the second...
    departure_times.sort()
    return departure_times
