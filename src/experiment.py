# This file is about: (running episodes, parsing output, creating dataframes and saving the results...). That is experiment logic
import yaml

from io_module.parser import Parser
from paths import FCD, STATISTICS, TRIPS_INFO, VEHROUTE, YAML_CONF

# Load YAML file
with open(YAML_CONF, "r") as file:
    config = yaml.safe_load(file)


def parse_aggregated_data(episode):
    statistics = parse_statistics()
    return {"episode": episode, **statistics}


def parse_statistics():
    data = {}
    parser = Parser(STATISTICS)

    for name, xpath in config["metrics"]["statistics"].items():
        value = parser.extract_one(xpath, float)
        data[name] = value
    return data


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
