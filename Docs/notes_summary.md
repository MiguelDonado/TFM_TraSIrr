- Bush-Mosteller: Classical behavioral learning
- Thompson Sampling: Bayesian learning
- Q-learning or another RL method (modern RL)

| Level                    | Example                                       |
| ------------------------ | --------------------------------------------- |
| Problem                  | Multi-agent route choice                      |
| Mathematical formulation | Multi-agent bandit / repeated congestion game |
| Behavioral Learning      | Bush-Mosteller                                |
| Bayesian Learning        | Thompson Sampling                             |
| RL-style learning        | Stateless Q-learning                          |

The problem is a multi-agent route choice problem, which can be modeled as a repeated congestion game (game theoretic perspective), or from the perspective of each traveler, as a multi-agent bandit problem with non-stationary rewards, or from transportation perspective as a day-to-day learning problem.

To solve this problem different learning algorithms can be used:

| Learning paradigm                         | Example algorithm    | Main idea                                                    |
| ----------------------------------------- | -------------------- | ------------------------------------------------------------ |
| Behavioral learning (behavioral sciences) | Bush-Mosteller       | Reinforce routes that perform well                           |
| Bayesian Learning (statistics)            | Thompson Sampling    | Maintain uncertainty and learn route quality through posterior updates (beliefs over route quality) |
| RL-style learning (ML/RL)                 | Stateless Q-learning | Learn action values from experienced rewards                 |

They all try to answer the same question, which route should I choose tomorrow given what I have experienced so far.

The problem of Multi-Agent Thompson Sampling, is that in the classical Thompson Sampling we are assuming the travel time distribution of a route r is fixed (stationary), i.e., if it has a mean of 10 min today, it will do so tomorrow (the observations are different because of randomness). But in my thesis, the travel times of a route, depend on the route choices of other agents, therefore the distribution is non stationary and the parameter we are trying to learn is not fixed. Example: If 1000 travelers choose that route, then its mean may be 75. If 0 travelers choose that route its mean 5. So the reward distribution depend on how many travelers choose that route.

RL-based models and multi-agent: These methods (BM, Q-learning) never assumes stationarity. In BM case, the traveler only sees route A was good and it reinforces it. No probabilistic model of the environment is assumed. Thats one reason why this model became popular in transportation.

An approach that Manuel suggested as a workaround for the Thompson sampling, is that instead of giving equal weight to all past observations, the posterior updates discount old observations (dont take into account all the nonstationary trajectory when estimating the parameter using posteriors).

Problem definition (multi-agent day-to-day route choice)

-  The key thing of RL are state transitions (MDP). An action influences future states, and hence future actions. But on my problem the traveler action does not move the driver into a new state tomorrow. The timeline is: 1. Day t | 2. Choose a route (action) | 3. Observe travel time | 4. Go home (there is exactly one decision). This absence of within day state transitions allows to view the route choice problem as a Multi agent Bandit problem.

Stateless RL is esentially a Multi-Armed Bandit problem (at, rt): 1. Choose action. 2. Observe reward. 3. Repeat

In transportation research people often say reinforcement learning, behavioral learning for models where agents reinforce succesful actions (its kind of a broader term for them). They are not necessarily referring to MDP-based RL.

**Algorithms comparison (assumptions)**

- Bush-Mosteller and Q-learning almost none. BM does not require a stationarity assumption for its update rule, but that does not mean non-stationarity is not a problem for BM. Non-stationairyty can still affect performance, the difference is that BM remains a valid algorithm.

- Thompson Sampling: Explicit statistical model $TT_r \sim Gamma(\alpha, \beta)$ 

  - Bandit problems:  They assume the reward distribution of each route is fixed. This assumption does not refer to a particular algorithm like Thompson Sampling, UCB, epsilon-greedy. A bandit problem in general makes this assumption. In our case it changes because congestion changes, so Thomsom Sampling, UCB lose their theoretical assumptions. Thompson sampling assumes a fixed Gamma distribution, but UCB and epsilon-greedy assumes a fixed expected reward. Same with Q-learning.

  

