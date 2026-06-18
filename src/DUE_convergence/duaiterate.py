import gzip
import shutil
import subprocess
from collections import defaultdict

import pandas as pd
from lxml import etree

from config.config import config
from parsing.sumo_outputs import parse_edgedata, parse_trips_info, parse_vehroute
from paths import BASE_DIR, TRIPS_duaIterate
from utils.od_routes import od_routes_to_rows
from utils.sumo_xml import write_meandata_file


def run_duarouter(network, trips_file, routes_file, weights_file, seed):
    cmd = [
        "duarouter",
        "-n",
        network,
        "--route-files",
        trips_file,
        "--weight-files",
        weights_file,
        "--write-costs",
        "true",
        "-o",
        routes_file,
        "--seed",
        str(seed),
    ]

    subprocess.run(cmd, check=True)

    # Delete alternative route files (undesirable)
    alt_route_file_to_delete = routes_file.with_name(
        f"{routes_file.stem}.alt{routes_file.suffix}"
    )
    if alt_route_file_to_delete.exists():
        alt_route_file_to_delete.unlink()


def generate_trips_file_duaIterate(agents):
    with open(TRIPS_duaIterate, "w") as f:
        f.write(f"<routes>\n")
        for i, agent in enumerate(agents):
            f.write(
                f"""\t<trip id="{agent["id"]}" from="{agent["origin"]}" to="{agent["destination"]}" depart="{agent["departure_time"]}"/>\n"""
            )
        f.write("</routes>\n")


def call_duaIterate(network, max_iterations):
    cmd = [
        "duaIterate.py",
        "-n",
        network,
        "-t",
        TRIPS_duaIterate,
        "--last-step",
        str(max_iterations),
        "sumo--step-length",
        "0.1",
        "sumo--vehroute-output",
        "vehroute.xml",
        "sumo--vehroute-output.exit-times",
        "true",
    ]

    subprocess.run(cmd, check=True)


def run_simulation_duaIterate(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)
    path_config_file = BASE_DIR / folder_number / f"iteration_{folder_number}.sumocfg"
    cmd = ["sumo-gui", "-c", path_config_file]
    subprocess.run(cmd, check=True)


def delete_duaIterate_folders(max_iterations):
    target_numbers = [str(number).zfill(3) for number in range(max_iterations)]

    for number in target_numbers:
        path_to_delete = BASE_DIR / number
        shutil.rmtree(path_to_delete)


