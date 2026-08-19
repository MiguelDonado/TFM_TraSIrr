# Session notes — RQ13 nonlinear stimulus design (2026-08-18)

Thesis repo `/home/miguel/6.Projects/Thesis`. Follow-up to RQ11 (risk
aversion, θ) and RQ12 (waiting-time aversion, φ), both already implemented.
RQ13 replaces RQ6 (deleted in commit `4320244` when RQ11 landed) — RQ6
applied a hard-threshold nonlinearity to the *final* stimulus `S`, after
normalization; the plan since that commit has been to move the
nonlinearity earlier, onto each route's raw perceived-cost margin, before
normalization. This session worked out that design in full and wrote it
into `experiments/rq13/design.yaml`.

## 1. The motivating problem

Advisor's framing: humans don't react linearly to deviations from
expectation. Analogy: running 30 miles doesn't feel harder mile-to-mile
for a long stretch, then each extra mile past some point gets dramatically
harder — flat reaction, then steep. Applied to driving: a route 1 second
worse than expected goes unnoticed; a route 10 minutes worse triggers a
strong, aggressive drop in the probability of choosing it again. The
current linear model has no such dead zone — every deviation, however
tiny, drives a proportional update.

Concrete illustration of why this matters (`AC = 100`):
- Chosen route 1s better (`PC_chosen=99`), alternative 5s worse
  (`PC_other=105`) → `stimulus = 1/1 = 1` (max possible).
- Chosen route 80s better (`PC_chosen=20`), same alternative → `stimulus =
  80/80 = 1` — **identical** to the 1-second case.

A 1-second win and an 80-second win are indistinguishable under the
current model, because eq. 4's max/min normalization only measures "how
good relative to today's best/worst alternative," not absolute magnitude.
This is the concrete gap RQ13 targets.

## 2. Formula, finalized this session

```
x_r = (AC - PC_r) / AC                         (relative margin, dimensionless)
g_r = sign(x_r) * (max(0, |x_r| - tau) / (1 - tau + epsilon))^2   (RQ6's function, reused)

diff_chosen   = g_chosen
normalization = max(g_r) + epsilon   if diff_chosen >= 0   (biggest benefit)
              = |min(g_r)| + epsilon if diff_chosen <  0   (biggest loss)
stimulus      = diff_chosen / normalization
```

Two decisions made this session, both now written into
`experiments/rq13/design.yaml`:

- **Use `AC`/`PC_r`, not raw `ET`/`PT_r`.** I initially found the user's
  draft used `(ET-PT_r)/ET`. Flagged that this would silently bypass
  RQ11's θ and RQ12's φ whenever either is nonzero — RQ13 needs to
  compose with them the same way φ already composes with θ. User agreed:
  "use AC/PC_r so it composes with RQ11/RQ12."
- **Threshold `tau` as a fraction of `AC`, not fixed seconds.** A
  fixed-second threshold wouldn't generalize: on this network trips
  average ~70-100s, so a real-world "ignore under 5 minutes" intuition
  has to be re-expressed as something like "ignore under ~20% of expected
  cost" to mean anything here.

## 3. Worked examples (tau = 0.20)

**Dead-zone check** (`AC=100`):
- Case A (1s better / 5s worse, both <20%): `g_chosen=g_other=0` →
  `stimulus=0` (correctly suppressed).
- Case B (80s better / 5s worse): `g_chosen=((0.80-0.20)/0.80)^2=0.5625`,
  `g_other=0` → `stimulus=1`.