**Thompson Sampling Workaround for dealing with Non-stationarity**

The bayesian model says something like: $TT_r \sim \text{Gamma}(\alpha, \beta_r)$ with $\beta_r$ fixed (then every observation is used to infer that fixed parameter).

The solution is Thompson Sampling with forgetting (sliding window). It does not really assume a fixed route quality. With the forgetting mechanism is no longer trying to estimate a permanent route quality. It is tracking the current one.

Contextual bandit is not a solution for my case, because it assumes: 1. Observe context, 2. Choose action, 3. Receive reward (the context is given by the environment). On my case I would have a contextual bandit if I let the users observe aggregate information before choosing. But on my problem the travelers dont see any info / context / state.

The forgetting/sliding idea is: Track current environment instead of trying to estimate a permanent route quality (give more weight to recent observations).

Why it makes sense: Imagine 1000 travelers: At the beginning everyone explores. then route flows change rapidly, then reward distributions vary a lot. After many days, flows start stabilizing, route travel times become less variable. If you use the entire history equally, then observations from Day 5 still influences decisions on Day 500. But day 5 belong to a complete different regime. Estimate current route quality, rather than estimate the true route quality. As learning progresses, route shares and travel times become more stable, and the environment may become approximately stationary.

The intuition is that instead of finding a distribution that is plausible/likely for all the observations, find a distribution that is likely for the last 20 observations.

In normal Thompson sampling, every observation from the past contributes equally forever. An observation from day 1 has exactly the same weight as an observation from day 1000. That makes sense if there is a fixed $\beta$ that you are trying to estimate.

In a multi-agent non stationary route choice environment, kearning rules that discount old information may produce more stable convergence than treating all past info equally.

## BM-model intuition and gotchas

#### Weaknesses

**Question 1:¿If i only visited one route once, 20 days ago, then i will still remember perfectly the cost of the route that day? **

*Answer* 

Yes — that's correct, and it follows directly from eq. 6 in the paper.

Example for a route with only one observation

PT for route k is a weighted average, not a decaying quantity:

$M_ik^t = Σ_j ψ^(t−j)·T_j·ξ_jk / Σ_j ψ^(t−j)·ξ_jk$

If route k was chosen exactly once, at day j₀, both sums collapse to a single term:

$M_ik^t = ψ^(t−j₀)·T_{j₀} / ψ^(t−j₀) = T_{j₀}$

The decay weight appears in both numerator and denominator and cancels exactly — regardless of how large t − j₀ is, or what γ is (as long as γ > 0). So a route visited once 20 days ago is remembered with the exact travel time from that day, undiminished, forever (until visited again).

***\*This isn't decay of a memory's "strength" — γ only controls the relative weighting between multiple observations of the same route.\**** With only one observation, there's nothing to weigh it against, so the average is just that one sample.

PT for route k depends only on the gaps between visits to that specific route, never on how far today is from the last visit. So:

\- The most recent visit (jₙ) always carries weight γ^0 = 1 — full weight, by construction, no matter whether jₙ was yesterday or 400 days ago.

\- Older visits to that route (j₁, j₂, ...) are discounted relative to jₙ, by γ^(jₙ−jᵢ) — that's the real decay you identified earlier.

\- But there's no term anywhere that discounts jₙ itself relative to "now." A route last driven 100 days ago, never revisited since, produces exactly the same PT today as it would have produced the day after that 100th-day visit.

**So the precise characterization: γ in this model is a relative-recency weight among an action's own observation history, not a staleness/freshness decay tied to the current day. Nothing in the paper's formulation makes a memory less trusted just because it's old in absolute terms — only because newer memories of the same route exist to outweigh it. An infrequently-explored route keeps an undiminished, fully-confident PT based on whatever its last visit happened to show, indefinitely. That's a genuine structural property of eq. 6 (not an implementation quirk — the code inherits it faithfully), and it's arguably a real limitation of the model if you wanted "confidence in a memory" to erode with elapsed time rather than just with newer competing samples.**



