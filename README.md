# Day-to-Day MARL Route-Choice Model

**Research thesis** — Universidad Politècnica de Catalunya (UPC) · 2026

The objective of this thesis was to investigate whether a day-to-day multi-agent reinforcement learning (MARL) approach to route choice — in which agents learn solely from their own experiences — converges to a Dynamic User Equilibrium (DUE) within a dynamic traffic assignment (DTA) setting, using a microscopic traffic simulation. First, the study examined whether a DUE would emerge from the learning process of rational agents using a reinforcement learning approach. Second, more realistic behavioral traits were integrated into the agents' decision-making to examine how these traits affect the learning process and whether a DUE would still emerge.

📄 [Read the full thesis document](thesis_document/thesis.pdf)

---

## Demo

A short walkthrough of the pipeline in action:

![Demo of the pipeline](demo/demo.gif)

---

## Background

Traffic assignment models estimate how travel demand distributes itself across a road network. [This diagram](<thesis_document/media/4.LiteratureReview/MapTrafficAssignment(2)(1).drawio.pdf>) situates the day-to-day learning approach studied here among the broader family of traffic assignment methods.

---

## Thesis Objectives

This thesis is guided by the following primary research questions:

- **(Rational Agent)** Does a multi-agent reinforcement learning approach, following the Bush-Mosteller learning rule, converge toward a dynamic user equilibrium (DUE) when applied within a microscopic traffic simulation environment?
- **(Memory Sensitivity)** Does reducing agents' memory level — how quickly older experiences lose weight relative to more recent ones when forming perceptions — prevent the model from converging toward a DUE state, and how does it affect route-choice behavior?
- **(Learning-Rate Sensitivity)** Does reducing agents' learning rate — how quickly they update their beliefs in response to new experience — prevent the model from converging toward a DUE state, and how does it affect route-choice behavior?
- **(Disruption Recovery)** If a link is temporarily disrupted and then restored, does the model recover the same route-choice equilibrium it had reached before the disruption?
- **(Risk Aversion)** How does incorporating travel-time variability into a route's perceived cost, making agents sensitive to risk, not just to mean travel time, affect route-choice behavior and convergence toward a DUE state?
- **(Waiting-Time Aversion)** How does incorporating time spent stopped into a route's perceived cost, making agents sensitive to waiting, not just to mean travel time, affect route-choice behavior and convergence toward a DUE state?
- **(Nonlinear Response)** How does introducing a nonlinear response to perceived travel-time differences — reflecting that people tend to ignore small differences, but once a difference becomes noticeable, react increasingly strongly — affect route-choice behavior and convergence toward a DUE state?
- **(Heterogeneous Memory)** Whether considering populations of drivers with different memory levels changes convergence behavior compared with a homogeneous population.
- **(Spatial Traffic Comparison)** A comparison between the implemented algorithm and the SUMO `duaIterate` benchmark algorithm.

---

## Results

### Rational Agent

The first research question examined whether a MARL approach based on the Bush-Mosteller algorithm could lead to a DUE state under the assumption of rational drivers. The results show that, under these assumptions, the agents converge to a DUE state through their individual learning process. Consequently, DUE can emerge not only through a conventional iterative assignment procedure but also through a MARL approach, where equilibrium results from individual route-choice decisions.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ1/plot1_rgap_evolution.png" width="32%" alt="R-gap evolution across episodes">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ1/plot2_refined_rgap_heatmap.png" width="32%" alt="Refined R-gap heatmap by departure interval">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ1/plot4_distribution_final_od_r_gap.png" width="32%" alt="Distribution of final OD-level R-gap">
</p>

### Spatial Traffic Comparison

The second research question compared the spatial traffic patterns produced by the proposed Bush-Mosteller MARL approach with those obtained using the `duaIterate` benchmark. The resulting flows on the links were similar between the two approaches. However, at the path level, the Bush-Mosteller MARL approach distributed traffic more broadly among the available routes, whereas `duaIterate` concentrated traffic on fewer routes.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ7/plot_route_composition_1.png" width="32%" alt="Route composition comparison, OD pair 1">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ7/plot_route_composition_5.png" width="32%" alt="Route composition comparison, OD pair 5">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ7/plot_route_composition_6.png" width="32%" alt="Route composition comparison, OD pair 6">
</p>

### Memory Sensitivity

The third research question investigated the effect of memory. Lower memory levels increased route-flow variability. However, for the synthetic network and demand configuration considered, all tested memory levels still converged to DUE.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ2/plot1_rgap_evolution_mem_seed.png" width="48%" alt="R-gap evolution across episodes for different memory levels">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ2/plot3_route_flow_stability.png" width="48%" alt="Route-flow stability by memory level">
</p>

### Disruption Recovery

The influence of memory became more apparent when considering a temporary disruption: lower memory enabled faster adaptation to the disruption and partial recovery after the network was restored, whereas perfect memory resulted in slower adaptation and persistent avoidance of the previously disrupted routes.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/disrupted_network.png" width="32%" alt="Disrupted network segment">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/plot1_rgap_evolution.png" width="32%" alt="R-gap evolution around the disruption">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/plot2_flow_disrupted_edges_evolution.png" width="32%" alt="Flow evolution on disrupted edges">
</p>

### Learning-Rate Sensitivity

