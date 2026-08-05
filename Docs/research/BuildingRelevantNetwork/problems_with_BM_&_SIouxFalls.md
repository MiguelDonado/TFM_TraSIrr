Reasonable, clearly-documented deviations from the paper (engineering necessities, not errors):
- A small epsilon is added to stimulus denominators to avoid divide-by-zero — this only pads the bound, doesn't break the paper's guaranteed |S| ≤ 1.
- A warm-up gate (episode > warm_up and all routes visited once) delays learning until every route has been observed at least once, avoiding NaN in PT — the paper's simulation doesn't need this since it's not concerned with cold-start per-route data.

 The perceived travel times. I have a doubt, because if i only visited one route once, 20 days ago, then i will still remember perfectly the cost of the route that day. Thats correct?. The paper says the same?

Yes — that's correct, and it follows directly from eq. 6 in the paper.

PT for route k is a weighted average, not a decaying quantity:

M_ik^t = Σ_j ψ^(t−j)·T_j·ξ_jk / Σ_j ψ^(t−j)·ξ_jk

If route k was chosen exactly once, at day j₀, both sums collapse to a single term:

M_ik^t = ψ^(t−j₀)·T_{j₀} / ψ^(t−j₀) = T_{j₀}

The decay weight appears in both numerator and denominator and cancels exactly — regardless of how large t − j₀ is, or what γ is (as long as γ > 0). So a route visited once 20 days ago is remembered with the exact travel time from that day, undiminished, forever (until visited again).

This isn't decay of a memory's "strength" — γ only controls the relative weighting between multiple observations of the same route. With only one observation, there's nothing to weigh it against, so the average is just that one sample.

The code (_compute_perceived_travel_times) reproduces this identically — numerator[r]/denominator[r] for a single-visit route reduces to that one tt value the same way. So implementation matches the paper faithfully here; this isn't a bug.
Worth flagging as a modeling property rather than a fix: it means a route explored only once keeps a "crisp," never-fading PT based on a single (possibly lucky/unlucky) sample, while frequently-chosen routes get smoothed, multi-sample averages. That asymmetry is inherent to the paper's formula, not something the codebase introduced.

Yes, exactly — with two or more observations to weigh against each other, γ becomes a real recency-decay parameter. The single-visit case is the degenerate exception, not the rule.

Why it's different with ≥2 observations:

For PT with two visits to route k, at days j₁ < j₂:

M_ik^t = [γ^(t−j₁)·T_{j₁} + γ^(t−j₂)·T_{j₂}] / [γ^(t−j₁) + γ^(t−j₂)]

This time the γ terms don't cancel — they're different for each day, so they act as genuine relative weights. Dividing num/denom by γ^(t−j₂) (the more recent, larger term) gives:

M_ik^t = [γ^(j₂−j₁)·T_{j₁} + T_{j₂}] / [γ^(j₂−j₁) + 1]

As γ → 0, the older observation T_{j₁} is washed out and PT ≈ T_{j₂} (only the latest visit matters). As γ → 1, both observations get equal weight (plain average, "perfect memory"). That's a real decay effect — the older sample's influence shrinks geometrically with both γ and the gap j₂ − j₁.

Same logic for ET, which pools travel times across all routes chosen over time: with many terms in the sum, γ < 1 means travel times from further back contribute exponentially less to the current expectation. This matches the paper's own description (§3.2): "travelers weight recent travel time more than older ones... the smaller the ψ-value, the less the travel time of the past days influence travelers' current ET and PT," and ψ = 1 is explicitly the "ideal state" where "travelers remember all travel time they have experienced... the travel time of each day has the same effect."

So the rule of thumb: γ only does work when there are multiple data points competing for weight. With one observation, normalization strips the decay out entirely (as you noted for the single-visit PT case); with several, it behaves as a proper exponential recency filter — which is exactly the paper's intent for both ET and PT.

