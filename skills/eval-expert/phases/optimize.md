# Optimize against eval evidence

Search for a change that survives held-out evaluation. A rising development score alone is not success.

## Phase contract

- **Enter when:** a credible metric, validated scorers, reproducible baseline, protected held-out set, bounded target, and approved budget already exist.
- **Required inputs:** the editable component, development and validation cases, frozen held-out identity, baseline, constraints, scorer versions, and stop budget.
- **Result:** an accepted or rejected candidate with exact configuration, lineage, slice results, held-out confirmation, cost, and constraint status.
- **Complete when:** the selected candidate receives one untouched held-out check or the search stops for budget, plateau, variance, or constraint failure.
- **Next route:** send metric defects to `design.md`, scorer defects to `validate-scorer.md`, missing cases to `build-dataset.md`, and accepted release evidence to the owning release process.

## Admit the objective

Start only when the target behavior, metric bundle, scorer validity, baseline, constraints, and held-out boundary are credible. Send gaps back to `phases/design.md` or `phases/validate-scorer.md`. Freeze the held-out set before search. See [the decision record](../SKILL.md#maintain-the-decision-record) for the isolation rule and read [the cost guards](../cost-guards.md) before running the loop.

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

When the editable component is a prompt and the loop stalls — a model swap regresses results, gains flatten, or a specific failure cluster won't move — read [the prompt-tuning strategies](../prompt-tuning.md) instead of continuing to poke at the current draft.

## Completion

Confirm the selected candidate once on untouched held-out data. Return its exact configuration, baseline and candidate results by important slice, safety and constraint status, cost and latency impact, experiment lineage, and the accept or reject decision.
