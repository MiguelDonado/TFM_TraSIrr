import numpy as np

from config.config import config


class BMAgent:
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
        self.PT = np.zeros(self.n_routes)

        # (scalar) Expected travel time
        self.ET = 0

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

    def compute_ET(self):
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

        self.ET = float(np.average(times, weights=weights))

    def compute_PT(self):
        T = len(self.history)

        # Arrays
        numerator = np.zeros(self.n_routes)
        denominator = np.zeros(self.n_routes)
        PT = np.zeros(self.n_routes, dtype=float)

        # Compute numerator and denominators formula PT
        for j, (r, tt) in enumerate(self.history, 1):
            weight = self.gamma ** (T - j)

            numerator[r] += weight * tt
            denominator[r] += weight

        # Compute PT all routes
        # Unused routes have PT = None
        for k in range(self.n_routes):
            if denominator[k] == 0:
                PT[k] = np.nan
            else:
                PT[k] = numerator[k] / denominator[k]

        self.PT = PT

    def compute_stimulus(self, chosen):
        A = self.ET
        M = self.PT

        # Heuristic
        # Set value of PT of unused routes to A (expected travel time)
        # This way they dont influence in stimulus computation
        M[np.isnan(M)] = A
        M_c = M[chosen]

        diff = A - M_c

        if diff >= 0:
            biggest_benefit = max(A - M) + config.epsilon
            stimulus = diff / biggest_benefit
            return stimulus
        else:
            biggest_loss = abs(min(A - M)) + config.epsilon
            stimulus = diff / biggest_loss
            return stimulus

    def update_probabilities(self, chosen, stimulus):
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

    def update_history(self, chosen, reward):
        info = (chosen, reward)
        self.history.append(info)

    def update(self, chosen, reward, warm_up, episode):
        self.update_history(chosen, reward)

        # Before learning starts, two conditions must be satisfied:
        # 1. A minimum number of episodes must have elapsed
        # 2. The agent must have visited all routes at least once
        # The following conditional checks it:
        if (
            episode > warm_up
            and len({route for route, _ in self.history}) == self.n_routes
        ):
            self.compute_ET()
            self.compute_PT()

            self.stimulus = self.compute_stimulus(chosen)

            self.update_probabilities(chosen, self.stimulus)
