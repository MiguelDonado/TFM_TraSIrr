import sys

import numpy as np

from agent import Agent
from environment import Sumo
from scenario import scenario

MAP = "/home/miguel/6.Projects/ReplicateSongThesis/sumo_conf/thesisToyNetwork.net.xml"
DURATION = 1000  # 1000 seconds = 16.67 minutes
N_VEH = 20  # Number of vehicles to insert
ACCIDENTS = False
START_EDGE = "E0"  # For agent vehicle
END_EDGE = "E6"  # For agent vehicle
MEMORY_SIZE = 10000
BATCH_SIZE = 32
MIN_REPLAY_SIZE = BATCH_SIZE * 10


def main():

    # -----------------------------
    # 1. CREATE SCENARIO (files)
    # -----------------------------
    scen = scenario(
        map=MAP,
        duration=DURATION,
        n_veh=N_VEH,
        accidents=ACCIDENTS,
    )

    # -----------------------------
    # 2. CREATE ENVIRONMENT
    # -----------------------------
    env = Sumo(
        sumo_conf=scen.conf,
        gui=True,
        start_edge=START_EDGE,
        end_edge=END_EDGE,
        max_n_veh=N_VEH,
    )

    # -----------------------------
    # 3. CREATE AGENT
    # -----------------------------
    agent = Agent(
        n_features=env.n_features, n_actions=env.max_n_actions, memory_size=MEMORY_SIZE
    )

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------
    n_episodes = 100

    for episode in range(n_episodes):

        print(f"\n--- Episode {episode} ---")

        # Reset environment
        obs, display, n_actions, reward, done = env.reset()

        while True:

            # Get current edge and connections
            current_edge = env.traci.vehicle.getRoadID("nav_veh")
            conn_edges = env.e_conn_dict[current_edge]

            # -----------------------------
            # 1. CHOOSE ACTION
            # -----------------------------
            action, _ = agent.choose_action(
                obs, n_actions, current_edge, conn_edges, env.e_distance_dest_dict
            )

            # -----------------------------
            # 2. STEP ENVIRONMENT
            # -----------------------------
            obs_, display, n_actions_, reward, done = env.run_simulation(action)

            # -----------------------------
            # 3. STORE TRANSITION
            # -----------------------------
            agent.store_transition((obs, action, reward, obs_))

            # -----------------------------
            # 4. LEARN
            # -----------------------------
            if agent.memory.tree.memory_counter >= MIN_REPLAY_SIZE:
                agent.learn(episode, env)

            # -----------------------------
            # 5. Keep simulating until DONE or IN_ZONE (because previously we were at NEW, it will stop when DONE or IN_ZONE)
            obs_, display, n_actions, reward, done = env.run_simulation()
            # -----------------------------

            # -----------------------------
            # 6. TERMINATION
            # -----------------------------
            if done:
                print("Episode finished")
                break

        env.close()

    # -----------------------------
    # 5. SAVE MODEL
    # -----------------------------
    agent.save()


if __name__ == "__main__":
    main()