- Well yeah, it washes out the older observation, but the most recent observation is never washed out, even with very low memory and if it happend 100 days ago.
You've spotted something real and worth stating precisely: the current day t actually cancels out of the PT formula entirely. Watch what happens with an arbitrary number of visits to route k, at days j₁ < j₂ < ... < jₙ (jₙ = most recent visit):

M_ik^t = Σᵢ γ^(t−jᵢ)·T_jᵢ / Σᵢ γ^(t−jᵢ)

Factor γ^(t−jₙ) out of every term (numerator and denominator alike) and it cancels completely:

M_ik^t = Σᵢ γ^(jₙ−jᵢ)·T_jᵢ / Σᵢ γ^(jₙ−jᵢ)

t is gone. PT for route k depends only on the gaps between visits to that specific route, never on how far today is from the last visit. So:

- The most recent visit (jₙ) always carries weight γ^0 = 1 — full weight, by construction, no matter whether jₙ was yesterday or 400 days ago.
- Older visits to that route (j₁, j₂, ...) are discounted relative to jₙ, by γ^(jₙ−jᵢ) — that's the real decay you identified earlier.
- But there's no term anywhere that discounts jₙ itself relative to "now." A route last driven 100 days ago, never revisited since, produces exactly the same PT today as it would have produced the day after that 100th-day visit.

Same cancellation happens in the ET formula, for the same algebraic reason — but it's less visible there because ET pools travel time from every day regardless of route, so in practice the most recent term (day t−1) is always "yesterday," never stale.

So the precise characterization: γ in this model is a relative-recency weight among an action's own observation history, not a staleness/freshness decay tied to the current day. Nothing in the paper's formulation makes a memory less trusted just because it's old in absolute terms — only because newer memories of the same route exist to outweigh it. An infrequently-explored route keeps an undiminished, fully-confident PT based on whatever its last visit happened to show, indefinitely. That's a genuine structural property of eq. 6 (not an implementation quirk — the code inherits it faithfully), and it's arguably a real limitation of the model if you wanted "confidence in a memory" to erode with elapsed time rather than just with newer competing samples.

Could you read /home/miguel/6.Projects/Thesis/data/agent_state/agent_debug_trace.json. How it is possible that with memory 0.001, still works the algorithm and is able to lower the mean travel time

  Ran 3 shell commands

I traced through the JSON — it's a single agent (agent_1000, 8 routes) logged episode-by-episode with p, ET, PT, and stimulus. The answer is visible directly in the numbers: with γ = 0.001, the algorithm doesn't actually retain 100 days of memory — it degenerates into a one-day-lookback comparison, and that's still enough to find the cheap route.

Look at the actual values (episode 25–29):

ep=24 route=6 tt=118.00
ep=25 route=7 tt=133.00  ET=117.999  PT_chosen=133.000
ep=26 route=5 tt=149.00  ET=132.985  PT_chosen=149.000
ep=27 route=7 tt=155.00  ET=148.984  PT_chosen=155.000

Two things jump out:
- PT_chosen ≈ today's tt, exactly. ep25 PT_chosen=133.000 = today's tt=133.00. Every single row in the trace shows this.
- ET(t) ≈ tt(t−1), exactly. ep25's ET=117.999 ≈ ep24's tt=118.00. ep26's ET=132.985 ≈ ep25's tt=133.00.

This is exactly the cancellation we worked out earlier, taken to the extreme. With γ=0.001:
- PT for the chosen route: the just-observed tt gets weight γ⁰=1, and any earlier visit to that same route (even yesterday) gets weight ≤ γ¹ = 0.001 → contributes ~0.1% → PT_chosen collapses to just today's observation.
- ET: same mechanism, but pooled across all routes/days — the day-(t−1) term gets weight 1, day-(t−2) gets weight 0.001, etc. → ET collapses to just yesterday's observed travel time, whatever route that was.

So the stimulus formula (ET − PT_chosen)/norm effectively becomes:

stimulus(t) ≈ normalize(tt(t−1) − tt(t))

