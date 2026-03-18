# Thesis Project: Reinforcement Learning for Urban Traffic Optimization

## Overview

This project explores the application of Reinforcement Learning (RL) to urban traffic optimization using simulation tools. The primary goal is to investigate how learning-based approaches can improve route decisions and contribute to more efficient and sustainable transportation systems.

## Current Stage

At the initial stage, the objective is to **replicate the experiment presented in the thesis**:

> *"Realtime Vehicle Route Optimisation via DQN for Sustainable and Resilient Urban Transportation Network"*  
> *Song Sang Koh*

The purpose of this replication is not to propose a novel contribution yet, but to:

- Gain familiarity with **SUMO (Simulation of Urban MObility)**
- Understand the interaction between **Reinforcement Learning and traffic simulators**
- Explore how **Deep Q-Networks (DQN)** are applied in a traffic routing context
- Learn how to use **TraCI** for real-time communication with SUMO

## Future Direction

After this initial replication phase, the project will shift towards a different modeling perspective.

### Key Idea: From Local to Global Decisions

The referenced work focuses on **real-time decision-making at each junction**, where vehicles dynamically choose their next move.

In contrast, this project will adopt a **"zoomed-out" approach**, where:

- Decisions are made at the **route level (origin → destination)**
- Learning occurs in a **day-to-day framework**, rather than step-by-step within a single simulation

### Implications for Reinforcement Learning Design

This shift will require redefining core RL components:

- **State Space**  
  Likely to represent aggregated traffic conditions or historical travel times rather than local intersection states

- **Action Space**  
  Selection of entire routes instead of next-edge decisions

- **Reward Function**  
  Based on overall trip performance (e.g., travel time, congestion, emissions), possibly evaluated after each episode (day)

### Interaction with SUMO

Given the day-to-day learning setting:

- Real-time interaction via **TraCI may not be necessary**
- Instead, the workflow may rely on:
  - Running full simulations
  - Extracting results from **SUMO output files**
  - Updating the agent **after each simulation episode**

This simplifies the architecture and aligns better with the proposed learning paradigm.

## Technical Considerations

### RL Framework Modernization

The original implementation of the agent will need to be updated:

- Migrate to a **modern deep learning framework**, such as:
  - TensorFlow (using the **Keras API**)
  - or **PyTorch**

- Refactor the `Agent` class to:
  - Improve modularity
  - Support experimentation with different architectures
  - Enable easier training and evaluation

## Status

🚧 Work in progress:
- Replication phase ongoing
- SUMO + RL integration under development
- Future modeling approach under design