# This file is about: (running episodes, parsing output, creating dataframes and saving the results...). That is experiment logic
import pandas as pd
import yaml

from io_module.parser import Parser
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


def parse_aggregated_data(episode):
    data = {}
    parser = Parser(STATISTICS)

    for name, xpath in config["metrics"]["statistics"].items():
        value = parser.extract_one(xpath, float)
        data[name] = value
    return {"episode": episode, **data}


def parse_vehroute(episode):
    data_dict = {}
    data = []
    parser = Parser(VEHROUTE)

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
    data_dict = {}
    data = []
    parser = Parser(TRIPS_INFO)

    for name, xpath in config["metrics"]["tripsinfo"].items():
        values = parser.extract_many(xpath, str)
        data_dict[name] = values

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


def parse_fcd(episode):
    parser = Parser(FCD)
    data = parser.extract_fcd_flat(episode)

    return data


def accumulate_results(results, result):
    results["aggregated"].append(result["aggregated_result"])
    results["vehroute"].extend(result["vehroute_result"])
    results["trips_info"].extend(result["trips_info_result"])
    results["fcd"].extend(result["fcd_result"])


def save_processed_data(results):
    aggregated_df = pd.DataFrame(results["aggregated"])
    aggregated_df.to_parquet(STATISTICS_PROCESSED, engine="pyarrow")

    vehroute_df = pd.DataFrame(results["vehroute"])
    vehroute_df.to_parquet(VEHROUTE_PROCESSED, engine="pyarrow")

    trips_info_df = pd.DataFrame(results["trips_info"])
    trips_info_df.to_parquet(TRIPS_INFO_PROCESSED, engine="pyarrow")

    fcd_df = pd.DataFrame(results["fcd"])
    fcd_df.to_parquet(FCD_PROCESSED, engine="pyarrow")
