---
name: eval-optimize
description: Improve prompts, policies, tools, retrieval, or agent configuration through an eval-driven search loop. Use when a credible baseline and objective exist and the user wants systematic tuning without overfitting the eval.
---

# Optimize against eval evidence

Search for a change that survives held-out evaluation. A rising development score alone is not success.

## Admit the objective

Start only when the target behavior, metric bundle, scorer validity, baseline, constraints, and held-out boundary are credible. Send gaps back to `eval-design` or `eval-validate-scorer`. Freeze the held-out set before search.

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

For GEPA and platform-specific implementation hints, read [the platform notes](references/platforms.md) only for the selected platform.

## Completion

Confirm the selected candidate once on untouched held-out data. Return its exact configuration, baseline and candidate results by important slice, safety and constraint status, cost and latency impact, experiment lineage, and the accept or reject decision.
