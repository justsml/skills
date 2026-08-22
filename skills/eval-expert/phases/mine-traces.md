# Mine traces for evals

Use traces to find failure mechanisms, then convert reviewed examples into durable tests.

## Select evidence

Define the time window, population, system versions, and privacy boundary. Sample across success signals, explicit feedback, escalations, retries, tool errors, high cost or latency, policy events, and important user or risk slices. Preserve enough metadata to reproduce the behavior without retaining unnecessary sensitive content.

## Reconstruct and attribute

Reconstruct the observable path: input, retrieved context, model decisions, tool calls and results, handoffs, guardrails, human actions, and final state. Separate outcome failure from process failure. Attribute the earliest consequential divergence when evidence supports it, and mark ambiguity when several paths could explain the result.

Cluster by failure mechanism rather than wording. Useful clusters lead to different fixes or tests. Quantify prevalence only when sampling supports it; otherwise report counts as discovery evidence.

## Promote cases

For each candidate regression, record provenance, minimized reproducible input, expected invariant or acceptable outcome range, relevant trajectory assertions, severity, slice, and why the old behavior failed. Transform private data according to policy and have a human review labels that will become ground truth.

Send metric blind spots back to `phases/design.md`, scorer mistakes to `phases/validate-scorer.md`, executable cases to `phases/run-regressions.md`, and recurring high-value clusters to `phases/optimize.md` after the held-out boundary is protected.

For trace-query and export hints, read [the platform notes](../references/platforms/mine-traces.md) only for the selected platform.

## Completion

Finish with named failure clusters, supporting trace references, uncertainty, prioritized regression candidates, and the next discriminating test for each high-value cluster.
