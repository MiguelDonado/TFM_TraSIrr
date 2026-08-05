"""
Computes alternative routes per OD pair via duarouter.

find_routes() is shared between two call sites that need it for different reasons:

- Scenario.compute_k_routes - the real, final route set used for training,
parameterised per-experiment (k, random_factor may vary across
sensitivity sweeps that reuse the same OD pool).
- generate_agents.restrict_od_space - a cheap upfront screen that checks
candidate OD pairs have enough route diversity before commiting to them, 
independent of whatever k/random_factor a later Scenario call will use.
"""

import os
import subprocess
import tempfile

from config.config import config
from config.paths import UNDESIRED_ROUTE_FILE
from utils.od_routes import parse_route


def find_routes(network, ods, seeds, k, random_factor):
    """
    For each OD pair in `ods`, find up to k alternative routes via duarouter.

    Returns {od: [route, ...]}, where a route list may have fewer than k
    entries if duarouter could not find more alternatives within the given
    seeds budget. Returns {} if duarouter could not route any of the ods at
    all (e.g. a disconnected network).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        trips_file = os.path.join(tmpdir, "trips.xml")
        routes_file = os.path.join(tmpdir, "routes.xml")

        _write_trip(trips_file, ods)

        # Best route according to shortest-path
        best_routes = _run_duarouter(
            network, trips_file, routes_file, random_factor=1.0
        )

        if not best_routes:
            return {}

        # Initialize structure: one list per OD
        routes_per_od = [[r] for r in best_routes]

        # Fill in alternatives by perturbing edge costs across seeds
        _fill_alternative_routes(
            network, routes_per_od, trips_file, routes_file, seeds, k, random_factor
        )

        UNDESIRED_ROUTE_FILE.unlink(missing_ok=True)

        return dict(zip(ods, routes_per_od))


def _fill_alternative_routes(
    network, routes_per_od, trips_file, routes_file, seeds, k, random_factor
):
    """
    Does not need to return anything because it is already modifying the
    routes_per_od object passed by reference
    """
    for seed in seeds:
        # Early stop
        if all(len(rlist) >= k for rlist in routes_per_od):
            break

        # So each time we call duarouter, assigns different random factor to each edge
        new_routes = _run_duarouter(
            network,
            trips_file,
            routes_file,
            random_factor=random_factor,
            seed=seed,
        )

        if not new_routes:
            continue

        for i, route in enumerate(new_routes):
            # Avoid duplicates per OD
            if route not in routes_per_od[i] and len(routes_per_od[i]) < k:
                routes_per_od[i].append(route)


def _run_duarouter(network, trips_file, routes_file, random_factor, seed=None):

    seed = seed if seed is not None else config.seed

    cmd = [
        "duarouter",
        "-n",
        network,
        "--route-files",
        trips_file,
        "-o",
        routes_file,
        "--routing-threads",
        str(config.n_threads),
        "--routing-algorithm",
        config.routing_algorithm,
        # Just in case, even though it seems that this option --max-alternatives does not work (does not compute more than one route)
        "--max-alternatives",
        "1",
        "--weights.random-factor",
        str(random_factor),
        "--seed",
        str(seed),
        "--no-step-log",
    ]

    subprocess.run(cmd, check=True)

    return parse_route(routes_file)


def _write_trip(file_path, ods):
    with open(file_path, "w") as f:
        f.write(f"<routes>\n")
        for i, (origin, destination) in enumerate(ods):
            f.write(
                f"""\t<trip id="t{i}" from="{origin}" to="{destination}" depart="0"/>\n"""
            )
        f.write("</routes>\n")
