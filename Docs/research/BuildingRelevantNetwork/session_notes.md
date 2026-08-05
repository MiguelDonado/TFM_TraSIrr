# Session notes — BM algorithm audit + low-memory convergence puzzle (2026-08-05)

Thesis repo `/home/miguel/6.Projects/Thesis`. User is verifying their `BMAgent`
implementation (`src/agents/agent.py`) against Wei, Ma & Jia (2014) "A
Day-to-Day Route Choice Model Based on Reinforcement Learning" (Bush-Mosteller
RL for route choice), then investigating a surprising empirical result: very
low memory (γ) still lets the algorithm reach DUE, contradicting their naive
expectation from the paper.

## 1. Paper vs implementation — verified correct

Went through `src/agents/agent.py` line by line against eqs. 2, 4, 5, 6, 9:

- **ET** (`_compute_expected_travel_time`, eq. 5) and **PT**
  (`_compute_perceived_travel_times`, eq. 6) weighting/index math both check
  out exactly (verified by hand-deriving the weight exponents).
- **Stimulus** (`_compute_stimulus`, eq. 4): normalizes by max/min deviation
  over *all* routes including the chosen one — matches the paper's BM
  lineage (their eq. 1 sup is over all actions), not the more literal
  "other path" phrasing in the prose.
- **Probability update, S≥0** (`_reinforce_chosen`, eq. 2/9): matches
  term-for-term.
- **Probability update, S<0** (`_penalise_chosen`, eq. 2/9): the `scale`
  factor is algebraically equivalent to the paper's
  `1 − p_c·l·S/(1−p_c)` — verified by hand, and confirmed probabilities
  sum to exactly 1. Code comment says "corrected version Eq. 9", implying
  this was already caught/fixed in an earlier pass.
- Deviations from the paper (epsilon padding, warm-up gate requiring all
  routes visited, RQ6 nonlinear stimulus threshold) are all intentional,
  documented engineering additions — not bugs.

**Verdict given to user: implementation is faithful to the paper.**

## 2. PT/ET memory-decay mechanics — structural property, not a bug

Worked through with the user, step by step:

- A route visited **only once** has its PT decay factor cancel out of
  numerator/denominator exactly — PT equals that one observation, forever,
  regardless of γ or how long ago. Verified in code too
  (`_compute_perceived_travel_times`).
- With ≥2 visits, γ *is* a real relative-recency weight between those
  visits — but critically, **the current day `t` cancels out of the PT
  formula entirely** (shown algebraically: factor out `γ^(t−jₙ)` from
  every term). PT only depends on gaps *between visits to that route*, not
  on how long ago the last visit was relative to today. Same cancellation
  happens in ET, just less visible since ET pools every day's experience
  regardless of route.
- Conclusion user arrived at with my confirmation: γ is a **relative
  recency weight among an action's own observation history**, not a
  **staleness/freshness decay tied to the current day**. This is inherent
  to eq. 6, present in both paper and code — not an implementation quirk.

## 3. Debug trace investigation — why low memory still "worked"

User pointed me at `data/agent_state/agent_debug_trace.json` (single-agent
per-episode snapshot, gated by `DEBUG_AGENT_ID = "agent_1000"` in
`src/utils/run_training_BM.py`, dumps history/p/ET/PT/stimulus every
episode). Traced two separate runs from it (both via
`experiments/developer_modes/production.yaml`, Sioux Falls network, 2000
agents, seed 1999):

- **Run 1** (`learning_rate=0.3, memory_level=0.001`): showed PT_chosen ≈
  today's tt and ET(t) ≈ tt(t−1) almost exactly every episode — with γ this
  small, the BM update degenerates into a myopic "was today better than
  yesterday" comparison. Still converged agent_1000 onto route 0
  (p→0.80+) because route 0 is a clear, persistent winner (tt≈112–120 vs
  130–220+ for alternatives) — a dominant-route OD pair will converge under
  *any* γ, since even a 1-step lookback usually has the correct sign.

