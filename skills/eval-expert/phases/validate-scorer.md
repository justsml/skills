# Validate an eval scorer

Treat the scorer as a measurement instrument. Its prompt can sound sensible while its decisions are useless.

## Phase contract

- **Enter when:** a learned or heuristic scorer may influence tuning, release, or safety decisions, or its judgments appear unstable or gameable.
- **Required inputs:** the scorer version, rubric, representative calibration cases, qualified human labels, and an acceptable error tradeoff.
- **Result:** a validation report with agreement, uncertainty, stability, bias, slice behavior, and promotion status.
- **Complete when:** the evidence supports promotion or records why the scorer remains diagnostic only.
- **Next route:** promote credible scorers to `run-regressions.md`; send rubric defects to `design.md`, case gaps to `build-dataset.md`, and implementation defects to `build-scorer.md`.

Before building a calibration set, read [the cost guards](../cost-guards.md) for smoke-slice, retry, and abort rules.

## Define the construct

Write the rubric as observable criteria with anchored examples. Separate dimensions that can disagree. State what evidence the scorer may use, how it handles missing context, and when it must abstain. Prefer pairwise comparison for fine candidate distinctions and direct scoring when an absolute threshold is the real decision.

## Build a calibration set

Sample clear passes, clear failures, boundary cases, important slices, and adversarial cases. Have qualified humans label them independently where the decision warrants it. Reconcile disagreements into rubric changes or explicit ambiguity instead of forcing false consensus.

## Measure validity

Compare scorer output with human labels using statistics suited to the output type. Report uncertainty and per-slice results. Test repeatability across runs and robustness to answer order, verbosity, formatting, identity, irrelevant style, rubric paraphrases, judge-model changes, injected instructions in graded material, and candidates optimized to exploit the rubric.

For trajectory grading, attribute the failure to the earliest consequential decision supported by the trace. Do not blame a later step for state it inherited.

Cache scorer results by the complete evaluation identity, including scorer version, rubric, judge model and settings, input, candidate output, reference material, and relevant trace. Re-evaluate only affected examples after a scorer change, then run the full calibration set before promotion.

If implementation depends on a particular service or framework, read [the platform notes](../references/platforms/validate-scorer.md) only for the selected platform.

## Promotion gate

Promote the scorer only when agreement, stability, bias tests, slice behavior, failure examples, and the acceptable error tradeoff are documented. A scorer that fails calibration remains diagnostic evidence, not an optimization objective or release gate.