— "was today's route better than whatever I happened to experience yesterday?" There's no real long-run expectation being compared against; it's a myopic win-stay/lose-shift rule.

Why that's still enough to converge: this network clearly has one persistently cheap route (route 0, tt ≈ 112–120) versus the rest (tt ≈ 130–220+, congestion-dependent). Because route 0 is almost always cheaper than whatever was tried the day before, the one-step comparison usually has the correct sign whenever route 0 gets sampled — giving stimulus ≈ +1 and a big reinforcement jump (see ep29, ep31, ep37...: p_chosen jumps 0.36→0.55→0.58...→0.80 by ep100). When a worse route gets sampled after the agent has drifted toward route 0, it looks bad by comparison and gets punished (ep34: route 2, tt=201 vs ET=131 → stimulus=−1.0, p_chosen crashes 0.56→0.03).

So it's not that low memory is "harmless" — it destroys the model's ability to hold a stable, averaged expectation (which is why the paper needed ψ close to 1 to get the smooth UE convergence you'd see in Figures 5–10; recall the tables showed low ψ giving weak-to-no convergence in their multi-agent, congestion-dependent setting). Here it still trends toward the good route because there's a large, mostly-consistent gap between route 0 and the alternatives, so a naive "beat yesterday" heuristic is a noisy but adequate proxy gradient. If the routes were closer in cost, or cost ranking flipped often due to congestion, this degenerate γ=0.001 regime would likely fail to converge cleanly (much more oscillation, since it's reacting to single noisy samples rather than a stable average) — which is consistent with what the paper itself found for low memory levels.

Good question — and the trace explains exactly why the current setup won't easily let you reproduce the paper's "low memory → no convergence" result. Here's the mechanism and what to change.

Why it converges anyway: as shown, with tiny γ, PT_chosen collapses to today's observation and ET collapses to yesterday's observation. The Bush-Mosteller update degenerates into a myopic "was today better than yesterday" rule. That's still a perfectly functional (if noisy) hill-climbing signal whenever one route is a persistent, large-margin winner — which route 0 clearly is in this trace (tt≈112–120 vs 130–220+ for everything else). No amount of memory-shortening breaks convergence to an option that's almost always better than whatever came before it.

The paper's non-convergence under low ψ isn't really about an individual agent losing the plot — it's a population-level congestion feedback effect: many agents simultaneously chase "yesterday's good route," collectively overload it, which makes it worse the next day, causing everyone to bail simultaneously, then flip back — that's their "cyclical oscillation" (Fig. 18). That effect needs (a) enough shared demand on a route relative to its capacity that switching mass visibly moves its congestion, and (b) route costs close enough together that this back-and-forth can actually flip the ranking. A single agent's own greedy "yesterday vs today" heuristic, on an OD pair with one dominant cheap route, will converge basically regardless of γ.

I already tried, and it still converges cleanly. What should i do

Let me pull the actual route-level travel-time data from that same run to check whether route 0 ever loses its rank at all — that's the decisive diagnostic before tuning further.

  Searched for 3 patterns, ran 9 shell commands

Found it — I pulled the actual run that used your learning_rate=0.9, memory_level=0.001 attempt (data/agent_state/actions.parquet + agents_od_all.parquet, run 9ce1ed7f...) and it does fail to converge. It's just invisible in mean travel time.

Single agent (agent_1000) — its own policy never settles:
ep 29-58:  locks onto route 0  (p≈0.99+)
ep 59-68:  flips to route 5    (p≈0.99+)
ep 69-86:  flips back to route 0
ep 87-100: flips to route 5 again
It's fully committing (>99% probability) and then completely reversing, repeatedly, within the 100-episode run.

Population level (all 179 agents sharing that OD pair) — the flow split doesn't stabilize either. I computed each route's share of that OD's traffic per episode and compared the mid-run window (ep 40–70) to the late-run window (ep 70–100):

route 0: mid mean=0.239 std=0.024  →  late mean=0.275 std=0.022
route 5: mid mean=0.269 std=0.027  →  late mean=0.297 std=0.029
route 6: mid mean=0.166 std=0.024  →  late mean=0.157 std=0.023

The standard deviation isn't shrinking toward zero — it's the same ~0.02–0.03 noise band all the way to episode 100. In the paper's Fig. 6/15, that std is exactly what collapses as the network reaches UE. Here it just doesn't.

Why it "looks" converged anyway: routes 0, 4, 5, 6, 7 all cluster around similar travel times (~112–135s), while routes 1, 2, 3 (~150–220s) get correctly and permanently abandoned. So mean travel time drops fast and stays flat — but that flat mean is consistent with the flow bouncing around within the competitive tier indefinitely. Averaging over near-tied alternatives hides the instability; it doesn't remove it.

What to do: stop judging convergence off mean travel time — judge it off flow/policy stability, which the codebase already computes:
1. mean_policy_change, already tracked by your stopping rule (stopping_rule.py) every episode — this run went the full 100 episodes without triggering should_stop, which is itself evidence it never stabilized. Pull policy_change_BM.parquet and plot that trajectory; it should show persistent non-decay at this config, versus decay-to-near-zero at memory_level=1.
2. Per-route flow share std over a trailing window (what I just computed above) — or the paper's own FSD statistic (Fig. 15) — computed per OD pair, not network-wide mean travel time.

So the algorithm is already doing what you wanted at (β=0.9, γ=0.001) — you were just looking at a metric (mean travel time) that happens to be insensitive to it in this particular route-cost structure.

Your teacher's right, and pulling the actual R-gap data changes my answer. Let me show what I found, because it also resolves the dichotomy you're pointing at.

I checked data/DUE/BM/R-gap/rgap.parquet and rgap_by_od.parquet for the exact run you ran (β=0.9, γ=0.001). Both the network-wide R-gap and the R-gap specific to agent_1000's OD pair do converge — they shrink from ~±20–40% early on down to a tight band of roughly ±1–2.5% by episode 70–100, and for the OD-specific series the standard deviation actually keeps decreasing (1.57 → 1.11 from the mid-run to late-run window). By the metric that actually defines DUE, this run is reaching near-equilibrium.

This means my earlier "policy flip-flopping = non-convergence" framing was wrong, and here's why it matters: DUE (Wardrop equilibrium) only requires that used routes have equal, minimal cost — it says nothing about which agent uses which of several equal-cost routes, or how that split evolves. Routes 0, 4, 5, 6, 7 in this OD pair all sit around 112–135s — meaning flow reshuffling among them isn't a equilibrium violation, it's exactly what you'd expect at equilibrium when multiple routes are cost-tied (UE doesn't pin down a unique split in that case). R-gap correctly ignores that churn because it's only sensitive to whether people are using routes meaningfully costlier than the cheapest available one — and they mostly aren't. My "check flow-share variance" suggestion was measuring something that isn't actually a DUE failure.

So to your real question — does the network's route-cost structure matter, and is my earlier dichotomy real:

Yes, but it's sharper than I put it, and it now applies to R-gap too, not just mean travel time:

- If one route dominates everywhere: R-gap converges trivially (equilibrium requires ~100% on that route, and any reasonable learning rule finds it — no test of memory).
- If several routes are genuinely cost-tied across the full range of loads that occur: R-gap also converges easily, regardless of γ, because almost any split among them is near-optimal — which is exactly what you're seeing now. The network is "forgiving": there's enough slack/redundant capacity that mis-tracking equilibrium barely costs anything.

The condition you actually want is neither of those — you want a network/OD structure where the correct equilibrium flow split is narrow and load-sensitive: routes whose relative cost ordering flips as flow shifts (a real crossover, not a static tie), so that a route being "temporarily favored" by noisy myopic learning becomes measurably worse once enough agents pile onto it. That's what makes R-gap sensitive to γ — because getting the split wrong now has a real, non-negligible cost.