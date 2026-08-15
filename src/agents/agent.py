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
σ_ET        — γ-weighted standard deviation of ALL past travel times
               (same population as ET, excludes today). Represents how
               variable the trip from A to B has been in general,
               regardless of route.
σ_r         — γ-weighted standard deviation of route r's travel times
               (same population/weights as PT_r, includes today).
               Reduces to 0 when a route has only 1 observation.
AC          — Aspiration Cost (RQ11/RQ12): ET risk-loaded by σ_ET and
               waiting-time-loaded by AWT. Equals ET exactly when
               reliability_sensitivity = waiting_time_sensitivity = 0.
PC_r        — Perceived Cost of route r (RQ11/RQ12): PT_r risk-loaded by
               σ_r and waiting-time-loaded by WT_r. Equals PT_r exactly
               when reliability_sensitivity = waiting_time_sensitivity = 0.
WT_r        — γ-weighted average of route r's waitingTime (SUMO's
               per-trip seconds spent stopped/crawling below 0.1 m/s),
               same population/weights as PT_r (includes today).
AWT         — γ-weighted average of ALL past waitingTime, all routes
               (same weights as ET, excludes today).
stimulus    — normalised signal in [-1, 1] measuring how much better
               or worse the chosen route was relative to AC.

Formulas
--------
ET  =  Σ_{j=1}^{T-1} γ^(T-1-j) · tt_j  /  Σ γ^(T-1-j)

         (excludes episode T — ET represents the expectation formed
          before departing, based only on past experience)

PT_r =  Σ_{j: route_j=r} γ^(T-j) · tt_j  /  Σ_{j: route_j=r} γ^(T-j)

         (includes episode T — PT is updated with today's observation
          before computing the stimulus)

RQ11 reliability sensitivity (reliability_sensitivity, θ ≥ 0, per agent)
--------------------------------------------------------------------------
σ_ET² = Σ_{j=1}^{T-1} γ^(T-1-j) · (tt_j - ET)²  /  Σ γ^(T-1-j)
σ_r²  = Σ_{j: route_j=r} γ^(T-j) · (tt_j - PT_r)²  /  Σ_{j: route_j=r} γ^(T-j)

AC    = ET   + θ · σ_ET
PC_r  = PT_r + θ · σ_r

θ must load both AC and PC_r (not just PC_r). Loading both keeps the
comparison symmetric:
A route only looks risky relative to what the agent is used to overall.
θ=0 recovers the original ET/PT_r model exactly (PC_r=PT_r, AC=ET).

RQ12 waiting-time sensitivity (waiting_time_sensitivity, φ ≥ 0, per agent)
--------------------------------------------------------------------------
WT_r = Σ_{j: route_j=r} γ^(T-j) · wt_j  /  Σ_{j: route_j=r} γ^(T-j)
AWT  = Σ_{j=1}^{T-1} γ^(T-1-j) · wt_j  /  Σ γ^(T-1-j)

AC    = ET   + θ · σ_ET + φ · AWT
PC_r  = PT_r + θ · σ_r  + φ · WT_r

Same reasoning as θ: φ must load both AC and PC_r symmetrically.
φ is dimensionless — "extra perceived seconds of
cost per second the driver expects to spend waiting" on top of what
waiting already contributes to PT_r/ET (waitingTime is part of duration).
φ=0 recovers the θ-only model exactly 

stimulus = (AC - PC_chosen) / normalisation
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
  update         append (route, tt, wt) to history, then (if past warm-up)
                 recompute ET → PT → stimulus → update p
