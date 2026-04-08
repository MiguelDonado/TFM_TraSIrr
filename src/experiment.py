# This file is about: (running episodes, parsing output, creating dataframes and saving the results...). That is experiment logic
import yaml

from io_module.parser import Parser
from paths import STATISTICS, YAML_CONF

# Load YAML file
with open(YAML_CONF, "r") as file:
    config = yaml.safe_load(file)


def run_and_parse_output(env, episode):
    env.run_episode()
    stats = parse_statistics_output_file()
    return {"episode": episode, **stats}


def parse_statistics_output_file():
    # Quiero devolver un diccionario plano, de esa manera se puede convertir facilmente a df
    """
    Instead of this
    [
        {"name": "mean_routeLength", "value": 200.42},
        {"name": "timeLoss", "value": 50.1}
    ]

    I wanna return this
    {
        "mean_routeLength": 200.42,
        "timeLoss": 50.1
    }
    """
    results = {}
    parser = Parser(STATISTICS)

    for metric_name, metric_xpath in config["metrics"]["statistics_output"].items():
        value = parser.extract_one(metric_xpath, float)
        results[metric_name] = value
    return results
