---
name: eval-planner
description: Coordinate an end-to-end evaluation program for an AI feature or agent. Use when the work spans metric design, scorer validation, regression execution, trace analysis, and iterative optimization, or when the user wants one maintained eval plan across those activities.
---

# Eval planner

Keep one decision record for the evaluation program and route each piece of work to the narrow skill that owns it.

## Route the work

- Use `eval-design` to turn product claims and risks into datasets, metrics, slices, and decision gates.
- Use `eval-build-dataset` to curate versioned development, validation, held-out, and regression cases.
- Use `eval-build-scorer` to implement one evidence-producing scorer per metric.
- Use `eval-validate-scorer` before a learned scorer can influence tuning, release, or safety decisions.
- Use `eval-run-regressions` to make the design executable and compare candidates reproducibly.
- Use `eval-mine-traces` when production or experiment traces are the evidence source.
- Use `eval-optimize` only after the objective and held-out evaluation are credible.

Do the requested phase directly. For multi-phase work, sequence it as failure discovery, design, dataset construction, scorer implementation, scorer validation, baseline execution, optimization, then held-out confirmation. Re-enter design whenever evidence shows that the metric rewards the wrong behavior or misses an important failure.

## Maintain the decision record

Prefer the user's existing artifact. Otherwise create `.scratch/evals/<short-name>/plan.md` with only the sections that carry current decisions:

```markdown
# <name>

## Target behavior and release decision

## Evaluation contract

| Claim or risk | Dataset slice | Metric or gate | Scorer | Threshold | Evidence |
| --- | --- | --- | --- | --- | --- |

## Experiments

| Candidate | Change | Development result | Held-out result | Cost and latency | Decision |
| --- | --- | --- | --- | --- | --- |

## Open failures and next actions

| Failure cluster | Evidence | Likely cause | Next discriminating test | Owner |
| --- | --- | --- | --- | --- |

## Decisions

| Date | Decision | Evidence | Revisit when |
| --- | --- | --- | --- |
```

Keep tuning examples separate from the held-out set. Record dataset, prompt, model, tool, and scorer versions for every result used in a decision. Treat critical safety, privacy, authorization, and irreversible-action failures as gates rather than averages.

## Completion

Finish when the current decision is stated, its evidence is reproducible, remaining uncertainty is explicit, and the next action has an owner or the program has a justified stop decision.
