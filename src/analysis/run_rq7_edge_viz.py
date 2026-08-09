"""
CLI driver for RQ7's edge-flow visualization.

Wraps run_edge_visualization() (sumo_edge_analysis.py) so it can be called
from RQ7.qmd (R) via system2(), one call per (mode, metric, algorithm)
combination, against the files scripts/run_analysis.py RQ7 downloaded from
MLflow into r/RQ7/data/ (not the live local data/ files, which may belong
to an unrelated, more recent run by the time the report is rendered).

Usage
-----
  python run_rq7_edge_viz.py --mode aggregated --metric density \
      --algorithm BM --data-dir <dir>

  python run_rq7_edge_viz.py --mode interval --period 900 --metric entered \
      --algorithm duaIterate --data-dir <dir>

--data-dir must contain the five files written by
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

RQ7_DESIGN = Path(__file__).resolve().parent.parent.parent / "experiments" / "rq7" / "design.yaml"


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["aggregated", "interval"], required=True)
    parser.add_argument("--metric", choices=["entered", "density"], required=True)
    parser.add_argument("--algorithm", choices=["BM", "duaIterate"], required=True)
    parser.add_argument("--period", type=int, default=900)
    parser.add_argument("--data-dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = _parse_args()

    # config.config runs its own argparse.parse_args() on import (it expects
    # a single positional config-file path), which would otherwise collide
    # with the CLI args parsed above. Reset sys.argv to what it expects,
    # using the same base_config RQ7's simulation run used, so config.end_time
    # (needed for interval breakpoints) matches that run.
    with open(RQ7_DESIGN) as f:
        base_config = yaml.safe_load(f)["base_config"]
    sys.argv = [sys.argv[0], base_config]

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from analysis.sumo_edge_analysis import run_edge_visualization
    from config.paths import (
        GUI_SETTINGS,
        GUI_SETTINGS_AGGREGATED,
        MEANDATA,
        MEANDATA_AGGREGATED,
        SUMO_CONF,
        SUMO_CONF_AGGREGATED,
    )

    data_dir = args.data_dir
    routes_file = data_dir / ("routes_bm.rou.xml" if args.algorithm == "BM" else "routes_dua.rou.xml")

    run_edge_visualization(
        generic_config=SUMO_CONF,
        config_visualization=SUMO_CONF_AGGREGATED,
        generic_gui_settings=GUI_SETTINGS,
        gui_settings_visualization=GUI_SETTINGS_AGGREGATED,
        edgedata_BM_file=data_dir / "bm_edgedata.parquet",
        edgedata_duaIterate_file=data_dir / "dua_edgedata.parquet",
        generic_meandata=MEANDATA,
        meandata_visualization=MEANDATA_AGGREGATED,
        routes_file=routes_file,
        metric=args.metric,
        period=args.period,
        aggregated=args.mode == "aggregated",
        times_interval_file=data_dir / "times_interval.parquet",
    )


if __name__ == "__main__":
    main()