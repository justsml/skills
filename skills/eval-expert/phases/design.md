# Eval design

Build an evaluation contract that can distinguish a useful change from a merely higher score.

## Phase contract

- **Enter when:** the product claim, risk, metric, threshold, or release decision is undefined or disputed.
- **Required inputs:** the AI behavior in scope, the decision the evidence must support, known failures, operating constraints, and available evidence.
- **Result:** an evaluation contract mapping each claim and blocking risk to cases, scorers, slices, thresholds, and decision rules.
- **Complete when:** every in-scope claim and gate has a measurable contract or a named evidence gap.
- **Next route:** send case construction to `build-dataset.md`, scorer work to `build-scorer.md`, and unresolved product claims back to the user.

## Start from decisions

Name the decision the eval will support, the behavior users were promised, and the failures that would block release. Inspect the system path and available evidence before choosing metrics.

For each claim or risk, define:

- the unit of evaluation and representative population;
- curated, production-derived, adversarial, and regression cases as needed;
- slices that could hide behind an aggregate;
- a deterministic check, model judge, human review, or combination;
- a threshold tied to a baseline, tolerance, or operating constraint;
- the action taken on pass, fail, or inconclusive evidence.

Use deterministic checks for schemas, exact state, tool arguments, citations, calculations, and policy rules. Use learned judges for qualities that require interpretation. Use human experts to establish ground truth and calibrate consequential or subjective judgments.

## Build a metric bundle

Combine metrics only when each catches a distinct failure. Keep end-state task success, trajectory quality, factual support, severe safety gates, and operating cost separate when they can disagree.

Specify aggregation and missing-data behavior. Report paired results and slice deltas when comparing candidates. Do not let a weighted average compensate for a critical gate failure.

Keep development and held-out sets separate. Record provenance, privacy constraints, deduplication policy, expected-output flexibility, and version identifiers. Add production failures to a regression set only after labeling the failure and desired behavior.

## Review for validity

Try to break the design. Look for construct mismatch, synthetic-only coverage, label leakage, contamination, arbitrary thresholds, one-path trajectory grading, style-sensitive judges, correlated metrics, and slices too small to support a claim.

If implementation depends on a particular service or framework, read [the platform notes](../references/platforms/design.md) only for the selected platform.

## Completion

Return an evaluation contract in which every release claim and blocking risk maps to cases, a scorer, slices, a threshold, and a decision rule. Mark unsupported cells as open evidence gaps rather than inventing precision.
