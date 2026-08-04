"""
Bush-Mosteller reinforcement learning agent for day-to-day route choice.

Reference
---------
Wei, F., Ma, S., & Jia, N. (2014).
A Day-to-Day Route Choice Model Based on Reinforcement Learning.
Mathematical Problems in Engineering, 2014, 646548.
https://doi.org/10.1155/2014/646548

Notation
--------
β  (beta)   — learning rate: controls how fast the agent updates
               its route probabilities after each experience
γ  (gamma)  — memory level: exponential decay applied to past travel
               times (recent experiences matter more than older ones).
               Normally the same for every agent (config.memory_level);
               under RQ5 (config.heterogeneous_memory), agents.factory
               samples a different γ per agent from a Beta distribution
               before construction
ET          — Expected Travel Time: what the agent expects the trip to
               take, computed as a γ-weighted average over all past
               travel times across all routes
PT_r        — Perceived Travel Time for route r: γ-weighted average
               of past travel times on route r specifically
stimulus    — normalised signal in [-1, 1] measuring how much better
               or worse the chosen route was relative to ET.
                Under RQ6, the raw stimulus is passed through the threshold
                function before driving the update

Formulas
--------
ET  =  Σ_{j=1}^{T-1} γ^(T-1-j) · tt_j  /  Σ γ^(T-1-j)

         (excludes episode T — ET represents the expectation formed
          before departing, based only on past experience)

PT_r =  Σ_{j: route_j=r} γ^(T-j) · tt_j  /  Σ_{j: route_j=r} γ^(T-j)

         (includes episode T — PT is updated with today's observation
          before computing the stimulus)

stimulus = (ET - PT_chosen) / normalisation
           > 0  →  chosen route was cheaper than expected  →  reinforce
           < 0  →  chosen route was more expensive         →  penalise

Warm-up conditions (both must be satisfied before learning begins)
------------------------------------------------------------------
1. episode > warm_up  (minimum number of episodes elapsed)
2. all routes visited at least once
   (prevents division by zero in the stimulus normalisation when
    some PT values are undefined)

Note: this is unrelated to the agent's post_warm_up flag below, which is
about simulation time (departure_time vs config.warm_up_time), not episode
count — it marks whether the agent departs after the SUMO network's initial
traffic-loading window, and is used by the stopping rule to decide which
agents' policy changes count towards convergence.

Agent lifecycle
---------------
  __init__       uniform probability vector p, empty history
  select_action  sample route index from p
  update         append (route, tt) to history, then (if past warm-up)
                 recompute ET → PT → stimulus → update p (it must sum up to 1)
"""

import numpy as np


