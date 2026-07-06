"""
Generates the agent list (OD pairs + departure times) from a network.

Called by the demand calibration loop on each iteration with the current
n_agents estimate. The final agents produced at convergence are passed
directly to Scenario, so both calibration and training use the same OD
matrix.
"""

import os
import subprocess
import tempfile
from collections import Counter

from lxml import etree

from config.config import config
from utils.network import compute_diagonal_network


def generate_agents(
    n_agents_warmup, n_agents_post_warmup, rng, min_distance_factor=None
):
    if min_distance_factor is None:
        min_distance_factor = config.min_distance_factor

    n_agents = n_agents_warmup + n_agents_post_warmup

    agents = []
    od_pairs, unique_ods = generate_od_for_agents(
        n_agents, n_agents_post_warmup, rng, min_distance_factor
    )
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


def generate_od_for_agents(n_agents, n_agents_post_warmup, rng, min_distance_factor):

    with tempfile.TemporaryDirectory() as tmpdir:
        trips_file = os.path.join(tmpdir, "trips.xml")
        # Generate random ods for agents
        generate_random_trips_agents(
            n_agents_post_warmup, trips_file, min_distance_factor
        )
        # OD space
        od_space = parse_od_agents(trips_file)
        # Restricted/bounded OD space
        restricted_od_space_counter = restrict_od_space(
            od_space, config.max_size_od_space, n_agents_post_warmup
        )
        # Sample ods for all the agents from the restricted OD space
        od_pairs, unique_ods = sample_od_space(
            restricted_od_space_counter,
            n_agents,
            rng,
        )
    return (od_pairs, unique_ods)


def generate_random_trips_agents(
    n_agents_post_warmup, output_file, min_distance_factor
):
    """
    Generate random trips for the requested number of agents.

    Notes
    -----
    randomTrips.py attempts to find a valid origin–destination pair that
    satisfies the specified constraints (e.g., minimum distance). For each
    requested trip, it performs at most `--maxtries` random attempts.

    If no valid trip is found within `--maxtries` attempts, that trip is
    discarded. Consequently, the total number of generated trips may be
    smaller than the requested number of agents.

    During testing, the limiting factor was not the availability of distinct
    origin–destination pairs, but rather that some valid trips were not found
    within the default limit of 100 random attempts due to the rejection
    sampling process (especially when using a fringe factor). Therefore,
    `--maxtries` was increased to 1000 to reduce the number of discarded trips.

    Rejection sampling process:
    1. Randomly propose a candidate
    2. Check whether it satisfies the required constraints
    3. Accepting it if it does: otherwise rejecting it and trying again
    """

    assert (
        min_distance_factor <= 0.9
    ), f"lower min_distance_factor, otherwise no valid OD pairs will be found"

    min_distance = int(min_distance_factor * compute_diagonal_network(config.network))

    config.min_distance = min_distance
    print(f"min_distance: {min_distance}\n")

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
        str(min_distance),
        "--seed",
        str(config.seed),
        "-o",
        output_file,
        "--maxtries",
        "1000",
    ]

    subprocess.run(cmd, check=True)


def parse_od_agents(trips_file):
    tree = etree.parse(trips_file)
    origins = tree.xpath("//trip/@from")
    destinations = tree.xpath("//trip/@to")
    od_pairs = list(zip(origins, destinations))
    return od_pairs


def restrict_od_space(od_list, k, n_agents_post_warmup):
    """
    Make sure to restrict/bound the OD pool to <= k unique ODs
    """
    counter = Counter(od_list)

    generated_trips = sum(counter.values())
    distinct_ods = len(counter)

    print(f"{generated_trips} trips have been generated")
    print(f"{distinct_ods} different ods have been found")

    assert (
        generated_trips == n_agents_post_warmup
    ), f"Expected {n_agents_post_warmup} generated trips, but only {distinct_ods} "
    "were created. Some trips were discarded because randomTrips.py failed to "
    "find a valid origin–destination pair within --maxtries attempts, not "
    "necessarily because no feasible OD pair exists. Consider increasing "
    "--maxtries or relaxing the trip generation constraints."

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
