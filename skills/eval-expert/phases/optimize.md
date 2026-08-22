# Optimize against eval evidence

Search for a change that survives held-out evaluation. A rising development score alone is not success.

## Admit the objective

Start only when the target behavior, metric bundle, scorer validity, baseline, constraints, and held-out boundary are credible. Send gaps back to `phases/design.md` or `phases/validate-scorer.md`. Freeze the held-out set before search — see `SKILL.md` § Maintain the decision record and § Protect the budget and the run for the hard rule against exposing it during search and the cost guardrails for this loop.

Choose the smallest editable component that could explain the failure: prompt, examples, tool schema, routing rule, retrieval setting, policy, or model configuration. Preserve safety gates, output contracts, latency and cost limits, and any user-specified architecture.

## Run the search loop

1. Sample development cases and collect outputs, scores, traces, and scorer feedback.
2. Form a concrete hypothesis from a failure cluster.
3. Propose a bounded change with an expected effect and known tradeoff.
4. Evaluate it against the baseline on the same development cases.
5. Keep, revise, or discard it from paired evidence.
6. Periodically check a validation split and stop when gains flatten, variance dominates, constraints fail, or the budget is spent.

Track the lineage of every candidate. Cache evaluations by complete candidate and evaluator identity. Do not expose held-out examples or labels to the optimizer, and do not let the optimizer rewrite its scorer or acceptance threshold during a run.

Use qualitative scorer feedback as a proposal signal, then trust measured outcomes. Inspect regressions and slice tradeoffs before accepting an aggregate gain. Prefer the simplest candidate within measurement uncertainty of the best result.

For GEPA and platform-specific implementation hints, read [the platform notes](../references/platforms/optimize.md) only for the selected platform.

## When the target is a prompt

When the editable component is a prompt and the loop stalls — a model swap regresses results, gains flatten, or a specific failure cluster won't move — reach for these strategies instead of continuing to poke at the current draft:

- **Check the model card, then verify it.** Look up the target model's official model card and prompting guidance before hand-tuning around unconfirmed folklore (a provider's stated preferences for markup, system-vs-user placement, tool-call conventions, or known quirks). Treat it as a hypothesis to test on the development set, not a fact — providers' own guidance can be stale, generic, or wrong for this task.
- **Strategy 1 — clean slate, then accrete.** Throw out the accumulated prompt and try several genuinely different starting points from scratch. Score each on the development set and keep the strongest one as the new base, even if it looks sparser than the original. Then add instruction chunks back one at a time, each one aimed at a specific failing row or cluster, and keep only the chunks that measurably fix what they targeted. This avoids inheriting dead weight nobody has re-justified since it was added.
- **Strategy 2 — vary markup and register.** Hold the content fixed and vary its packaging: Markdown vs. XML-tagged vs. a mix, dense structured lists vs. human prose, rules-and-requirements framing vs. worked examples. Different models respond differently to the same instructions in different clothing — this is a real axis to search, not cosmetics.
- **Strategy 3 — slice for load-bearing content.** Ablate the prompt section by section (or statement by statement) against the development set to find what each part actually carries: drop a section and measure the delta. Cut sections that are neutral or harmful. For the load-bearing sections, expect little room left to improve — their failures are more likely unrelated to that content. For the minimal or marginal sections, look for outsized gains from small edits, since a small under-tuned part can carry disproportionate improvement once corrected. Don't spend the same tuning effort on both ends of that spectrum.

Run all three as instances of the same search loop above: hypothesis, bounded change, paired evaluation against baseline, keep or discard from evidence. A strategy that sounds principled but doesn't move the development score is still a discard.

## Completion

Confirm the selected candidate once on untouched held-out data. Return its exact configuration, baseline and candidate results by important slice, safety and constraint status, cost and latency impact, experiment lineage, and the accept or reject decision.
