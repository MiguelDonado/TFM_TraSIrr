import numpy as np

from config.config import config


class BMAgent:
    """
    Bush-Mosteller reinforcement learning agent for route choice
    """

    def __init__(
        self,
        agent_id,
        routes,
        seed,
        beta=config.learning_rate,
        gamma=config.memory_level,
    ):
        self.id = agent_id
        self.routes = routes
        self.n_routes = len(routes)
        self.beta = beta  # Learning rate
        self.gamma = gamma  # Memory decay
        self.rng = np.random.default_rng(seed)

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
        Does not take into account travel time on day t

        Example:
        for i in range(1):
            print(i)
        # 0   (it just prints 0, not 1)
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
        perceived_travel_times = np.zeros(self.n_routes, dtype=float)

        # Compute numerator and denominators formula PT
        for j, (r, tt) in enumerate(self.history, 1):
            weight = self.gamma ** (T - j)

            numerator[r] += weight * tt
            denominator[r] += weight

        # Compute PT all routes
        # Unused routes have PT = None
        for k in range(self.n_routes):
            if denominator[k] == 0:
                perceived_travel_times[k] = np.nan
            else:
                perceived_travel_times[k] = numerator[k] / denominator[k]

        self.perceived_travel_times = perceived_travel_times

    def _compute_stimulus(self, chosen):
        expected_tt = self.expected_travel_time
        perceived_tt = self.perceived_travel_times.copy()

        # Heuristic
        # Set value of PT of unused routes to A (expected travel time)
        # This way they dont influence in stimulus computation
        perceived_tt[np.isnan(perceived_tt)] = expected_tt
        chosen_perceived_tt = perceived_tt[chosen]

        diff = expected_tt - chosen_perceived_tt

        if diff >= 0:
            biggest_benefit = max(expected_tt - perceived_tt) + config.epsilon
            stimulus = diff / biggest_benefit
            return stimulus
        else:
            biggest_loss = abs(min(expected_tt - perceived_tt)) + config.epsilon
            stimulus = diff / biggest_loss
            return stimulus

    def _update_probabilities(self, chosen, stimulus):
        p = self.p.copy()

        # Good route
        if stimulus >= 0:
            # Update chosen route
            p[chosen] += (1 - p[chosen]) * self.beta * stimulus
            # Adjust other routes
            for k in range(self.n_routes):
                if k != chosen:
                    p[k] -= p[k] * self.beta * stimulus

        # Bad route
        else:
            # Update chosen route
            p[chosen] += p[chosen] * self.beta * stimulus
            # Adjust other routes
            for k in range(self.n_routes):
                if k != chosen:
                    p[k] = (p[k] - p[k] * p[chosen] * self.beta * stimulus) / (
                        1 - p[chosen]
                    )

        # Normalize
        self.p = p / np.sum(p)

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

            self._update_probabilities(chosen, self.stimulus)