"""

import numpy as np


class BMAgent:
    """
    Bush-Mosteller reinforcement learning agent for route choice
    """

    def __init__(self, agent_id, routes, seed, beta, gamma, epsilon, departure_time, post_warm_up, reliability_sensitivity, waiting_time_sensitivity):
        self.id = agent_id
        self.routes = routes
        self.n_routes = len(routes)
        self.beta = beta  # Learning rate
        self.gamma = gamma  # Memory decay
        self.epsilon = epsilon
        self.reliability_sensitivity = reliability_sensitivity  # theta (RQ11)
        self.waiting_time_sensitivity = waiting_time_sensitivity  # phi (RQ12)
        self.rng = np.random.default_rng(seed)
        self.departure_time = departure_time
        # Whether this agent departs after the SUMO network warm-up window
        # (see module docstring); used by the stopping rule to exclude
        # warm-up agents from the convergence signal.
        self.post_warm_up = post_warm_up

        # initial probabilities (uniform over routes, no preference in the beginning)
        self.p = np.ones(self.n_routes) / self.n_routes

        # Memory
        # List of tuples (route, reward, waiting_time). Ex: [(0, 12, 3), (2, 15, 0)]
        self.history = []

        # (vector) Stores perceived travel times of all routes at time t
        self.perceived_travel_times = np.zeros(self.n_routes)  # PT in BM paper notation

        # (scalar) Expected travel time
        self.expected_travel_time = 0  # ET in BM paper notation

        # RQ11: reliability-sensitive perceived cost / aspiration
        self.route_travel_time_std = np.zeros(self.n_routes)  # sigma_r
        self.travel_time_std = 0.0  # sigma_ET

        # RQ12: waiting-time-sensitive perceived cost / aspiration
        self.perceived_waiting_times = np.zeros(self.n_routes)  # WT_r
        self.expected_waiting_time = 0.0  # AWT

        self.perceived_costs = np.zeros(self.n_routes)  # PC_r
        self.aspiration_cost = 0.0  # AC

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
        times = [tt for _, tt, _ in self.history[:-1]]

        # New to old
        weights = [self.gamma**i for i in range(len(times))]
        # Reverse list
        # Old to new (to make them match with times)
        weights = weights[::-1]

        self.expected_travel_time = float(np.average(times, weights=weights))

    def _compute_expected_waiting_time(self):
        """
        AWT: gamma-weighted average of all past waitingTime (same
        population/weights as ET, excludes today). Structural copy of
        _compute_expected_travel_time, averaging waiting_time instead of tt.
        """
        times = [wt for _, _, wt in self.history[:-1]]

        weights = [self.gamma**i for i in range(len(times))]
        weights = weights[::-1]

        self.expected_waiting_time = float(np.average(times, weights=weights))

    def _compute_travel_time_std(self):
        """
        sigma_ET: gamma-weighted standard deviation of all past travel
        times (same population/weights as ET, excludes today). Deviations
        are measured against self.expected_travel_time, which must already
        be computed (data dependency: the mean has to exist before spread
        around it can be measured).
        """
        times = [tt for _, tt, _ in self.history[:-1]]

        weights = [self.gamma**i for i in range(len(times))]
        weights = weights[::-1]

        mean = self.expected_travel_time
        variance = np.average([(tt - mean) ** 2 for tt in times], weights=weights)

        self.travel_time_std = float(np.sqrt(variance))

    def _compute_perceived_travel_times(self):
        # Arrays
        numerator = np.zeros(self.n_routes)
        denominator = np.zeros(self.n_routes)

        # Index (1-based) of each route's most recent occurrence. Weights are
        # anchored per-route to this instead of to T: with a low gamma
        # (e.g. memory_level=0.01), a route not chosen in ~150+ episodes has
        # gamma**(T-j) underflow to 0.0 for every one of its entries when
        # anchored to T, turning numerator/denominator into 0/0 = NaN.
        # Anchoring to the route's own last visit keeps its top weight at
        # gamma**0 = 1, so denominator is never zero. Numerator and
        # denominator are both scaled by the same constant relative to the
        # T-anchored formula, so the resulting ratio is unchanged.
        last_seen = {}
        for j, (r, _, _) in enumerate(self.history, 1):
            last_seen[r] = j

        # Compute numerator and denominators formula PT
        for j, (r, tt, _) in enumerate(self.history, 1):
            weight = self.gamma ** (last_seen[r] - j)

            numerator[r] += weight * tt
            denominator[r] += weight

        # Compute PT all routes
        self.perceived_travel_times = numerator / denominator

    def _compute_perceived_waiting_times(self):
        """
        WT_r: gamma-weighted average of route r's waitingTime (same
        population/weights as PT_r, includes today). Structural copy of
        _compute_perceived_travel_times, accumulating waiting_time instead
        of tt.
        """
        numerator = np.zeros(self.n_routes)
        denominator = np.zeros(self.n_routes)

        last_seen = {}
        for j, (r, _, _) in enumerate(self.history, 1):
            last_seen[r] = j

        for j, (r, _, wt) in enumerate(self.history, 1):
            weight = self.gamma ** (last_seen[r] - j)

            numerator[r] += weight * wt
            denominator[r] += weight

        self.perceived_waiting_times = numerator / denominator

    def _compute_route_travel_time_std(self):
        """
        sigma_r: gamma-weighted standard deviation of route r's travel
        times (same population/weights as PT_r, includes today). Deviations
        are measured against self.perceived_travel_times, which must
        already be computed. Reduces to 0 when a route has only 1
        observation.
        """
        last_seen = {}
        for j, (r, _, _) in enumerate(self.history, 1):
            last_seen[r] = j

        numerator = np.zeros(self.n_routes)
        denominator = np.zeros(self.n_routes)

        for j, (r, tt, _) in enumerate(self.history, 1):
            weight = self.gamma ** (last_seen[r] - j)
            numerator[r] += weight * (tt - self.perceived_travel_times[r]) ** 2
            denominator[r] += weight

        self.route_travel_time_std = np.sqrt(numerator / denominator)

    def _compute_perceived_costs(self):
        """
        PC_r = PT_r + theta*sigma_r + phi*WT_r  (risk/waiting-adjusted perceived route cost)
        AC   = ET   + theta*sigma_ET + phi*AWT  (risk/waiting-adjusted aspiration)

        theta = reliability_sensitivity = 0 and phi = waiting_time_sensitivity = 0
        recovers PC_r = PT_r, AC = ET exactly.
        """
        self.perceived_costs = (
            self.perceived_travel_times
            + self.reliability_sensitivity * self.route_travel_time_std
            + self.waiting_time_sensitivity * self.perceived_waiting_times
        )
        self.aspiration_cost = (
            self.expected_travel_time
            + self.reliability_sensitivity * self.travel_time_std
            + self.waiting_time_sensitivity * self.expected_waiting_time
        )

    def _compute_stimulus(self, chosen):
        """
        stimulus = (AC - PC_chosen) / normalisation, where normalisation is:
        diff >= 0:  max(AC - PC_r) over all routes  (biggest possible benefit)
        diff <  0:  |min(AC - PC_r)| over all routes (biggest possible loss)

        Normalising by the best/worst achievable deviation — not by AC itself —
        keeps stimulus in [-1, 1] and scales the signal relative to the full
        spread of route qualities on that episode.
        """

        aspiration_cost = self.aspiration_cost
        perceived_costs = self.perceived_costs

        chosen_perceived_cost = perceived_costs[chosen]

        diff = aspiration_cost - chosen_perceived_cost

        if diff >= 0:
            biggest_benefit = max(aspiration_cost - perceived_costs) + self.epsilon
            stimulus = diff / biggest_benefit
        else:
            biggest_loss = abs(min(aspiration_cost - perceived_costs)) + self.epsilon
            stimulus = diff / biggest_loss

        # Make sure stimulus is between [-1,1]
        tol = 1e-4
        if not (-1 - tol <= stimulus <= 1 + tol):
            raise ValueError("Stimulus must be between -1 and 1.")

        return stimulus

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

        if np.isclose(s, 1.0, atol=1e-3) or self.n_routes == 1:
            p = p / s
        else:
            raise ValueError(f"Probabilities must sum to 1, got {s}")

        # Normalize
        self.p = p 

    def _reinforce_chosen(self, p, chosen, stimulus):
        """
        p_chosen ← p_chosen + (1 - p_chosen) · β · stimulus
        p_k      ← p_k     - p_k             · β · stimulus   for k ≠ chosen

        (1 - p_chosen) keeps p_chosen bounded below 1; the p_k factor keeps
        unchosen routes bounded above 0. Called only when stimulus >= 0.
        """
        # Update chosen route
        p[chosen] += (1 - p[chosen]) * self.beta * stimulus
        # Adjust other routes
        for k in range(self.n_routes):
            if k != chosen:
                p[k] -= p[k] * self.beta * stimulus
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

        # Exceptional case in which old_chosen == 1
        if old_chosen == 1:
            diff = 1 - p[chosen]
            for k in range(self.n_routes):
                if k != chosen:
                    p[k] = diff / (self.n_routes - 1)
            return p

        # Scale remaining probabilities to preserve unity (orrected version Eq. 9)
        scale = (1 - old_chosen - old_chosen * self.beta * stimulus) / (1 - old_chosen)

        for k in range(self.n_routes):
            if k != chosen:
                # Excepcional case in which some route has 0 probbaility, so that it can be recovered
                if p[k] == 0:
                    p[k] = (p[k] + self.epsilon) * scale
                else:
                    p[k] = p[k] * scale
        return p

    def _update_history(self, chosen, reward, waiting_time):
        info = (chosen, reward, waiting_time)
        self.history.append(info)

    def snapshot(self):
        """
        Full internal state as JSON-serializable primitives (numpy arrays →
        lists, numpy scalars → float/int). Used for debug traces of a single
        agent across episodes — see run_training_BM.DEBUG_AGENT_ID — dumped
        as JSON so it can be browsed as a folding tree in VS Code, the same
        way the debugger's Locals/Watch panel shows nested variables.
        """
        return {
            "id": self.id,
            "history": [[int(route), float(tt), float(wt)] for route, tt, wt in self.history],
            "p": self.p.tolist(),
            "expected_travel_time": float(self.expected_travel_time),
            "perceived_travel_times": self.perceived_travel_times.tolist(),
            "travel_time_std": float(self.travel_time_std),
            "route_travel_time_std": self.route_travel_time_std.tolist(),
            "expected_waiting_time": float(self.expected_waiting_time),
            "perceived_waiting_times": self.perceived_waiting_times.tolist(),
            "aspiration_cost": float(self.aspiration_cost),
            "perceived_costs": self.perceived_costs.tolist(),
            "stimulus": float(self.stimulus),
            "chosen": int(self.history[-1][0]),
            "chosen_tt": int(self.history[-1][1])
        }

    def update(self, chosen, reward, waiting_time, warm_up, episode):
        self._update_history(chosen, reward, waiting_time)

        # Before learning starts, two conditions must be satisfied:
        # 1. A minimum number of episodes must have elapsed
        # 2. The agent must have visited all routes at least once
        # The following conditional checks it:
        if (
            episode > warm_up
            and len({route for route, _, _ in self.history}) == self.n_routes
        ):
            self._compute_expected_travel_time()
            self._compute_perceived_travel_times()
            self._compute_travel_time_std()
            self._compute_route_travel_time_std()
            self._compute_expected_waiting_time()
            self._compute_perceived_waiting_times()
            self._compute_perceived_costs()

            self.stimulus = self._compute_stimulus(chosen)

            self._update_probabilities(chosen, self.stimulus)
