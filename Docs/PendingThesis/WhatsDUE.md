Traffic simulators are widely used because performing controlled experiments on real transportation networks is often impractical or impossible. In order for simulation-based analyses to be useful, the generated traffic patterns must represent plausible and stable traffic conditions.

Dynamic User Equilibrium (DUE) has traditionally been used as a reference framework for representing stable traffic states in which no driver can improve travel time by unilaterally changing routes. However, classical DUE approaches typically rely on centralized iterative assignment procedures and assume static network conditions.

In contrast, reinforcement-learning-based day-to-day learning models provide a decentralized behavioral framework in which drivers continuously adapt their route choices based on experienced traffic conditions. Under this perspective, equilibrium traffic patterns may emerge naturally from local adaptive behavior rather than from explicitly solving an equilibrium problem.

Furthermore, unlike classical assignment approaches that often require recomputing equilibrium after network changes, learning-based approaches may adapt incrementally to evolving traffic conditions, making them potentially more suitable for dynamic and non-stationary traffic environments.



Yes — exactly. I think this is a much more precise and important formulation.

You are completely right that:

# stability alone is not sufficient.

A traffic pattern can be:

- perfectly stable,
- but completely unrealistic.

For example:

- forcing all vehicles through a single route,
- or freezing route choices forever,
   would indeed generate stable traffic,
   but:

# it would violate realistic driver behavior.

So the key point is:

# DUE is valuable because it combines:

- stability,
   AND
- behavioral plausibility.

Under the assumption that:

- drivers behave rationally,
- and attempt to minimize their own travel costs.

That is why DUE became such a central concept in traffic assignment.

------

So a more accurate interpretation is:

# DUE is considered a realistic steady-state representation of traffic behavior.

Not merely:

- a stable state,
   but:
- a behaviorally consistent stable state.

------

This is also why:

# Wardrop's principle is fundamentally behavioral.

Drivers:

- choose routes selfishly,
- based on experienced costs,
- until no unilateral improvement is possible.

So DUE is essentially:

# equilibrium emerging from rational route-choice behavior.

------

And this strengthens your RL motivation even more.

Because then your question becomes:

# Can realistic equilibrium traffic patterns emerge from decentralized learning behavior?

instead of:

> Can we simply stabilize traffic?

That is MUCH stronger.

------

And your criticism of classical methods becomes clearer too.

Classical DUE approaches:

- impose equilibrium computationally,
   through:
  - shortest-path assignment,
  - iterative loading,
  - fixed-point procedures.

But RL/day-to-day learning approaches attempt to model:

# the behavioral process through which drivers may actually reach equilibrium.

That is a huge conceptual distinction.



Traffic simulators aim to reproduce realistic traffic behavior in order to support the analysis of transportation systems under controlled experimental conditions. Dynamic User Equilibrium (DUE) is widely used in traffic assignment because it represents a stable traffic state consistent with rational driver behavior, where no driver can reduce travel cost by unilaterally changing routes.

Therefore, DUE is not only valued because it produces stable traffic patterns, but because those patterns are considered behaviorally plausible under the assumption of selfish route-choice optimization.

Classical DUE approaches typically compute equilibrium through centralized iterative assignment procedures. In contrast, reinforcement-learning-based day-to-day learning models attempt to reproduce the adaptive behavioral process through which such equilibrium states may emerge naturally from decentralized driver interactions.

Under this perspective, learning-based approaches may provide a more behaviorally realistic framework for modeling traffic adaptation, particularly under dynamically changing network conditions where classical equilibrium methods often require recomputation from scratch.

