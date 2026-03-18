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
        gui=False,
        start_edge=START_EDGE,
        end_edge=END_EDGE,
        max_n_veh=N_VEH,
    )

    # -----------------------------
    # 3. CREATE AGENT
    # -----------------------------
    agent = Agent(
        n_features=env.n_features,
        n_actions=env.max_n_actions,
    )

    # -----------------------------
    # 4. TRAINING LOOP
    # -----------------------------
    n_episodes = 100

    for episode in range(n_episodes):

        print(f"\n--- Episode {episode} ---")

        # Reset environment
        obs, display, n_actions, done, terminal = env.reset()

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
            obs_, display, n_actions_, done, terminal = env.run_simulation(action)

            # -----------------------------
            # 3. REWARD (IMPORTANT)
            # -----------------------------
            # You need to define this depending on reward_method
            reward = compute_reward(env)

            # -----------------------------
            # 4. STORE TRANSITION
            # -----------------------------
            agent.store_transition((obs, action, reward, obs_))

            # -----------------------------
            # 5. LEARN
            # -----------------------------
            if agent.learn_step_counter > agent.batch_size:
                agent.learn(episode, env)

            # Move to next state
            obs = obs_

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


# -----------------------------
# REWARD FUNCTION
# -----------------------------
def compute_reward(env):
    """
    You MUST define this based on your thesis

    Example (simple):
    negative travel time or congestion
    """

    # Placeholder (you should adapt)
    return -1


if __name__ == "__main__":
    main()