class BMAgent:
    """
    Bush-Mosteller reinforcement learning agent for route choice
    """

    def __init__(self, agent_id, routes, seed, beta, gamma, epsilon, departure_time, post_warm_up, nonlinear_stimulus, stimulus_tau):
        self.id = agent_id
        self.routes = routes
        self.n_routes = len(routes)
        self.beta = beta  # Learning rate
        self.gamma = gamma  # Memory decay
        self.epsilon = epsilon
        self.nonlinear_stimulus = nonlinear_stimulus
        self.stimulus_tau = stimulus_tau
        self.rng = np.random.default_rng(seed)
        self.departure_time = departure_time
        # Whether this agent departs after the SUMO network warm-up window
        # (see module docstring); used by the stopping rule to exclude
        # warm-up agents from the convergence signal.
        self.post_warm_up = post_warm_up

        # initial probabilities (uniform over routes, no preference in the beginning)
        self.p = np.ones(self.n_routes) / self.n_routes

        # Memory
        # List of tuples (route, reward). Ex: [(0, 12), (2,15)]
        self.history = []

        # (vector) Stores perceived costs of all routes at time t
        self.perceived_travel_times = np.zeros(self.n_routes)  # PT in BM paper notation

        # (scalar) Expected travel time
        self.expected_travel_time = 0  # ET in BM paper notation

        # (scalar) Stimulus
        self.stimulus = 0

    def select_action(self):
        """
        Action selection
        Example:
            self.n_routes = 2
            Then self.rng.choice returns 0 or 1, not 1 or 2.

            It means:
            “Select from the array [0, 1] with probabilities p = [0.5, 0.5]”
        """
        return self.rng.choice(self.n_routes, p=self.p)

    def _compute_expected_travel_time(self):
        """
        Does not take into account travel time on day t,
        because it represents the travel time we expected our trip to take
        during day t
        """
        # Old to new
        times = [tt for _, tt in self.history[:-1]]

        # New to old
        weights = [self.gamma**i for i in range(len(times))]
        # Reverse list
        # Old to new (to make them match with times)
        weights = weights[::-1]

        self.expected_travel_time = float(np.average(times, weights=weights))

    def _compute_perceived_travel_times(self):
        T = len(self.history)

        # Arrays
        numerator = np.zeros(self.n_routes)
        denominator = np.zeros(self.n_routes)

        # Compute numerator and denominators formula PT
        for j, (r, tt) in enumerate(self.history, 1):
            weight = self.gamma ** (T - j)

            numerator[r] += weight * tt
            denominator[r] += weight

        # Compute PT all routes
        self.perceived_travel_times = numerator / denominator

    def _compute_stimulus(self, chosen):
        """
        stimulus = (ET 3- PT_chosen) / normalisation, where normalisation is:
        diff >= 0:  max(ET - PT_r) over all routes  (biggest possible benefit)
        diff <  0:  |min(ET - PT_r)| over all routes (biggest possible loss)

        Normalising by the best/worst achievable deviation — not by ET itself —
        keeps stimulus in [-1, 1] and scales the signal relative to the full
        spread of route qualities on that episode.
        """

        expected_tt = self.expected_travel_time
        perceived_tt = self.perceived_travel_times

        chosen_perceived_tt = perceived_tt[chosen]

        diff = expected_tt - chosen_perceived_tt

        if diff >= 0:
            biggest_benefit = max(expected_tt - perceived_tt) + self.epsilon
            stimulus = diff / biggest_benefit
        else:
            biggest_loss = abs(min(expected_tt - perceived_tt)) + self.epsilon
            stimulus = diff / biggest_loss

        # Make sure stimulus is between [-1,1]
        tol = 1e-7
        if not (-1 - tol <= stimulus <= 1 + tol):
            raise ValueError("Stimulus must be between -1 and 1.")

        return stimulus

    def _apply_stimulus_threshold(self, stimulus):
        """
        RQ6 nonlinear reinforcement: hard-threshold (dead-zone) transform of
        the raw stimulus, applied before it drives the propensity update.

        f(S) = sign(S) · ( max(0, |S| - τ) / (1 - τ) )²

        |S| <= τ  →  f(S) = 0          small deviations are ignored entirely
        |S| = 1   →  f(S) = sign(S)    renormalised back to the full [-1, 1] range
        Quadratic ramp in between: suppresses reactions just above τ more than
        reactions near |S| = 1, i.e. weak sensitivity near threshold, strong
        sensitivity to severe deviations.
        """
        tau = self.stimulus_tau
        magnitude = max(0.0, abs(stimulus) - tau) / (1 - tau + self.epsilon)
        return float(np.sign(stimulus) * magnitude**2)

    def _update_probabilities(self, chosen, stimulus):
        # Copy so a failed validation below never leaves self.p corrupted
        p = self.p.copy()

        # Good route
        if stimulus >= 0:
            p = self._reinforce_chosen(p, chosen, stimulus)
        # Bad route
        else:
            p = self._penalise_chosen(p, chosen, stimulus)

        # If the sum is close to 1, renormalize to remove tiny numerical error.
        s = np.sum(p)
        
        if np.isclose(s, 1.0, atol=1e-3):
            p = p / s
        else:
            raise ValueError(f"Probabilities must sum to 1, got {s}")

        self.p = p

    def _reinforce_chosen(self, p, chosen, stimulus):
        """
        p_chosen ← p_chosen + (1 - p_chosen) · β · stimulus
        p_k      ← p_k     - p_k             · β · stimulus   for k ≠ chosen

        (1 - p_chosen) keeps p_chosen bounded below 1; the p_k factor keeps
        unchosen routes bounded above 0. Called only when stimulus >= 0.
        """
        # Update chosen route
        p[chosen] = p[chosen] + (1 - p[chosen]) * self.beta * stimulus
        # Adjust other routes
        for k in range(self.n_routes):
            if k != chosen:
                p[k] = p[k] - p[k] * self.beta * stimulus
        return p

    def _penalise_chosen(self, p, chosen, stimulus):
        """
        p_chosen ← p_chosen + p_chosen · β · stimulus                         (stimulus < 0)
        p_k      ← (p_k - p_k · p_chosen · β · stimulus) / (1 - p_chosen)    for k ≠ chosen

        p_chosen factor keeps p_chosen bounded above 0. Division by (1 - p_chosen)
        renormalises the remaining mass to preserve sum(p) = 1. Called only when stimulus < 0.
        """
        old_chosen = p[chosen]
    
        # chosen update (Eq. 2)
        p[chosen] = old_chosen + old_chosen * self.beta * stimulus

        # Scale remaining probabilities to preserve unity (corrected versio Eq. 9)
        scale = (1 - old_chosen - old_chosen * self.beta * stimulus) / (1 - old_chosen)

        for k in range(self.n_routes):
            if k != chosen:
                p[k] = p[k] * scale
        return p

    def _update_history(self, chosen, reward):
        info = (chosen, reward)
        self.history.append(info)

    def update(self, chosen, reward, warm_up, episode):
        self._update_history(chosen, reward)

        # Before learning starts, two conditions must be satisfied:
        # 1. A minimum number of episodes must have elapsed
        # 2. The agent must have visited all routes at least once
        # The following conditional checks it:
        if (
            episode > warm_up
            and len({route for route, _ in self.history}) == self.n_routes
        ):
            self._compute_expected_travel_time()
            self._compute_perceived_travel_times()

            self.stimulus = self._compute_stimulus(chosen)
             

            if self.nonlinear_stimulus:
                self.stimulus = self._apply_stimulus_threshold(self.stimulus)

            self._update_probabilities(chosen, self.stimulus)
