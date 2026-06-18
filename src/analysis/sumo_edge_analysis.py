"""
This file is used to handle the color edge visualization in SUMO.
We will compare results of last episode BM with results of last iteration duaIterate

Several metrics could be used:
1. entered: Measures edge usage
2. density: Measures congestion
3. travel time: Great for DUE analysis (compare costs)

It is important to make sure that we are using the same scale for both visualizations (BM and duaIterate) and for all intervals,
the function max_value implements that logic.

Some gotchas regarding the metrics:
1. entered: When aggregating it we have to sum over intervals, and we would get right entered value for the aggregated case
2. density: When aggregating we have to do the mean over intervals to get the right value.
    Intuition why density has to be aggregated that manner:
        - Density is computed the following way: Take the nº vehicles on the edge for each timestep, and takes average
        (sum all nº vehicles divided by nºtimesteps).
    So the density represents the avg nº of cars over the time interval.
    So if we want the density over a bigger time interval, we have to take the average of the averages over small intervals.

Already checked in sumo-gui that density metric makes sense (not monotonic increasing, because is an avg)

"""

import subprocess
from shutil import copy2

import numpy as np
import pandas as pd
from lxml import etree

from config.config import config
from paths import TIMES_INTERVAL

# routes = [ROUTES, ROUTES_duaIterate]
# for route in routes:
#     run_edge_visualization(
#         aggregated=False,
#         config_visualization=SUMO_CONF_AGGREGATED,
#         generic_config=SUMO_CONF,
#         generic_gui_settings=GUI_SETTINGS,
#         gui_settings_visualization=GUI_SETTINGS_AGGREGATED,
#         edgedata_BM_file=EDGEDATA_PARQUET,
#         edgedata_duaIterate_file=EDGEDATA_duaIterate_PROCESSED,
#         generic_meandata=MEANDATA,
#         meandata_visualization=MEANDATA_AGGREGATED,
#         routes_file=route,
#         period=900,
#         metric="density",
#     )


def run_edge_visualization(
    generic_config,
    config_visualization,
    generic_gui_settings,
    gui_settings_visualization,
    edgedata_BM_file,
    edgedata_duaIterate_file,
    generic_meandata,
    meandata_visualization,
    routes_file,
    metric,
    period,
    aggregated=True,
):
    """
    The purpose of this function is to run the final episode of whatever algorithm,
    and perform one of the following visualizations:
        - overall edge usage ("entered" metric)
        - interval specific visualizations ("entered" metric)
    """

    # 1. Create separate config file to run the episode in which edges are colored
    create_config(
        generic_config=generic_config,
        config_visualization=config_visualization,
        routes_file=routes_file,
    )

    # 2. Create gui-settings
    create_gui_settings(
        generic_gui_settings=generic_gui_settings,
        gui_settings_visualization=gui_settings_visualization,
        aggregated=aggregated,
        edgedata_BM_file=edgedata_BM_file,
        edgedata_duaIterate_file=edgedata_duaIterate_file,
        metric=metric,
        period=period,
    )

    # 3. Create meandata file
    create_meandata(
        meandata_visualization=meandata_visualization,
        aggregated=aggregated,
        generic_meandata=generic_meandata,
        period=period,
    )

    # 4. Update config file (add gui-settings file)
    update_config(
        config_visualization=config_visualization,
        gui_settings_visualization=gui_settings_visualization,
        meandata_visualization=meandata_visualization,
    )

    # 5. Run episode
    cmd = [
        "sumo-gui",
        "-c",
        config_visualization,
    ]
    subprocess.run(cmd)


def create_config(generic_config, config_visualization, routes_file):
    """
    Basically:
        1. Make a copy of config file
        2. Remove unnecesary things config file
        3. Add route file
    """
    # 1. Copy basic config file
    copy2(generic_config, config_visualization)

    # 2. Remove unnecessary stuff
    tree = etree.parse(config_visualization)
    report = tree.xpath("//report")[0]
    report.getparent().remove(report)
    device = tree.xpath("//device")[0]
    device.getparent().remove(device)

    # Clean values of additional file element
    additional_files = tree.xpath("//additional-files")[0]
    additional_files.attrib.pop("value", None)

    # 3. Add route file
    # 3.1. Find input section
    input_section = tree.find(".//input")

    # 3.2. Create route-files element
    route_files = etree.Element("route-files")
    route_files.attrib["value"] = str(routes_file)

    # 3.3. Append to input section
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
    edgedata_duaIterate_file,
    edgedata_BM_file,
    aggregated,
    period,
):
    """
    Basically:
    1. Copy the generic gui-settings file
    2. Handle different cases:
        - Aggregated and metric entered
        - ...
    """
    # 1. Copy generic gui-settings file
    copy2(generic_gui_settings, gui_settings_visualization)

    # 2. Get max value of given metric (between BM and duaIterate) edgeData file
    max_value = get_max_value(
        metric=metric,
        edgedata_duaIterate_file=edgedata_duaIterate_file,
        edgedata_BM_file=edgedata_BM_file,
        aggregated=aggregated,
    )

    # 3. Compute the right threholds
    list_color_thresholds = compute_color_scale(max_value)

    # 4. Update gui_settings with the right thresholds
    set_color_scale_gui_settings(gui_settings_visualization, list_color_thresholds)

    # 5. Update attributes gui-settings
    set_attributes_gui_settings(
        metric=metric,
        aggregated=aggregated,
        gui_settings_visualization=gui_settings_visualization,
    )

    # 6. Set breakpoints
    if not aggregated:
        set_breakpoints_gui_settings(
            gui_settings_visualization=gui_settings_visualization, period=period
        )


