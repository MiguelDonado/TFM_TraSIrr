"""
Purpose of this file: Orchestration + Pipeline
1. Saving results
2. Handling the data structure in which results are stored
"""

import pandas as pd
import yaml

from parsing.parser import Parser
from paths import (
    FCD,
    FCD_PROCESSED,
    STATISTICS,
    STATISTICS_PROCESSED,
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


def parse_output(episode):
    aggregated_result = parse_aggregated_data(episode)
    vehroute_result = parse_vehroute(episode)
    trips_info_result = parse_trips_info(episode)
    fcd_result = parse_fcd(episode)
    return {
        "aggregated_result": aggregated_result,
        "vehroute_result": vehroute_result,
        "trips_info_result": trips_info_result,
        "fcd_result": fcd_result,
    }


def accumulate_results(results, result):
    mapping = {
        "aggregated": ("aggregated_result", "append"),
        "vehroute": ("vehroute_result", "extend"),
        "trips_info": ("trips_info_result", "extend"),
        "fcd": ("fcd_result", "extend"),
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
    }

    for key, path in mapping.items():
        df = pd.DataFrame(results[key])
        df.to_parquet(path, engine="pyarrow")


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
