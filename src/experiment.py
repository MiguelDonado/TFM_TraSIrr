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

from config.config import RunMode, config
from parsing.parser import Parser
from paths import (
    ACTIONS,
    BM_RESULTS,
    FCD,
    FCD_PROCESSED,
    OD_ROUTES,
    REWARDS,
    ROUTES,
    STATISTICS,
    STATISTICS_PROCESSED,
    SUMO_CONF,
    TRIPS_INFO,
    TRIPS_INFO_PROCESSED,
    VEHROUTE,
    VEHROUTE_PROCESSED,
    YAML_CONF,
)

# Load YAML file
with open(YAML_CONF, "r") as file:
    config = yaml.safe_load(file)

########################################
########################################
#  CORE LOGIC FUNCTIONS
########################################
########################################


def prepare_data(episode, actions, rewards, agents):
    aggregated_result = parse_aggregated_data(episode)
    vehroute_result = parse_vehroute(episode)
    trips_info_result = parse_trips_info(episode)
    fcd_result = parse_fcd(episode)
    actions = prepare_actions(episode, actions)
    rewards = prepare_rewards(episode, rewards)
    BM_result = prepare_BM_data(episode, agents)
    return {
        "aggregated_result": aggregated_result,
        "vehroute_result": vehroute_result,
        "trips_info_result": trips_info_result,
        "fcd_result": fcd_result,
        "actions_result": actions,
        "rewards_result": rewards,
        "BM_result": BM_result,
    }


def accumulate_results(results, result):
    mapping = {
        "aggregated": ("aggregated_result", "append"),
        "vehroute": ("vehroute_result", "extend"),
        "trips_info": ("trips_info_result", "extend"),
        "fcd": ("fcd_result", "extend"),
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
        "aggregated": STATISTICS_PROCESSED,
        "vehroute": VEHROUTE_PROCESSED,
        "trips_info": TRIPS_INFO_PROCESSED,
        "fcd": FCD_PROCESSED,
        "actions": ACTIONS,
        "rewards": REWARDS,
        "BM_results": BM_RESULTS,
    }

    for key, path in mapping.items():
        df = pd.DataFrame(results[key])
        df.to_parquet(path, engine="pyarrow")


def make_plots():
    subprocess.run(["Rscript", "r/plots.R"])


########################################
########################################
# HELPER FUNCTIONS
########################################
########################################


def parse_aggregated_data(episode):
    data = {}
    parser = Parser(STATISTICS)

    for name, xpath in config["metrics"]["statistics"].items():
        value = parser.extract_one(xpath, float)
        data[name] = value
    return {"episode": episode, **data}


def parse_vehroute(episode):
    data = []
    parser = Parser(VEHROUTE)

    data_dict = extract_dict(parser, config["metrics"]["vehroute"])

    for name, xpath in config["metrics"]["vehroute"].items():
        values = parser.extract_many(xpath, str)
        data_dict[name] = values

    for vid, edges, times in zip(
        data_dict["vehicles"], data_dict["routes"], data_dict["exit_times"]
    ):
        edge_list = edges.split()
        time_list = list(map(float, times.split()))

        for edge, t in zip(edge_list, time_list):
            data.append(
                {
                    "episode": episode,
                    "vehicle_id": vid,
                    "edge": edge,
                    "exit_times": t,
                }
            )
    return data


def parse_trips_info(episode):
    data = []
    parser = Parser(TRIPS_INFO)

    data_dict = extract_dict(parser, config["metrics"]["tripsinfo"])

    for vid, arrival, duration, length, time_loss in zip(
        data_dict["vehicles"],
        data_dict["arrivals"],
        data_dict["durations"],
        data_dict["route_lengths"],
        data_dict["time_losses"],
    ):
        data.append(
            {
                "episode": episode,
                "vehicle_id": vid,
                "arrival": arrival,
                "duration": duration,
                "length": length,
                "time_loss": time_loss,
            }
        )
    return data


def extract_dict(parser, config_section):
    return {
        name: parser.extract_many(xpath, str) for name, xpath in config_section.items()
    }


def parse_fcd(episode):
    parser = Parser(FCD)
    data = parser.extract_fcd_flat(episode)

    return data


def prepare_actions(episode, actions):
    rows = []
    for agent, action in actions.items():
        rows.append({"episode": episode, "agent_id": agent, "action": action})
    return rows


def prepare_rewards(episode, rewards):
    rows = []
    for agent, reward in rewards.items():
        rows.append({"episode": episode, "agent_id": agent, "reward": reward})
    return rows


def prepare_BM_data(episode, agents):
    rows = []
    for _, agent in agents.items():
        for route_id, PT in enumerate(agent.PT):
            rows.append(
                {
                    "episode": episode,
                    "agent_id": agent.id,
                    "ET": agent.ET,
                    "stimulus": agent.stimulus,
                    "route_id": route_id,
                    "PT": float(PT),
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
    sys.exit()