- **Run 2** (`learning_rate=0.9, memory_level=0.001`, the user's own
  follow-up attempt at breaking convergence): agent_1000's own `p` vector
  *does* flip completely between route 0 and route 5 multiple times across
  100 episodes (>99% → >99% the other way, repeatedly). Pulled population-
  level data too (`data/agent_state/actions.parquet` +
  `data/environment/agents_od_all.parquet`, 179 agents share agent_1000's
  OD `E21_22_NB→E1_2_EB`): route shares among the tier {0,4,5,6,7} (all
  ~112–135s) don't visibly narrow between the mid-run (ep 40–70) and
  late-run (ep 70–100) windows — looked at first like genuine
  non-convergence.

- **Correction via R-gap** (user's teacher's point — R-gap is the
  authoritative DUE metric, not mean travel time or policy variance):
  pulled `data/DUE/BM/R-gap/rgap.parquet` and `rgap_by_od.parquet` for the
  same run. Both network-wide and OD-specific R-gap **do** converge into a
  tight band (~±1–2.5%) by episode 70–100, and the OD-specific std
  actually *shrinks* late-run (1.57→1.11). **This means the individual/
  population flip-flopping among routes {0,4,5,6,7} is not a DUE
  violation at all** — Wardrop equilibrium only requires used routes have
  equal minimal cost; it doesn't pin down a unique split among tied-cost
  routes. My earlier "check policy/flow-share stability" framing was a
  false positive — walked this back explicitly to the user.

## 4. Where the user is stuck (open thesis question, unresolved at session end)

Core finding: on the Sioux Falls network at 2000 agents, DUE (via R-gap) is
reached even at γ=0.001 paired with β=0.9 — the network has enough slack/
route redundancy that almost any reasonable flow split is near-optimal, so
low memory doesn't visibly break convergence the way the paper's toy
networks show. Two framings on the table, neither resolved:

1. **Route-cost structure dichotomy** (mine, still holds even under
   R-gap): a dominant route → trivial convergence regardless of γ; several
   genuinely cost-tied routes → also easy convergence (any split is
   near-optimal), *and* this case is not a false positive under R-gap
   either — it's genuinely easy. What's needed to see γ matter is a
   network where the **correct equilibrium split is narrow/load-sensitive**
   (routes whose cost ranking actually crosses over as flow shifts), not
   just "many okay options."
2. Suggested next steps, not yet tried: (a) push demand much higher
   relative to route capacity to remove slack, (b) target/construct OD
   pairs with fewer, more asymmetric-capacity route alternatives (closer to
   the paper's own 3-link Fig. 2 test network) so equilibrium requires
   precise flow allocation rather than "anything in this tier works."

**User's own framing of the open problem** (their words, worth preserving
verbatim-ish for continuity): the thesis's main question is whether DUE is
reachable via this RL algorithm at all; they confirmed it's reachable at
γ=1; the surprise is it also seems reachable at very low γ, "at least in
our environment" — and they note the paper's own flow variability (which
they'd point to as evidence of non-convergence under low ψ) is *also*
present in their own results, muddying the comparison. This is unresolved
— next session should pick up here, likely by trying one of the two
next-step network/demand changes above and rechecking R-gap trajectories
across a small β×γ grid.

## Data/tooling notes for continuity

- `data/agent_state/agent_debug_trace.json` — single-agent trace, only
  useful for the currently-hardcoded `DEBUG_AGENT_ID`. Overwritten each
  training run.
- `data/agent_state/actions.parquet` — per-episode, per-agent chosen route
  index, all agents. Good for population-level route-share analysis.
- `data/environment/agents_od_all.parquet` — agent_id → origin/destination/
  departure_time/post_warm_up mapping, needed to filter actions.parquet to
  a specific OD pair's population.
- `data/DUE/BM/R-gap/{rgap,rgap_by_od,refined_rgap,refined_rgap_by_od}.parquet`
  — the R-gap pipeline outputs (see also prior memory
  `rgap_pipeline_time_interval_bugs.md`). This is the metric to use going
  forward per the user's advisor — not mean travel time, not policy
  variance.
- MLflow run params (via `mlflow_db/mlflow.db`, `runs`/`params` tables) are
  the reliable way to recover exactly which config produced a given data
  file when in doubt — matched runs to files by bracketing file mtimes
  against `runs.start_time`.
