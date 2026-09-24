"""
Golden (characterization) reference for the Bush-Mosteller agent.

Freezes the CURRENT behavior of agents.agent.BMAgent so later refactors
can prove they change nothing.
It does not prove BM is correct, only that its behavior hasn't changed.

How it works
-------------
BMAgents are trained for N_EPISODES with synthetic travel times instead of 
SUMO: fast (seconds), fully deterministic, and isolates the learner from 
everything around it. The training loop mirrors run_training_BM: all agents 
select an action, the environment returns travel/waiting times, then all
agents update

Synthetic environment
----------------------
Agents are split into OD groups (2, 4 and 8 routes). Within a group, each
route has a free-flow time.

It uses a link performance function, in particular the BPR.
Basically a link performance functions: 
The travel time on a route is a function of the number of users on it (non-decreasing)

    tt_r = ff_r · (1 + 0.15 · (load_r / cap_r)^4) · noise
    wt   = (tt_r - ff_r) · U(0.2, 0.6)        (part of the delay spent stopped)

Scenarios
---------
baseline                γ=1 (perfect memory) without Bounded Rationality extensions
fast_learning           high learning rate, low memory, without Bounded Rationality
                        extensions. To exercise the: 
                        the old_chosen >= 0.999 branch of _penalise_chosen 
heterogeneous_memory    per-agent γ ~ Beta(1, 1)
reliability_waiting     θ, φ > 0 (risk-averse and waiting-time averse drivers)
nonlinear               nonlinear response

Recorded per scenario: the route chosen by every agent each episode, and
every agent's p after each update (NaN-padded to 8 routes)

Usage
-----
Two modes. 
1) Only when you want to change the reference, e.g. after an intended change to the model
    python tests/golden/bm_golden.py            record the reference (overwrites)
2) Compares the new results against it.
    python tests/golden/bm_golden.py --verify   recompute and compare, bit for bit

Reference file
--------------
It is a NumPy .npz file. Basically a zip of named arrays:
               Key                    │           Shape           │                                          Content                                          │
├──────────────────────────────────────────┼───────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────┤
│ baseline__actions                        │ (100 episodes, 60 agents) │ route each agent chose each episode                                                       │
├──────────────────────────────────────────┼───────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────┤
│ baseline__p                              │ (100, 60, 8)              │ each agent's probabilities after each update (NaN where an agent has fewer than 8 routes) │
├──────────────────────────────────────────┼───────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────┤
... same for the other scenarios
... meta                                    metadata
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agents.agent import BMAgent

GOLDEN_FILE = Path(__file__).with_name("bm_golden.npz")

N_EPISODES = 100
WARM_UP = 10
EPSILON = 1e-8
MASTER_SEED = 2026
MAX_ROUTES = 8

# (n_routes, n_agents) per OD group
OD_GROUPS = [(2,20), (4,20), (8,20)]

SCENARIOS = {
    "baseline": dict(beta=0.3, gamma=1.0, theta=0.0, phi=0.0, nonlinear=False, tau=0.0),
    "fast_learning": dict(beta=0.8, gamma=0.5, theta=0.0, phi=0.0, nonlinear=False, tau=0.0),
    "heterogeneous_memory": dict(beta=0.3, gamma="beta(1,1)", theta=0.0, phi=0.0, nonlinear=False, tau=0.0),
    "reliability_waiting": dict(beta=0.3, gamma=0.8, theta=1.0, phi=0.5, nonlinear=False, tau=0.0),
    "nonlinear": dict(beta=0.3, gamma=0.8, theta=0.5, phi=0.2, nonlinear=True, tau=0.1),
}

def _build_agents(params, rng):
    agents = []
    groups = []  # group index of each agent (same length and order than agents)
                 # group refers to an OD pair. Each agent belongs to some OD pair
    i = 0
    for g, (n_routes, n_agents) in enumerate(OD_GROUPS):
        for _ in range(n_agents):
            gamma = rng.beta(1,1) if params["gamma"] == "beta(1,1)" else params["gamma"]
            agents.append(
                BMAgent(
                    agent_id=f"agent_{i}",
                    routes=list(range(n_routes)),
                    seed=MASTER_SEED+i,  # distinct seed per agent like factory.py
                    beta=params["beta"],
                    gamma=gamma,
                    epsilon=EPSILON,
                    departure_time=0,
                    post_warm_up=True,
                    reliability_sensitivity=params["theta"],
                    waiting_time_sensitivity=params["phi"],
                    nonlinear_stimulus=params["nonlinear"],
                    stimulus_tau=params["tau"]
                )
            )
            groups.append(g)
            i += 1
    return agents, np.array(groups)

def _environment(actions, groups, rng):
    """Synthetic travel and waiting times for one episode (BPR congestion + noise)"""
    travel_times = np.empty(len(actions))
    waiting_times = np.empty(len(actions))
    for g, (n_routes, n_agents) in enumerate(OD_GROUPS):
        # np.flatnonzero (returns the indices where value is nonzero/false)
        members = np.flatnonzero(groups == g)   # indices of agents in group g
        free_flow = 300.0 * (1 + 0.15 * np.arange(n_routes))
        capacity = n_agents / n_routes
        # np.bincount: Counter for integer values
        # Array containing the number of agents on each route
        load = np.bincount(actions[members], minlength=n_routes)
        route_tt = free_flow * (1 + 0.15 * (load / capacity) ** 4)
        for a in members:
            r = actions[a]
            tt = route_tt[r] * rng.lognormal(0.0, 0.1)
            travel_times[a] = tt
            waiting_times[a] = max(0.0, tt - free_flow[r]) * rng.uniform(0.2, 0.6)
    return travel_times, waiting_times

def run_scenario(index, params):
    # One rng for the environment (agents own their own rngs)
    rng = np.random.default_rng([MASTER_SEED, index])
    agents, groups = _build_agents(params, rng)
    n_agents = len(agents)

    # Creates a 2D array
    # Difference between np.empty and np.full is the values
    # they used to initialize the arrays
    actions_log = np.empty((N_EPISODES, n_agents), dtype=np.int64)
    p_log = np.full((N_EPISODES, n_agents, MAX_ROUTES), np.nan)

    for e, episode in enumerate(range(1, N_EPISODES + 1)):
        actions = np.array([agent.select_action() for agent in agents])
        travel_times, waiting_times = _environment(actions, groups, rng)
        for a, agent in enumerate(agents):
            agent.update(int(actions[a]), float(travel_times[a]), float(waiting_times[a]), WARM_UP, episode)
            p_log[e, a, : agent.n_routes] = agent.p
        actions_log[e] = actions

    return actions_log, p_log

def run_all():
    results = {}
    for index, (name, params) in enumerate(SCENARIOS.items()):
        actions_log, p_log = run_scenario(index, params)
        results[f"{name}__actions"] = actions_log
        results[f"{name}__p"] = p_log
    return results

def _git_commit():
    out = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    return out.stdout.strip()

def record():
    results = run_all()
    meta = dict(
        commit=_git_commit(),
        n_episodes=N_EPISODES,
        warm_up=WARM_UP,
        master_seed=MASTER_SEED,
        od_groups=OD_GROUPS,
        scenarios=SCENARIOS,
    )
    np.savez_compressed(GOLDEN_FILE, meta=np.array(json.dumps(meta)), **results)
    print(f"Recorded {len(SCENARIOS)} scenarios to {GOLDEN_FILE.resolve()}")

def verify():
    golden = np.load(GOLDEN_FILE)
    results = run_all()
    failures = [key for key, value in results.items() if not np.array_equal(value, golden[key], equal_nan = True)]
    if failures:
        print(f"FAIL: {len(failures)} arrays differ from the golden reference:")
        for key in failures:
            print(f"  {key}")
        sys.exit(1)
    print(f"OK: all {len(results)} arrays match the golden reference bit for bit")

if __name__ == "__main__":
    verify() if "--verify" in sys.argv else record()