- Contrast: linear model gives `stimulus=1` for *both* cases (§1);
  nonlinear model separates them (0 vs 1) — the actual point of the
  extension. (Caught and fixed an arithmetic slip in an earlier draft:
  `g_chosen` was written as `1.5625`, should be `0.5625` — doesn't change
  the concluding ratio since it's a self-division, but worth fixing before
  it's quoted anywhere.)

**Where the nonlinearity has teeth** (`AC=100`, chosen NOT the extremal
route):
- Chosen 25% better, some other route 50% better.
- Linear: `stimulus = 25/50 = 0.50`.
- Nonlinear: `g(0.25)=((0.25-0.20)/0.80)^2≈0.0039`,
  `g(0.50)=((0.50-0.20)/0.80)^2≈0.1406`, `stimulus≈0.0039/0.1406≈0.028`.
- A modest, ambiguous win gets compressed from 0.50 down to ~0.03 relative
  to a clearly-larger win elsewhere — this is the real behavioral content
  of RQ13, not just "ignore tiny stuff."

## 4. Key mechanism clarification (the "gotcha" for the meeting)

User's own question: "when the chosen route is also the best, does the
nonlinearity even do anything?" Worked through together — answer: **no,
and that's not a flaw.**

Whenever the chosen route is unambiguously the best (or worst) route that
day, `stimulus = g_chosen / g_chosen = ±1` **always**, regardless of
margin size (1% or 95% — doesn't matter, it's a self-ratio). This is not
something RQ13 introduces or fails to fix — it's a structural property of
eq. 4's max/min normalization, already true under the *current linear*
model for the identical reason. No per-route nonlinearity can touch this
case, because dividing a value by itself is always 1 regardless of what
transform was applied to it first.

The nonlinearity's actual effect is scoped entirely to the non-extremal
case (§3, second example). Whether the flat-±1 ceiling for extremal
choices is itself "realistic" depends on how the stimulus is interpreted:
BM's stimulus isn't literally "surprise magnitude," it's closer to
*relative regret* — "how close to optimal was my choice today." Under
that reading, 21%-better and 95%-better both answer "fully optimal" to
that question, so identical stimulus is arguably correct, not a gap. This
distinction — regret-based vs. surprise-based reaction — is probably worth
raising with the advisor directly, since it reframes what "nonlinear
reaction" is even claiming to model.

**Confirmed still realistic overall**: the dead-zone/quadratic-ramp shape
is a standard first-order approximation of a Weber-Fechner-style
just-noticeable-difference threshold. The one honest caveat is the hard
corner at `tau` (discontinuous derivative) — a stylized simplification of
what's really a graded/probabilistic detection threshold, not a smooth
psychological transition. Same simplification RQ6 already used; not
considered worth complicating unless the advisor flags it.

## 5. Open question — which nonlinear function — genuinely undecided

This is the actual thing pending the advisor's answer (per
`26_08_18.md`'s agenda item 3). Four candidates discussed, only the first
is currently written up as the working default in `design.yaml`:

1. **Dead-zone + quadratic ramp** (RQ6's function, reused as-is). Cleanest
   to implement — no new code, same shape everyone's already seen.
   Downside: hard corner at `tau`, not a literal behavioral claim.
2. **Smoothed dead-zone** (same idea, corner softened via e.g. `tanh`).
   More realistic transition, but adds a steepness parameter with no
   independent narrative payoff — likely not worth it.
3. **Weber-Fechner log-based** (`sign(x)·log(1+k|x|)`, no threshold at
   all). Wrong shape for this RQ's actual claim — decays sensitivity
   gradually rather than truly ignoring small deviations, which
   contradicts the "you don't even notice" framing from §1.
4. **Prospect-theory-style asymmetric gain/loss curvature** (different
   exponent/scale for `x>0` vs `x<0`, loss-aversion `λ>1`). Not a variant
   of the same idea — a genuinely different claim. Current dead-zone is
   symmetric (`x`% better feels exactly as strong as `x`% worse); loss
   aversion says a worse-than-expected route gets punished harder than an
   equally-better one gets rewarded. Possibly better scoped as its own RQ
   (RQ14?) than folded into RQ13.

## 6. Status as of 2026-08-18

- Formula finalized (modulo which function — option 1 above is the
  written default). `experiments/rq13/design.yaml` docstring fully
  written this session: motivation, problem example, formula, threshold
  rationale, worked examples, mechanism-clarification caveat, and the
  open-question list above.
- `base_config:`/`grid:` sections intentionally left unfilled — blocked on
  the advisor's answer, since the config parameter name (`tau`, or
  whatever the eventual function's shape parameter is called) can't be
  decided until the function is.
- No code written in `src/agents/agent.py` yet. Not implemented.
- Separately this session: RQ12 (`r/RQ12/RQ12.qmd`) finished — all 3 plots
  render cleanly end-to-end (data pipeline, mechanism scatter, R-gap
  convergence, qualitative flow-share evolution), three real bugs caught
  and fixed (invalid `\U+03C6` escape, leftover `theta` variable in the
  `phi` closure, `&&` vs `&` on R 4.3+ vectors), ready to commit.