def extract_routes_file_duaIterate(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration duaIterate
    folder_path = BASE_DIR / folder_number

    # Path of gzip file that contains routes generated from duaIterate
    gzip_path = folder_path / f"trips_duaIterate_{folder_number}.rou.xml.gz"

    # Path of xml file that contains routes generated from duaIterate
    xml_path = folder_path / f"trips_duaIterate_{folder_number}.rou.xml"

    # Decompress gzip file to get xml file with routes generated from duaIterate
    _decompress_gzip(gzip_path, xml_path)

    return xml_path


def _decompress_gzip(gzip_path, xml_path):
    """
    Decompress a gzip file
    """
    with gzip.open(gzip_path, "rb") as f_in:
        with open(xml_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


def compute_od_routes_table_duaIterate(routes_file, output_file):
    """
    This function computes the od routes table used during computation Rgap
    """
    # Dictionary with agents_id as keys, and routes (list of edges) as values
    dict_agent_routes = _parse_routes(routes_file)

    # Extract all routes used by agents (route = all its edges)
    all_routes = dict_agent_routes.values()

    # Get unique routes (route = all its edges)
    unique_routes = _get_unique_routes(all_routes)

    # Build od_routes dictionary
    od_routes = _build_od_routes_dict(unique_routes)

    # Put od_routes in right format to store in parquet file
    processed_od_routes = _process_od_routes(od_routes)

    df = pd.DataFrame(processed_od_routes)
    df.to_parquet(output_file, engine="pyarrow")

    return dict_agent_routes, od_routes


def compute_actions_table_duaIterate(agents, dict_agent_routes, od_routes, output_file):
    """
    Compute actions table used during Rgap computation
    """
    actions = []

    for agent in agents:
        agent_id = agent["id"]
        od = (agent["origin"], agent["destination"])
        route = dict_agent_routes[agent_id]
        idx_route = od_routes[od].index(route)
        actions.append({"episode": 1, "agent_id": agent_id, "action": idx_route})

    df = pd.DataFrame(actions)
    df.to_parquet(output_file, engine="pyarrow")


def process_trips_info_duaIterate(max_iterations, output_file):
    """
    Builds the processed trips info file
    """
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration duaIterate
    folder_path = BASE_DIR / folder_number

    # Raw trips info path
    trips_info_duaIterate_path = folder_path / f"tripinfo_{folder_number}.xml"

    # Parse trips info
    processed_data = parse_trips_info(
        episode=1, trips_info_path=trips_info_duaIterate_path
    )

    # Save trips info processed data in a parquet file
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")


def process_vehroute_duaIterate(max_iterations, output_file):
    """
    Builds the processed vehroute file
    """
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration duaIterate
    folder_path = BASE_DIR / folder_number

    # Raw vehroutes path
    vehroute_path = folder_path / "vehroute.xml"

    # Parse vehroutes
    processed_data = parse_vehroute(episode=1, vehroute_path=vehroute_path)

    # Save vehroutes processed data in a parquet file
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")


def process_edgedata_duaIterate(max_iterations, output_file):
    """
    Builds the processed vehroute file
    """
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration duaIterate
    folder_path = BASE_DIR / folder_number

    # Raw edgedata path
    edgedata_path = folder_path / "edgedata_duaIterate.xml"

    # Parse edgedata
    processed_data = parse_edgedata(episode=1, edgedata_path=edgedata_path)

    # Save vehroutes processed data in a parquet file
    df = pd.DataFrame(processed_data)
    df.to_parquet(output_file, engine="pyarrow")


def _parse_routes(routes_file):
    """
    Returns a dictionary that contains:
    - keys: agents_id
    - values: route (list with all the edges)
    """
    document = routes_file
    tree = etree.parse(document)

    # Routes
    vehicles = tree.xpath("//vehicle")
    agent_ids = [vehicle.xpath("@id")[0] for vehicle in vehicles]
    routes = [vehicle.xpath("route/@edges")[0] for vehicle in vehicles]
    edges = [route.split(" ") for route in routes]

    # Check
    assert len(edges) == len(agent_ids)

    return dict(zip(agent_ids, edges))


def _get_unique_routes(routes):
    unique_routes = [list(x) for x in set(tuple(inner) for inner in routes)]
    return unique_routes


def _build_od_routes_dict(unique_routes):
    # Initialize dictionary that will store as keys unique ods, and as values a list with all the used routes for that od
    od_routes = defaultdict(list)
    for route in unique_routes:
        od = (route[0], route[-1])
        od_routes[od].append(route)
    return od_routes


def _process_od_routes(od_routes):
    """
    I want this format
    origin | dest | route_id | step | edge
    A         B      1          1       e1
    A         B      1          2       e5 ...
    """
    return od_routes_to_rows(od_routes)


def generate_meandata_file(max_iterations):
    folder_number = _last_iteration_folder(max_iterations)

    # Path of the folder that contains last iteration duaIterate
    folder_path = BASE_DIR / folder_number

    path = folder_path / "meandata_duaIterate.xml"

    write_meandata_file(path, "../edgedata_duaIterate.xml", config.time_interval)

    return path


def generate_edgedata_file(max_iterations, meandata_duaIterate_file):
    folder_number = _last_iteration_folder(max_iterations)
    path_config_file = BASE_DIR / folder_number / f"iteration_{folder_number}.sumocfg"

    tree = etree.parse(path_config_file)

    # Find and remove the additional-files element
    for elem in tree.xpath("//additional-files"):
        elem.getparent().remove(elem)

    tree.write(
        path_config_file, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )

    cmd = [
        "sumo",
        "-c",
        path_config_file,
        "--additional-files",
        meandata_duaIterate_file,
    ]

    subprocess.run(cmd, check=True)


def _last_iteration_folder(max_iterations: int):
    """
    Return zero-padded folder name for the last duaIterate iteration.
    """
    return str(max_iterations - 1).zfill(3)
