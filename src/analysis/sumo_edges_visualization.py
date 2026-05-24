import subprocess
from paths import ROUTES, SUMO_CONF_AGGREGATED
import pandas as pd
from shutil import copy2
from lxml import etree
import numpy as np

cmd = [
    "sumo-gui",
    "-c",
    SUMO_CONF_AGGREGATED,
]


def run_episode_color_edges(
    cmd,
    generic_config,
    config_visualization,
    generic_gui_settings,
    gui_settings_visualization,
    edgedata_BM_file,
    edgedata_dueIterate_file,
    generic_meandata,
    meandata_visualization,
    routes_file,
    metric,
    aggregated=True,
):

    # 1. Create config file
    create_config(
        generic_config=generic_config,
        config_visualization=config_visualization,
        aggregated=aggregated,
        routes_file=routes_file,
    )

    # 2. Create gui-settings
    create_gui_settings(
        generic_gui_settings=generic_gui_settings,
        gui_settings_visualization=gui_settings_visualization,
        aggregated=aggregated,
        edgedata_BM_file=edgedata_BM_file,
        edgedata_dueIterate_file=edgedata_dueIterate_file,
        metric=metric,
    )

    # 3. Create meandata file
    create_meandata(
        meandata_visualization=meandata_visualization,
        aggregated=aggregated,
        generic_meandata=generic_meandata,
    )

    # 3. Update config file (add gui-settings file)
    update_config(
        config_visualization=config_visualization,
        gui_settings_visualization=gui_settings_visualization,
        meandata_visualization=meandata_visualization,
    )

    # 4. Run episode
    subprocess.run(cmd)

    # # Then is gonna be run on interval specific mode
    # if times_interval_file:
    #     # So we have to do a few things:

    #     # 1. Set breakpoints
    #     str_breakpoints = generate_breakpoints(times_interval_file)
    #     additional_cmd_b = [
    #         "--breakpoints",
    #         str_breakpoints,
    #     ]

    #     # 2. Set meandata file

    # additional_cmd = [
    #     "--gui-settings-file",
    #     GUI_SETTINGS,
    # ]
    # cmd.extend(additional_cmd)


def create_config(generic_config, config_visualization, aggregated, routes_file):
    # 1. Copy basic config file
    copy2(generic_config, config_visualization)

    # 2. Remove unnecessary stuff
    tree = etree.parse(config_visualization)
    report = tree.xpath("//report")[0]
    report.getparent().remove(report)
    device = tree.xpath("//device")[0]
    device.getparent().remove(device)

    if aggregated:
        # Update meandata file
        additional_files = tree.xpath("//additional-files")[0]
        additional_files.attrib.pop("value", None)

    # 3. Add route file
    # Find input section
    input_section = tree.find(".//input")

    # Create route-files element
    route_files = etree.Element("route-files")
    route_files.attrib["value"] = str(routes_file)

    # Append to input section
    input_section.append(route_files)

    # 4. Write updated XML back to file
    tree.write(
        str(config_visualization),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def create_gui_settings(
    generic_gui_settings,
    gui_settings_visualization,
    metric,
    edgedata_dueIterate_file,
    edgedata_BM_file,
    aggregated,
):
    # 1. Copy generic gui-settings file
    copy2(generic_gui_settings, gui_settings_visualization)

    # 2. Get max value of given metric (between BM and dueIterate) edgeData file
    if aggregated:
        if metric == "entered":
            # Get max dueIterate (last iteration)
            df = pd.read_parquet(edgedata_dueIterate_file)
            # Convert the entered column to integer
            df[metric] = df[metric].astype(int)
            df_grouped = df.groupby("edge", as_index=False)["entered"].sum()
            max_value_dueIterate = df_grouped["entered"].max()

            # Get max BM (last episode)
            df = pd.read_parquet(edgedata_BM_file)
            last_episode = df["episode"].max()
            df_last_episode = df[df["episode"] == last_episode]
            # Convert the entered column to integer
            df_last_episode[metric] = df_last_episode[metric].astype(int)
            df_grouped = df_last_episode.groupby("edge", as_index=False)[
                "entered"
            ].sum()
            max_value_BM = df_grouped["entered"].max()

    max_value = max(max_value_dueIterate, max_value_BM)

    # 3. Compute the right threholds
    list_color_thresholds = compute_color_scale(max_value)

    # 4. Update gui_settings with the right thresholds
    set_color_scale_gui_settings(
        gui_settings_visualization, list_color_thresholds, aggregated
    )


def compute_color_scale(max_value):
    return np.round(np.linspace(0, max_value, 7), 2)


def set_color_scale_gui_settings(
    gui_settings_visualization, list_color_thresholds, aggregated
):
    tree = etree.parse(gui_settings_visualization)

    if aggregated:
        edges = tree.find(".//edges")
        edges.attrib["edgeDataID"] = "aggregated"
    # Get color schema
    color_scheme = tree.xpath("//colorScheme[@name='by live edgeData']")[0]

    # Get entries that have a threshold attribute
    entries = color_scheme.xpath("./entry[@threshold]")

    # Update thresholds
    for entry, threshold in zip(entries, list_color_thresholds):
        entry.attrib["threshold"] = str(threshold)

    # Write back to file
    tree.write(
        str(gui_settings_visualization),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def update_config(
    config_visualization, gui_settings_visualization, meandata_visualization
):
    tree = etree.parse(config_visualization)

    # Find input section
    input_section = tree.find(".//input")

    # Create gui-settings-file element
    gui_settings = etree.Element("gui-settings-file")
    gui_settings.attrib["value"] = str(gui_settings_visualization)

    # Append element
    input_section.append(gui_settings)

    additional_files = tree.xpath("//additional-files")[0]

    additional_files.attrib["value"] = str(meandata_visualization)

    # Pretty formatting
    etree.indent(tree, space="    ")

    tree.write(
        str(config_visualization),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def create_meandata(generic_meandata, meandata_visualization, aggregated):
    # 1. Copy generic gui-settings file
    copy2(generic_meandata, meandata_visualization)

    if aggregated:
        tree = etree.parse(meandata_visualization)
        edge_data = tree.find(".//edgeData")
        edge_data.attrib.pop("period", None)
        edge_data.attrib["id"] = "aggregated"

        tree.write(
            str(meandata_visualization),
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )


# def generate_breakpoints(times_interval_file):
#     df = pd.read_parquet(times_interval_file)

#     breakpoints = df["end_time"].astype(str).tolist()

#     return ",".join(breakpoints[0:5])