def create_meandata(generic_meandata, meandata_visualization, aggregated, period):
    """
    Create the right meandata file, depending if we are in aggregate case or interval-specific
    """

    # 1. Copy generic meandata file
    copy2(generic_meandata, meandata_visualization)

    # 2. Handle different cases
    tree = etree.parse(meandata_visualization)
    edge_data = tree.find(".//edgeData")

    if aggregated:
        # The aggregation period the values the detector collects shall be summed up.
        # If not given the whole time interval from begin to end (see below) is aggregated.
        edge_data.attrib.pop("period", None)
        edge_data.attrib["id"] = "aggregated"

    else:
        edge_data.attrib["period"] = str(period)
        edge_data.attrib["id"] = "disaggregated"

    tree.write(
        str(meandata_visualization),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def update_config(
    config_visualization, gui_settings_visualization, meandata_visualization
):
    """
    Add gui-settings to config file
    """

    # Add gui-settings to config file
    tree = etree.parse(config_visualization)
    input_section = tree.find(".//input")
    gui_settings = etree.Element("gui-settings-file")
    gui_settings.attrib["value"] = str(gui_settings_visualization)
    input_section.append(gui_settings)

    # Add meandata to config file
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


############
# HELPERS
############


def get_max_value(
    metric, edgedata_duaIterate_file, edgedata_BM_file, aggregated, period=900
):
    """
    Get the max value of the metric, so the scale of colors can be set appropiately
    We only care about last episodes, that is what we want to analyze
    """

    # duaIterate
    df_due = pd.read_parquet(edgedata_duaIterate_file)
    max_value_duaIterate = process_df(df_due, metric, aggregated, period)

    # BM last episode
    df_BM = pd.read_parquet(edgedata_BM_file)
    last_episode = df_BM["episode"].max()
    df_BM = df_BM[df_BM["episode"] == last_episode]
    max_value_BM = process_df(df_BM, metric, aggregated, period)

    return max(max_value_duaIterate, max_value_BM)


def process_df(df: pd.DataFrame, metric: str, aggregated: bool, period: int) -> float:
    # Dimension table
    times_interval = pd.read_parquet(TIMES_INTERVAL)
    # Fact table
    df = df.copy()
    # Join
    df = df.merge(times_interval, on="interval")
    df[metric] = df[metric].astype(float)

    if aggregated:
        if metric == "entered":
            df_grouped = df.groupby("edge", as_index=False)[metric].sum()
        elif metric == "density":
            df_grouped = df.groupby("edge", as_index=False)[metric].mean()

    else:
        df["period"] = df["start_time"] // period
        if metric == "entered":
            df_grouped = df.groupby(["edge", "period"], as_index=False)[metric].sum()
        elif metric == "density":
            df_grouped = df.groupby(["edge", "period"], as_index=False)[metric].mean()

    return df_grouped[metric].max()


def compute_color_scale(max_value):
    """
    Compute the appropiate thresholds for the scale of colors
    """
    return np.round(np.linspace(0, max_value, 7), 2)


def set_attributes_gui_settings(aggregated, gui_settings_visualization, metric):
    """
    Update edgeDataID and edgeData attributes
    """

    tree = etree.parse(gui_settings_visualization)
    edges = tree.find(".//edges")
    if aggregated:
        edges.attrib["edgeDataID"] = "aggregated"
    else:
        edges.attrib["edgeDataID"] = "disaggregated"

    if metric == "entered":
        edges.attrib["edgeData"] = "entered"
    elif metric == "density":
        edges.attrib["edgeData"] = "density"

    # 3. Write back to gui-settings file
    tree.write(
        str(gui_settings_visualization),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def set_color_scale_gui_settings(gui_settings_visualization, list_color_thresholds):
    """
    Update the scale of colors thresholds in gui-settings
    """

    # 1. Name our color scheme for live edge data consistently
    tree = etree.parse(gui_settings_visualization)

    # 2. Update threshold values
    color_scheme = tree.xpath("//colorScheme[@name='by live edgeData']")[0]
    entries = color_scheme.xpath("./entry[@threshold]")
    for entry, threshold in zip(entries, list_color_thresholds):
        entry.attrib["threshold"] = str(threshold)

    # 3. Write back to gui-settings file
    tree.write(
        str(gui_settings_visualization),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def set_breakpoints_gui_settings(
    gui_settings_visualization,
    period,
):
    # SUMO-GUI breakpoint fires 2 s before the interval boundary, otherwise the visualization is reseted and
    # colors cannot be visualized anymore
    BREAKPOINT_LEAD_S = 2

    # 0. Compute list of breakpoints
    breakpoints = list(
        range(
            period - BREAKPOINT_LEAD_S,
            config.end_time + period - BREAKPOINT_LEAD_S,
            period,
        )
    )

    # 1. Add breakpoints
    tree = etree.parse(gui_settings_visualization)
    root = tree.getroot()

    for bp in breakpoints:
        breakpoint_elem = etree.Element("breakpoint")
        breakpoint_elem.attrib["time"] = f"{bp:.2f}"
        root.append(breakpoint_elem)

    # Pretty formatting
    etree.indent(tree, space="    ")

    # Write back
    tree.write(str(gui_settings_visualization), xml_declaration=True, encoding="UTF-8")
