import yaml
from lxml import etree

from paths import FCD_XML, STATISTICS_XML, YAML_CONF

from .parser import Parser

# Load YAML file
with open(YAML_CONF, "r") as file:
    config_parser = yaml.safe_load(file)


def parse_aggregated_data(episode):
    data = {}
    parser = Parser(STATISTICS_XML)

    for name, xpath in config_parser["metrics"]["statistics"].items():
        value = parser.extract_one(xpath, float)
        data[name] = value
    return {"episode": episode, **data}


def parse_vehroute(episode, vehroute_path):
    data = []
    parser = Parser(vehroute_path)

    data_dict = parse_section_to_raw_strings(
        parser, config_parser["metrics"]["vehroute"]
    )

    for name, xpath in config_parser["metrics"]["vehroute"].items():
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


def parse_trips_info(episode, trips_info_path):
    data = []
    parser = Parser(trips_info_path)

    data_dict = parse_section_to_raw_strings(
        parser, config_parser["metrics"]["tripsinfo"]
    )

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


def parse_section_to_raw_strings(parser, config_section):
    return {
        name: parser.extract_many(xpath, str) for name, xpath in config_section.items()
    }


def parse_fcd(episode):
    parser = Parser(FCD_XML)
    data = parser.extract_fcd_flat(episode)

    return data


def parse_edgedata(episode, edgedata_path):
    data = []

    document = edgedata_path
    tree = etree.parse(document)

    interval_elements = tree.xpath("//interval")

    for i, interval_element in enumerate(interval_elements):
        edges = interval_element.xpath(".//edge")

        for edge in edges:
            data.append(
                {
                    "episode": episode,
                    "interval": i,
                    "edge": edge.get("id"),
                    "entered": edge.get("entered"),
                    "density": edge.get("density"),
                }
            )
    return data
