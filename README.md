# Day-to-Day MARL Route-Choice Model

**Research thesis** — Universidad Politècnica de Catalunya (UPC) · 2026

The objective of this thesis was to investigate whether a day-to-day multi-agent reinforcement learning (MARL) approach to route choice — in which agents learn solely from their own experiences — converges to a Dynamic User Equilibrium (DUE) within a dynamic traffic assignment (DTA) setting, using a microscopic traffic simulation. First, the study examined whether a DUE would emerge from the learning process of rational agents using a reinforcement learning approach. Second, more realistic behavioral traits were integrated into the agents' decision-making to examine how these traits affect the learning process and whether a DUE would still emerge.

📄 [Read the full thesis document](thesis_document/thesis.pdf)

---

## 🎥 Video Tutorials

> [!IMPORTANT]
> **Watch these videos before using the application.** They walk through setup, running experiments, and how the code works.
>
> 1. ▶️ **[How to Set Up the Application Using Docker](https://youtu.be/LwC15-2MZUQ)**
> 2. ▶️ **[Experiment Workflow Explained: Create, Modify & Run](https://youtu.be/YFuyVfsoclA)**
> 3. ▶️ **[Understanding Program Logic Through Debugging](https://youtu.be/UnxYVW0cfpg)**

---

## Table of Contents

- [Day-to-Day MARL Route-Choice Model](#day-to-day-marl-route-choice-model)
  - [🎥 Video Tutorials](#-video-tutorials)
  - [Table of Contents](#table-of-contents)
  - [Demo](#demo)
  - [Background](#background)
  - [Thesis Objectives](#thesis-objectives)
  - [Tech Stack](#tech-stack)
  - [Networks](#networks)
  - [Software Architecture](#software-architecture)
  - [Workflow](#workflow)
  - [Results](#results)
    - [Rational Agent](#rational-agent)
    - [Spatial Traffic Comparison](#spatial-traffic-comparison)
    - [Memory Sensitivity](#memory-sensitivity)
    - [Disruption Recovery](#disruption-recovery)
    - [Learning-Rate Sensitivity](#learning-rate-sensitivity)
    - [Risk Aversion](#risk-aversion)
    - [Waiting-Time Aversion](#waiting-time-aversion)
    - [Nonlinear Response](#nonlinear-response)
    - [Summary](#summary)
  - [Getting Started (Simulation and Tracking)](#getting-started-simulation-and-tracking)
    - [Setup](#setup)
    - [Running it (without GUI support)](#running-it-without-gui-support)
    - [Check experiments in MLflow UI:](#check-experiments-in-mlflow-ui)
  - [Getting Started (Data Science)](#getting-started-data-science)
  - [Main Reference](#main-reference)

---

## Demo

A short walkthrough of the pipeline in action:

![Demo of the pipeline](demo/demo.gif)

---

## Background

The following diagram shows the landscape of traffic assignment models and positioning of the proposed day-to-day boundedly rational MARL DTA model. [This diagram](<thesis_document/media/4.LiteratureReview/MapTrafficAssignment(2)(1).drawio.pdf>).

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

## Workflow

The program is split into two parts.

**1. Simulation and Tracking.** Experiments are defined as YAML configuration files under `experiments/`. `run_batch.py` runs the simulations for a given experiment; once finished, all the resulting output data and metrics are saved and tracked by MLflow. The MLflow UI (`localhost:5000`) is where the runs that were performed can be inspected — this is also where runs are marked as **active**, meaning they're considered ready to be analyzed. `run_analysis.py` then pulls the data for the active runs and prepares it for the second part.

**2. Data Science.** This part is not containerized — it consists of R scripts, mostly automated, that take the data prepared by `run_analysis.py` and produce the plots for each research question.

See [Getting Started (Simulation and Tracking)](#getting-started-simulation-and-tracking) and [Getting Started (Data Science)](#getting-started-data-science) below for how to actually run each part.

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

The third research question investigated the effect of memory. Lower memory levels increased route-flow variability. However, for the synthetic network and demand configuration considered, all tested memory levels still converged to DUE. These results may differ in more complex network and demand configurations with more frequent changes in the cost ranking of routes across episodes, where memory and learning rate may have a stronger influence on the learning dynamics and convergence towards DUE.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ2/plot1_rgap_evolution_mem_seed.png" width="48%" alt="R-gap evolution across episodes for different memory levels">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ2/plot3_route_flow_stability.png" width="48%" alt="Route-flow stability by memory level">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ2/plot1_agent_learning_mem0_1.png" width="48%" alt="Agent learning process at memory level 0.1">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ2/plot1_agent_learning_mem1.png" width="48%" alt="Agent learning process at memory level 1">
</p>

### Disruption Recovery

The influence of memory became more apparent when considering a temporary disruption: lower memory enabled faster adaptation to the disruption and partial recovery after the network was restored, whereas perfect memory resulted in slower adaptation and persistent avoidance of the previously disrupted routes.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/disrupted_network.png" width="32%" alt="Disrupted network segment">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/plot1_rgap_evolution.png" width="32%" alt="R-gap evolution around the disruption">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/plot2_flow_disrupted_edges_evolution.png" width="32%" alt="Flow evolution on disrupted edges">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ4/plot3_flow_share_evolution_paths.png" width="48%" alt="Route-flow share evolution across paths">
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
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ11/plot3_qualitative_route_flow_evolution.png" width="48%" alt="Qualitative route-flow evolution under risk sensitivity">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ11/relevant_routes.png" width="48%" alt="Relevant routes for the risk-aversion scenario">
</p>

### Waiting-Time Aversion

The seventh research question investigated the effect of waiting-time sensitive behavior. The results indicate that the tested homogeneous populations, in which all drivers shared the same waiting-time sensitivity parameter, generally failed to converge towards DUE.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ12/plot1_waitingTime_sensitivity_mechanism.png" width="48%" alt="Waiting-time sensitivity mechanism">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ12/plot2_convergence_plot.png" width="48%" alt="Convergence under waiting-time sensitivity">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ12/plot3_qualitative_route_flow_evolution.png" width="48%" alt="Qualitative route-flow evolution under waiting-time sensitivity">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ12/relevant_routes.png" width="48%" alt="Relevant routes for the waiting-time-aversion scenario">
</p>

### Nonlinear Response

Finally, the eighth research question investigated the nonlinear reinforcement mechanism and its interaction with memory. The results showed that high values of τ (the dead-zone parameter) can prevent convergence towards DUE, particularly when combined with higher memory levels.

<p>
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ13/plot1_nonlinear_mechanism.png" width="48%" alt="Nonlinear stimulus mechanism">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ13/plot2_rgap_evolution.png" width="48%" alt="R-gap evolution under the nonlinear mechanism">
<img src="thesis_document/media/5.ExperimentalDesign_Evaluation/3.ExperimentalEvaluation/RQ13/plot3_qualitative_route_flow_evolution.png" width="48%" alt="Qualitative route-flow evolution under the nonlinear mechanism">
</p>

### Summary

Overall, the results suggest that the proposed model converges to DUE under its more rational formulation, while variations in the existing behavioral parameters, namely memory level and learning rate, do not necessarily prevent convergence under the tested scenario. However, their influence may become stronger in more complex network-demand configurations with more frequent changes in the cost ranking of routes across episodes. Previous research has shown that lower memory levels can prevent convergence to UE in a STA setting where changes in route-cost ranking occur more frequently (Wei et al., 2014).

The introduction of additional behavioral mechanisms, such as waiting-time sensitivity, risk aversion, and nonlinear response, can prevent convergence towards DUE. These results suggest that incorporating more realistic behavioral mechanisms into the agents' decision-making can prevent the network from reaching DUE, as reflected by higher R-gap values, although the effect depends on the behavioral parameters and the network-demand configuration.

---

## Getting Started (Simulation and Tracking)

The environment needed for simulation and tracking (Python, SUMO, MLflow) has been containerized using Docker. Hence, to run the program it is only needed to have Docker installed, solving the Matrix From Hell problem.

Docker can be used in two broad ways: a **dev-oriented** setup, where the image only provides the environment (Python, SUMO, dependencies) and the actual source code is bind-mounted in from the host, so it stays fully editable — or a **production-oriented** setup, where the code is baked into the image at build time and the program is effectively closed, exposing only a fixed set of configuration options. This project deliberately uses the dev-oriented approach: no source code is baked in, the repo is bind-mounted, and the container's only job is to solve the dependency-hell problem — since the actual audience (thesis reviewers, potential future students continuing this research) is expected to want to read and modify the code, not treat it as a black box.

**Prerequisites:** Docker

### Setup

> [!TIP]
> 🎥 Prefer video? Follow along with **[How to Set Up the Application Using Docker](https://youtu.be/LwC15-2MZUQ)**.

First steps to prepare Docker setup:

```sh
# 0. Prerequisite: Docker must be installed — https://docs.docker.com/engine/install/

# 1. Add your user to the docker group
sudo usermod -aG docker $USER

# 2. Log out and back in (or restart) for the group change to take effect
```

Copy the whole block below and paste it into your terminal — it clones the repo, pulls the pre-built image (skips compiling SUMO from source, which takes ~20 minutes), and prepares everything needed to bring the containers up:

```sh
# 3. Move to your home directory
cd ~

# 4. Create a folder for the project (whatever name you prefer)
mkdir thesis_migueldonado_project

# 5. Move into the created folder
cd thesis_migueldonado_project

# 6. Clone the repository into current folder
git clone --depth 1 https://github.com/MiguelDonado/TFM_TraSIrr.git .

# 7. Pull image from docker hub
docker pull migueldonado/thesis-app:latest

# 8. Tag the pulled image so docker-compose.yml can find it
docker tag migueldonado/thesis-app:latest thesis-app:latest

# 9. Generate a .env file so containers run as you, not as root
echo "UID=$(id -u)" > .env
echo "GID=$(id -g)" >> .env

# 10. Bring the containers up
docker compose up -d
```

### Running it (without GUI support)

Since the code is bind-mounted (not baked into the image), you can make any changes in the source code and YAML configs and it will take effect immediately — no rebuild needed.

```sh
# 1. Bring up the compose project (start the app + mlflow containers)
docker compose up -d

##########################
# SCRIPTS THAT CAN BE RUN
##########################
# a) Run simulations experiments in batch
docker compose exec app python scripts/run_batch.py RQ1 RQ2 RQ3 [--dev] 

# b) Manage "status" of runs in mlflow
docker compose exec app python scripts/manage_runs.py <research_question> --archive --apply     actually archive
docker compose exec app python scripts/manage_runs.py <research_question> --restore --apply     actually restore (remove status tag)

# c) Prepare data to be used in the research questions R analysis scripts
docker compose exec app python scripts/run_analysis.py <research_question>  

# 2. Stop when done
docker compose down                                         
```
### Check experiments in MLflow UI: 

Once the compose project is up, after running `docker compose up -d`, you can access the MLflow UI at: [http://localhost:5000](http://localhost:5000)

Each script above has a full usage guide in its own module docstring — open the file directly (top of the file, before any code) for all available flags and options:
- `scripts/run_batch.py` — running simulation batches, `--dev`/`--shutdown` flags, dev vs. production designs
- `scripts/run_analysis.py` — the active-run lifecycle and what gets prepared for R
- `scripts/manage_runs.py` — bulk archive/restore usage
- `scripts/start_mlflow.py` — running the MLflow UI outside Docker

---

## Getting Started (Data Science)

The data science part, in which the analysis of the simulation outputs is performed, is done in R. This part has not been containerized — it needs R and RStudio installed locally, and the exact package versions pinned in `renv.lock` restored.

**Prerequisites:** R + RStudio

1. Install R: [cran.r-project.org](https://cran.r-project.org/)
2. Install RStudio: [posit.co/download/rstudio-desktop](https://posit.co/download/rstudio-desktop/)
3. Clone the repo (skip if you already did this for the Docker setup above).
4. Open `Thesis.Rproj` in RStudio — this triggers `.Rprofile`, which automatically activates `renv` for the project (bootstrapping `renv` itself if it isn't already installed).
5. In the R console, install the required R packages:
```r
renv::restore()
```
6. Run the R scripts related to each research question

---

## Main Reference

Wei, F., Ma, S., & Jia, N. (2014). A Day-to-Day Route Choice Model Based on
Reinforcement Learning. *Mathematical Problems in Engineering*, 2014, 646548.
https://doi.org/10.1155/2014/646548