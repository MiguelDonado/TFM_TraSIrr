"""
CLI driver for RQ7's edge-flow visualization.

Wraps run_edge_visualization() (sumo_edge_analysis.py) so it can be called
from RQ7.qmd (R) via system2(), one call per (mode, metric, algorithm)
combination, against the files scripts/run_analysis.py RQ7 downloaded from
MLflow into r/RQ7/data/ (not the live local data/ files, which may belong
to an unrelated, more recent run by the time the report is rendered).

Usage
-----
  python src/analysis/run_rq7_edge_viz.py --mode aggregated --metric density --algorithm BM

  python src/analysis/run_rq7_edge_viz.py --mode interval --period 900 --metric entered \
      --algorithm duaIterate

r/RQ7/data/ must already contain the five files written by
scripts/run_analysis.py's _prepare_rq7_data():
  bm_edgedata.parquet, dua_edgedata.parquet, times_interval.parquet,
  routes_bm.rou.xml, routes_dua.rou.xml

edgedata_BM_file and edgedata_duaIterate_file are always both passed to
run_edge_visualization() regardless of --algorithm, since the color scale
is computed from the max across both algorithms (see sumo_edge_analysis.py
module docstring) so the two replays stay visually comparable. --algorithm
only picks which one's routes are actually driven in the sumo-gui replay.
"""

import argparse
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RQ7_DESIGN = BASE_DIR / "experiments" / "rq7" / "design.yaml"
DATA_DIR = BASE_DIR / "r" / "RQ7" / "data"

sys.path.insert(0, str(BASE_DIR / "src"))
from analysis.sumo_edge_analysis import run_edge_visualization
from config.paths import (
    GUI_SETTINGS,
    GUI_SETTINGS_AGGREGATED,
    MEANDATA,
    MEANDATA_AGGREGATED,
    SUMO_CONF,
    SUMO_CONF_AGGREGATED,
)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["aggregated", "interval"], required=True)
    parser.add_argument("--metric", choices=["entered", "density"], required=True)
    parser.add_argument("--algorithm", choices=["BM", "duaIterate"], required=True)
    parser.add_argument("--period", type=int, default=900)
    return parser.parse_args()


def _simulation_end_time():
    """
    end_time = warm_up_time + simulation_time of the base config RQ7's
    simulation run used, mirroring config.config's own end_time
    computation (see src/config/config.py) without needing to import
    config.config itself, which expects to be run as `main.py <config>`.
    """
    with open(RQ7_DESIGN) as f:
        base_config_path = yaml.safe_load(f)["base_config"]
    with open(base_config_path) as f:
        simulation = yaml.safe_load(f)["simulation"]
    return simulation["warm_up_time"] + simulation["simulation_time"]


def main():
    args = _parse_args()

    routes_file = DATA_DIR / ("routes_bm.rou.xml" if args.algorithm == "BM" else "routes_dua.rou.xml")

    run_edge_visualization(
        generic_config=SUMO_CONF,
        config_visualization=SUMO_CONF_AGGREGATED,
        generic_gui_settings=GUI_SETTINGS,
        gui_settings_visualization=GUI_SETTINGS_AGGREGATED,
        edgedata_BM_file=DATA_DIR / "bm_edgedata.parquet",
        edgedata_duaIterate_file=DATA_DIR / "dua_edgedata.parquet",
        generic_meandata=MEANDATA,
        meandata_visualization=MEANDATA_AGGREGATED,
        routes_file=routes_file,
        metric=args.metric,
        period=args.period,
        aggregated=args.mode == "aggregated",
        simulation_end_time=_simulation_end_time(),
        times_interval_file=DATA_DIR / "times_interval.parquet",
    )


if __name__ == "__main__":
    main()