The fifth research question examined the effect of learning rate. For the synthetic network and demand configuration considered, all tested learning rates converged towards DUE. Higher learning rates accelerated both the learning process and the attainment of DUE, although they resulted in slightly higher final R-gap values. These results may differ in more complex network and demand configurations with more frequent changes in the cost ranking of routes across episodes, where memory and learning rate may have a stronger influence on the learning dynamics and convergence towards DUE.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ3/plot1_rgap_evolution_l_seed.png" width="48%" alt="R-gap evolution across episodes for different learning rates">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ3/plot4_route_flow_stability.png" width="48%" alt="Route-flow stability by learning rate">
</p>

### Risk Aversion

The sixth research question investigated the effect of risk-sensitive behavior. The results indicate that the tested homogeneous populations, in which all drivers shared the same risk-aversion parameter, generally failed to converge towards DUE.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ11/plot1_risk_sensitivity_mechanism.png" width="48%" alt="Risk-sensitivity mechanism">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ11/plot2_convergence_plot.png" width="48%" alt="Convergence under risk sensitivity">
</p>

### Waiting-Time Aversion

The seventh research question investigated the effect of waiting-time sensitive behavior. The results indicate that the tested homogeneous populations, in which all drivers shared the same waiting-time sensitivity parameter, generally failed to converge towards DUE.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ12/plot1_waitingTime_sensitivity_mechanism.png" width="48%" alt="Waiting-time sensitivity mechanism">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ12/plot2_convergence_plot.png" width="48%" alt="Convergence under waiting-time sensitivity">
</p>

### Nonlinear Response

Finally, the eighth research question investigated the nonlinear reinforcement mechanism and its interaction with memory. The results showed that high values of τ (the dead-zone parameter) can prevent convergence towards DUE, particularly when combined with higher memory levels.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ13/plot1_nonlinear_mechanism.png" width="48%" alt="Nonlinear stimulus mechanism">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ13/plot2_rgap_evolution.png" width="48%" alt="R-gap evolution under the nonlinear mechanism">
</p>

### Summary

Overall, the results suggest that the proposed model converges to DUE under its more rational formulation, while variations in the existing behavioral parameters, namely memory level and learning rate, do not necessarily prevent convergence under the tested scenario. However, their influence may become stronger in more complex network-demand configurations with more frequent changes in the cost ranking of routes across episodes. Previous research has shown that lower memory levels can prevent convergence to UE in a STA setting where changes in route-cost ranking occur more frequently (Wei et al., 2014).

The introduction of additional behavioral mechanisms, such as waiting-time sensitivity, risk aversion, and nonlinear response, can prevent convergence towards DUE. These results suggest that incorporating more realistic behavioral mechanisms into the agents' decision-making can prevent the network from reaching DUE, as reflected by higher R-gap values, although the effect depends on the behavioral parameters and the network-demand configuration.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Traffic simulation | SUMO (Simulation of Urban MObility) |
| Reinforcement learning | Python |
| Experiment tracking | MLflow |
| Big Data | Arrow |
| Data Science | R · tidyverse · Quarto |
| Containerization | Docker |

---

## Networks

**Sioux Falls** — the standard transportation research benchmark network used for all main experiments: 24 nodes, 76 directed edges, no traffic lights, uniform free-flow speed.

[View the network diagram](<thesis_document/media/5.ExperimentalDesign_Evaluation/2.ExperimentalDesign/Sioux_Falls.drawio.pdf>)

---

## Software Architecture

[View the main program architecture diagram](<thesis_document/media/5.ExperimentalDesign_Evaluation/1.Implementation/MainProgram.pdf>)

The traffic assignment model actually implemented in this project, alongside the general/textbook formulation it's adapted from, for reference:

- [Traffic assignment model — implemented](<thesis_document/media/1.Introduction/TrafficAssignmentModel_Implemented.pdf>)
- [Traffic assignment model — general formulation](<thesis_document/media/1.Introduction/TrafficAssignmentModel.pdf>)

---

## Getting Started with Docker

The training/simulation/tracking pipeline (Python, SUMO, MLflow) is fully containerized — no manual dependency setup needed beyond Docker itself. R/Quarto analysis is intentionally kept outside Docker: it's used interactively in RStudio, and `renv.lock` already pins its package versions.

**Prerequisites:** Docker with the Compose plugin (`docker compose version`).

### Get the image

Either pull the pre-built image (fast — skips compiling SUMO from source):
```sh
docker pull migueldonado/thesis-app:latest
docker tag migueldonado/thesis-app:latest thesis-app:latest
```
or build it yourself (~20 minutes, compiles SUMO 1.26.0 from source):
```sh
docker build -t thesis-app .
```

### One-time setup

Generate a `.env` file so containers run as your own user rather than root — otherwise files the container creates through the bind mount (logs, generated data, MLflow's database) end up owned by root on your host:
```sh
echo "UID=$(id -u)" > .env
echo "GID=$(id -g)" >> .env
```

### Running it

```sh
docker compose up -d                                       # start the app + mlflow containers
docker compose exec app python scripts/run_batch.py RQ1 --dev
docker compose exec app python scripts/run_analysis.py RQ1
docker compose exec app python scripts/manage_runs.py RQ1 --archive
docker compose down                                         # stop when done
```
MLflow UI: [http://localhost:5000](http://localhost:5000)

### GUI (optional, Linux only)

A separate compose file adds SUMO GUI support via X11 forwarding:
```sh
xhost +local:docker
docker compose -f docker-compose-gui.yml up -d
docker compose -f docker-compose-gui.yml exec app sumo-gui
xhost -local:docker   # revoke access when done
```

---

## Main Reference

Wei, F., Ma, S., & Jia, N. (2014). A Day-to-Day Route Choice Model Based on
Reinforcement Learning. *Mathematical Problems in Engineering*, 2014, 646548.
https://doi.org/10.1155/2014/646548