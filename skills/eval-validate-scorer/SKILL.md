---
name: eval-validate-scorer
description: Validate, calibrate, or repair an LLM judge or other learned eval scorer. Use when a scorer will guide optimization, compare models, gate a release, or appears biased, unstable, or easy to game.
---

# Validate an eval scorer

Treat the scorer as a measurement instrument. Its prompt can sound sensible while its decisions are useless.

## Define the construct

Write the rubric as observable criteria with anchored examples. Separate dimensions that can disagree. State what evidence the scorer may use, how it handles missing context, and when it must abstain. Prefer pairwise comparison for fine candidate distinctions and direct scoring when an absolute threshold is the real decision.

## Build a calibration set

Sample clear passes, clear failures, boundary cases, important slices, and adversarial cases. Have qualified humans label them independently where the decision warrants it. Reconcile disagreements into rubric changes or explicit ambiguity instead of forcing false consensus.

## Measure validity

Compare scorer output with human labels using statistics suited to the output type. Report uncertainty and per-slice results. Test repeatability across runs and robustness to answer order, verbosity, formatting, identity, irrelevant style, rubric paraphrases, judge-model changes, injected instructions in graded material, and candidates optimized to exploit the rubric.

For trajectory grading, attribute the failure to the earliest consequential decision supported by the trace. Do not blame a later step for state it inherited.

Cache scorer results by the complete evaluation identity, including scorer version, rubric, judge model and settings, input, candidate output, reference material, and relevant trace. Re-evaluate only affected examples after a scorer change, then run the full calibration set before promotion.

If implementation depends on a particular service or framework, read [the platform notes](references/platforms.md) only for the selected platform.

## Promotion gate

Promote the scorer only when agreement, stability, bias tests, slice behavior, failure examples, and the acceptable error tradeoff are documented. A scorer that fails calibration remains diagnostic evidence, not an optimization objective or release gate.
