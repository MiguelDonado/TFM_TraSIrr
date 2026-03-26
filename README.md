# Thesis Project: Reinforcement Learning for Urban Traffic Optimization

## Overview

This project explores the application of Reinforcement Learning (RL) to urban traffic optimization using simulation tools. The main objective is to investigate how learning-based approaches can improve route decisions and contribute to more efficient and sustainable transportation systems.

---

## Project Evolution

### ✅ Replication Phase (Completed)

The initial stage of the project focused on replicating the experiment presented in:

> *"Realtime Vehicle Route Optimisation via DQN for Sustainable and Resilient Urban Transportation Network"*  
> *Song Sang Koh*

This phase has been successfully completed. Through this process, I achieved:

- Familiarity with **SUMO (Simulation of Urban MObility)**
- Understanding of **Deep Q-Networks (DQN)** in traffic routing
- Experience with **TraCI** for real-time simulation interaction

🚧 Remaining tasks for this phase:

- Verify that the agent is effectively learning
- Generate and analyze output plots
- Document results for inclusion in the thesis

---

## Current Stage: Day-to-Day Learning Approach

The project has now transitioned to a **day-to-day learning framework**, shifting from local, real-time decisions to global route-level optimization.

### Key Concept

Instead of making decisions at each junction, the agent:

- Selects a **complete route (origin → destination)**
- Learns from **aggregate outcomes across simulation episodes (days)**

This approach better reflects realistic traveler behavior and enables a more strategic learning process.

---

## Current Implementation Status

### ✅ Core Components Implemented

- `Scenario` class  
  Defines the traffic network, generate agents and routes (internally in Python), and simulation setup

- `Environment` class  
  Handles interaction with SUMO simulations to insert agents and manage episode execution

- `main.py`  
  Orchestrates the simulation and learning workflow

### 🔄 Interaction with SUMO

- **TraCI is no longer required**
- The system now relies on:
  - Running full simulations in SUMO
  - Extracting results from **tripinfo output files**
  - Updating the agent **after each episode**

This simplifies the architecture and aligns with the day-to-day learning paradigm.

---

## Reinforcement Learning Design

### Action Space

- Selection of **complete routes** between origin and destination

### Reward Function

- Currently based on **travel time**
- May be extended in the future to include irrationalities...

### State Space

- **Not yet defined**
- Will likely include:
  - Aggregated traffic conditions
  - Historical performance metrics

---

## Agent Development (In Progress)

The **Agent class** is the next major component to be implemented.

### Theoretical Foundation

The design is inspired by:

> *A Day-to-Day Route Choice Model Based on Reinforcement Learning*  
> Fangfang Wei, Shoufeng Ma, Ning Jia  
> DOI: 10.1155/2014/646548

Key characteristics:

- Based on the **Bush–Mosteller (BM) reinforcement learning model**

---

## Future Work

- Define and implement the **state representation**
- Complete the **Agent class**
- Handle more complex cases throughout the project (more than one OD pair, validation k routes computed for OD-pairs...)
- Evaluate learning performance and convergence behavior
- Extend reward structure

---

## Status

🚧 Work in progress:

- Replication phase completed (validation pending)
- Day-to-day learning framework implemented
- Agent development in progress