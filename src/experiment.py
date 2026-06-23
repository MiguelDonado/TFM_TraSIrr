"""
Purpose of this file: Orchestration + Pipeline
1. Saving results
2. Handling the data structure in which results are stored
"""

import subprocess
import sys

import numpy as np
import pandas as pd
import yaml
from lxml import etree

from config.config import RunMode, config
from config.paths import (
    ACTIONS,
    BM_RESULTS,
    EDGEDATA_PARQUET,
    EDGEDATA_XML,
    FCD_PARQUET,
    FCD_XML,
    OD_ROUTES,
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
    aggregated_result = parse_aggregated_data(episode)
    vehroute_result = parse_vehroute(episode, VEHROUTE_XML)
    trips_info_result = parse_trips_info(episode, TRIPS_INFO_XML)
    fcd_result = parse_fcd(episode)
    edgedata_result = parse_edgedata(episode, EDGEDATA_XML)
    actions = _prepare_actions(episode, actions)
    rewards = _prepare_rewards(episode, rewards)
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

    """
    getattr: Returns the method dynamically
    
    Example:
    getattr([], "append") translates to list.append()

    Example:
    key = "Padre"
    my_fun = "append"
    data_dict = {"Padre": ["Miguel", "Donado"], "Madre": ["Mercedes", "Fernandez"]}
    getattr(data_dict[key], my_fun)("Campos")

    ### Output ### 
    # {'Padre': ['Miguel', 'Donado', 'Campos'], 'Madre': ['Mercedes', 'Fernandez']}
    """

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


def make_plots():
    subprocess.run(["Rscript", "r/plots.R"])


########################################
########################################
# HELPER FUNCTIONS
########################################
########################################


def _prepare_actions(episode, actions):
    rows = []
    for agent, action in actions.items():
        rows.append({"episode": episode, "agent_id": agent, "action": action})
    return rows


def _prepare_rewards(episode, rewards):
    rows = []
    for agent, reward in rewards.items():
        rows.append({"episode": episode, "agent_id": agent, "reward": reward})
    return rows


def _prepare_bm_data(episode, agents):
    rows = []
    for _, agent in agents.items():
        for route_id, perceived_travel_time in enumerate(agent.perceived_travel_times):
            rows.append(
                {
                    "episode": episode,
                    "agent_id": agent.id,
                    "ET": agent.expected_travel_time,
                    "stimulus": agent.stimulus,
                    "route_id": route_id,
                    "PT": float(perceived_travel_time),
                }
            )
    return rows


def log_run_mode(mode, have_precomputed_routes, episodes_gui):
    print("\n\n#########################")
    print("RUN MODE")
    print("#########################")

    print(f"Mode '{mode}' has been selected.\n")

    if mode == RunMode.COMPUTE_ROUTES:
        print(
            (
                "The script will generate OD pairs and compute k routes. "
                f"Results will be saved in {OD_ROUTES}"
            )
        )
    elif mode == RunMode.EVAL_GUI:
        print("The script will visualize the previous final episode using the GUI.")
    elif mode in {RunMode.TRAIN}:
        msg_precomputed_routes = (
            f"Using precomputed routes from {OD_ROUTES}."
            if have_precomputed_routes
            else "k routes will be generated using the duarouter."
        )
        msg_gui = f"GUI enabled for episodes {episodes_gui}" if episodes_gui else ""

        print(msg_precomputed_routes)
        if msg_gui:
            print(msg_gui)
    print("\n")


def run_final_simulation():
    cmd = [
        "sumo-gui",
        "-c",
        SUMO_CONF,
        "--route-files",  # Add the route-files through CLI (for simplicity, avoids having modify config file again)
        ROUTES,
    ]
    subprocess.run(cmd)
