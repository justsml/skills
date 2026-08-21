---
name: eval-run-regressions
description: Implement or operate reproducible AI regression suites across prompts, models, tools, retrieval, and agents. Use when the user needs executable eval cases, candidate comparisons, CI gates, or failure reports.
---

# Run eval regressions

Turn an evaluation contract into a reproducible experiment and a decision, not a pile of scores.

## Establish the run identity

Capture dataset revision, candidate configuration, prompts, model and parameters, tools, retrieval inputs, scorer versions, random seeds when supported, concurrency, retries, and environment. Preserve raw outputs and scorer rationales needed to audit failures. Redact secrets and sensitive user data before sending them to an external evaluator.

## Execute

Run a small smoke slice first. Confirm that cases load, scorers observe the intended fields, failures are visible, and cost is bounded. Then run the planned suite against baseline and candidate under comparable conditions.

Use repeats when nondeterminism can change the decision. Distinguish model failure, scorer failure, infrastructure failure, and missing evidence. Retries may repair infrastructure errors; they must not silently erase behavioral failures.

## Decide from paired evidence

Report coverage, metric distributions, uncertainty, per-slice deltas, critical gate failures, latency, cost, and newly flaky cases. Inspect representative wins and losses. Block on the predeclared gates and call the result inconclusive when the sample or scorer cannot support the decision.

Store durable failures with expected behavior and provenance. Keep experimental output out of the regression corpus until reviewed, so a bad scorer cannot write its own ground truth.

For framework setup and command hints, read [the platform notes](references/platforms.md) only for the selected platform. Follow the repository's existing framework and scripts when present.

## Completion

Finish with a reproducible command or CI job, preserved run identity, a concise comparison, paths to failing cases, and one of: accept, reject, investigate, or gather more evidence.
