"""
Per-episode data collection and end-of-run persistence for the BM simulation.

Implements a two-phase pattern used inside the training loop:

  1. Per-episode  — parse SUMO XML outputs and agent state, accumulate
                    into eight in-memory lists (one per data stream).
  2. End-of-run   — flush all lists to parquet files under data/.

Data streams managed
--------------------
aggregated   — episode-level statistics (mean speed, travel time…)
vehroute     — per-vehicle, per-edge exit times
trips_info   — per-vehicle trip summary (duration, length, time_loss)
fcd          — sampled vehicle XY positions across timesteps
edgedata     — per-edge density and flow per time interval
actions      — route index chosen by each agent per episode
rewards      — travel time received by each agent per episode
BM_results   — agent internal state (ET, PT, stimulus) per episode

Post-warm-up filtering
-----------------------
Warm-up agents (BMAgent.post_warm_up is False) are excluded from every
per-agent stream, so nothing downstream (DUE convergence, plots) needs to
re-apply that filter itself:
  - vehroute, trips_info, fcd  — parsed from raw SUMO XML (all vehicles),
                                 then filtered post-parse by vehicle_id.
  - actions, rewards, BM_results — filtered at generation time, since each
                                 row is built directly from a BMAgent that
                                 already carries post_warm_up.
aggregated and edgedata are network/episode-level aggregates with no agent
dimension — there is no per-agent row to filter, and they must keep
reflecting all traffic (including warm-up vehicles) to stay physically
correct.

Also contains two utility functions used by main.py:
  log_episodes_gui     — prints which episodes have GUI enabled, if any
  run_final_simulation — replays the last episode in sumo-gui
"""

import subprocess
import sys

import numpy as np
import pandas as pd
import yaml
from lxml import etree

from config.config import config
from config.paths import (
    ACTIONS,
    BM_RESULTS,
    EDGEDATA_PARQUET,
    EDGEDATA_XML,
    FCD_PARQUET,
    FCD_XML,
    REWARDS,
    ROUTES,
    STATISTICS_PARQUET,
    STATISTICS_XML,
    SUMO_CONF,
    TRIPS_INFO_PARQUET,
    TRIPS_INFO_XML,
    VEHROUTE_PARQUET,
    VEHROUTE_XML,
    YAML_CONF,
)
from parsing.parser import Parser
from parsing.sumo_outputs import (
    parse_aggregated_data,
    parse_edgedata,
    parse_fcd,
    parse_section_to_raw_strings,
    parse_trips_info,
    parse_vehroute,
)

########################################
########################################
#  CORE LOGIC FUNCTIONS
########################################
########################################


def prepare_data(episode, actions, rewards, agents):

    post_warm_up_ids = {
        agent_id for agent_id, agent in agents.items() if agent.post_warm_up
    }

    # network aggregate, no agent dimension — never filtered
    aggregated_result = parse_aggregated_data(episode)
    vehroute_result = _filter_post_warm_up(
        rows = parse_vehroute(episode, VEHROUTE_XML), 
        post_warm_up_ids = post_warm_up_ids
    )
    trips_info_result = _filter_post_warm_up(
        rows = parse_trips_info(episode, TRIPS_INFO_XML),
        post_warm_up_ids = post_warm_up_ids
    )
    fcd_result = _filter_post_warm_up(
        rows = parse_fcd(episode),
        post_warm_up_ids = post_warm_up_ids
    )
    # network aggregate, no agent dimension — never filtered
    edgedata_result = parse_edgedata(episode, EDGEDATA_XML)

    actions = _prepare_actions(episode, actions, agents)
    rewards = _prepare_rewards(episode, rewards, agents)
    bm_result = _prepare_bm_data(episode, agents)
    return {
        "aggregated_result": aggregated_result,
        "vehroute_result": vehroute_result,
        "trips_info_result": trips_info_result,
        "fcd_result": fcd_result,
        "edgedata_result": edgedata_result,
        "actions_result": actions,
        "rewards_result": rewards,
        "BM_result": bm_result,
    }


def _filter_post_warm_up(rows, post_warm_up_ids):
    return [row for row in rows if row["vehicle_id"] in post_warm_up_ids]



def accumulate_results(results, result):
    mapping = {
        "aggregated": ("aggregated_result", "append"),
        "vehroute": ("vehroute_result", "extend"),
        "trips_info": ("trips_info_result", "extend"),
        "fcd": ("fcd_result", "extend"),
        "edgedata": ("edgedata_result", "extend"),
        "actions": ("actions_result", "extend"),
        "rewards": ("rewards_result", "extend"),
        "BM_results": ("BM_result", "extend"),
    }

    for key, (res_key, method) in mapping.items():
        getattr(results[key], method)(result[res_key])


def save_processed_data(results):
    mapping = {
        "aggregated": STATISTICS_PARQUET,
        "vehroute": VEHROUTE_PARQUET,
        "trips_info": TRIPS_INFO_PARQUET,
        "fcd": FCD_PARQUET,
        "edgedata": EDGEDATA_PARQUET,
        "actions": ACTIONS,
        "rewards": REWARDS,
        "BM_results": BM_RESULTS,
    }

    for key, path in mapping.items():
        df = pd.DataFrame(results[key])
        # Extra code to make fcd smaller
        if key == "fcd":
            categorical_cols = ["vehicle_id"]
            for col in categorical_cols:
                df[col] = df[col].astype("category")
            df.to_parquet(path, compression="zstd", compression_level=9)
        else:
            df.to_parquet(path, engine="pyarrow")


########################################
########################################
# HELPER FUNCTIONS
########################################
########################################


def _prepare_actions(episode, actions, agents):
    rows = []
    for agent_id, action in actions.items():
        if agents[agent_id].post_warm_up:
            rows.append({"episode": episode, "agent_id": agent_id, "action": action})
    return rows


def _prepare_rewards(episode, rewards, agents):
    rows = []
    for agent_id, reward in rewards.items():
        if agents[agent_id].post_warm_up:
            rows.append({"episode": episode, "agent_id": agent_id, "reward": reward})
    return rows


def _prepare_bm_data(episode, agents):
    rows = []
    for agent in agents.values():
        if not agent.post_warm_up:
            continue
        memory_level = agent.gamma
        for route_id, perceived_travel_time in enumerate(agent.perceived_travel_times):
            rows.append(
                {
                    "episode": episode,
                    "agent_id": agent.id,
                    "memory_level": memory_level,
                    "ET": agent.expected_travel_time,
                    "stimulus": agent.stimulus,
                    "route_id": route_id,
                    "PT": float(perceived_travel_time),
                }
            )
    return rows

def run_final_simulation():
    cmd = [
        "sumo-gui",
        "-c",
        SUMO_CONF,
        "--route-files",  # Add the route-files through CLI (for simplicity, avoids having modify config file again)
        ROUTES,
    ]
    subprocess.run(cmd)
