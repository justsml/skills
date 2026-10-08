# Decisions, uncertainty and the comparison helper

## Evidence sufficient for a decision

Acceptance requires a valid workload/harness, comparable environments, a meaningful confirmed objective gain, preserved correctness/product gates and bounded regressions for every required slice/resource metric. A larger mean throughput cannot cancel a tail/error/quality failure. If a deliberate tradeoff is required, present its measured frontier and obtain or reuse the user's product decision; it is not an automatic win.

Record absolute values and deltas as well as percentage change. Speedup `baseline/candidate` for time is different from percent time saved `1-candidate/baseline`; do not swap them. Report independent runs and spread, not only a best run. For quantiles retain definitions, underlying request/frame count, independent session count and uncertainty appropriate to that hierarchy. A percentile of per-run percentiles is not the pooled percentile; say what was summarized.

Use the simplest valid analysis for the design. Matched independent blocks can use paired effects and whole-block resampling. Unpaired fleets, censored latency, zero counts, strong autocorrelation and hierarchical workloads need another analysis. Do not make a universal statistics helper stand in for validating the experiment. A fixed confirmation schedule and predeclared gates protect against repeatedly testing until green; screening many candidates still requires fresh confirmation.

## Optional local helper

`scripts/compare.mjs` requires Node 20+; equivalent `scripts/compare.py` requires Python 3.10+. Neither needs packages/network. `scripts/compare.sh` is a Bash 3.2+ dispatcher selecting compatible Node first, then Python; it cannot run the statistics with Bash alone. Probe runtime versions and choose an existing compatible interpreter; record and keep it for the entire experiment. Fall back only for absence/incompatibility, never for a rejected experiment. Do not install a runtime just for this optional helper. Both implementations share the integer-seeded bootstrap draw sequence; numeric outputs may differ by floating-point roundoff (parity tests use 1e-10 relative/absolute tolerance), especially at a gate boundary. Do not switch runtimes to obtain acceptance; investigate boundary cases as uncertain. It reads one explicit JSON artifact and emits a JSON decision; it never executes the benchmark, modifies code, changes thresholds or validates the honesty of the collected evidence.

```text
node <skill-directory>/scripts/compare.mjs /path/to/experiment.json
bash <skill-directory>/scripts/compare.sh /path/to/experiment.json
node --test <skill-directory>/scripts/compare.test.mjs
python3 <skill-directory>/scripts/compare.py /path/to/experiment.json
python3 -m unittest discover -s <skill-directory>/scripts -p 'test_*.py'
```

Supported analysis: strictly positive per-block metric values, matched independent blocks, balanced AB/BA order, unprofiled outcome measurements. Every metric is a scenario/metric combination and is independently gated. Inputs carry matching environment/workload/harness identities, distinct source treatment identities, explicit hard checks and a predeclared design. This is a ratio analysis for positive durations/throughputs/memory/cost; error counts and quality/fidelity should use their task oracle or a suitable separate analysis, not fabricated positive values.

Version-1 format (illustrative schema; supply all actual blocks and gate rows):

```json
{
  "version": 1,
  "experiment_id": "parser-chunking-confirm-001",
  "phase": "confirm",
  "baseline": {"revision": "base-sha", "environment_id": "env-hash", "workload_id": "fixture-hash", "harness_id": "harness-hash"},
  "candidate": {"revision": "candidate-sha", "environment_id": "env-hash", "workload_id": "fixture-hash", "harness_id": "harness-hash"},
  "design": {"unit": "independent-paired-block", "min_blocks": 8, "confidence": 0.95, "resamples": 10000, "seed": 42, "profiled": false},
  "hard_checks": [{"id": "record-fidelity", "baseline": "pass", "candidate": "pass", "evidence": "artifacts/output-check.json"}],
  "metrics": [{
    "id": "large-warm.elapsed", "unit": "ms", "direction": "lower", "role": "primary", "threshold_pct": 5,
    "blocks": [{"id": "block-01", "order": "AB", "baseline": 100, "candidate": 90, "valid": true}]
  }]
}
```

`revision` can be a commit plus patch/config identity or a same-build feature-flag treatment; labels alone do not prove matching artifacts. `environment_id`, `workload_id` and `harness_id` are stable manifest/digest identities, with manifests retained alongside raw artifacts. An identity mismatch invalidates comparison; update the experiment and rerun both arms rather than deleting the field.

`min_blocks` must be chosen before the runs and at least four for this helper's resampling; four is a validation floor, not a recommended or sufficient sample size. `confidence` is 0.8–0.999; `resamples` is 2,000–200,000. Use enough resamples for the number of metrics and requested tail resolution. At least one primary metric and one passed hard check are required. Each metric has unique block IDs, at least one AB and BA block with count difference at most one. All rows remain present, including invalid samples. `valid: false` invalidates this comparison; fix the cause and report a new run rather than dropping the attempt silently.

For a **primary**, `threshold_pct` is the minimum practically useful positive improvement. For a **guardrail**, it is the maximum tolerated regression. Improvement is `(1 - candidate/baseline) × 100` for lower-is-better and `(candidate/baseline - 1) × 100` for higher-is-better, based on the geometric mean paired ratio. The helper resamples paired log ratios at the block level and uses conservative Bonferroni-adjusted percentile bounds across the declared metric family. These are **approximate bootstrap intervals**, conditional on independent comparable blocks; adjustment does not make biased/undersampled data reliable. The method does not correct repeated peeking, candidate search or omitted metrics.

To pass, each primary's lower improvement bound must meet its meaningful-effect threshold and each guardrail's lower bound must stay within its allowed regression. A clearly slower primary or clearly breached guardrail rejects. A clearly insufficient gain keeps the baseline. A boundary-crossing interval, unknown hard check or insufficient blocks is inconclusive. Baseline hard-check failure, invalid work, altered identities or profiled outcome data is invalid. Candidate correctness failure rejects. Passing screening yields `needs_confirmation`; only passing fresh `confirm` evidence yields `accept` under the declared contract.

Exit codes: `0` accept; `1` reject/keep-baseline; `2` invalid input/experiment; `3` inconclusive/needs-confirmation. JSON remains available for all validly parsed decisions. A report includes arm medians/ranges, paired effect, adjusted interval, independent block count and individual gate decisions. Retain input/raw reports and record the helper version/digest for reproducibility. Identical repeated ratios and very small blocks should prompt scrutiny of quantization, duplicated samples and underrepresented noise.

## Integration and regression protection

Screening may use a microbenchmark, but confirmation includes the real operation and every important slice. Corroborate predicted mechanism change with a short diagnostic profile, and rerun the final combined patch unprofiled. Reversion/ablation can distinguish the proposed mechanism from unrelated drift. Keep failed experiments as evidence with exact treatment and rejection reasons.

Use correctness/complexity/work-count checks in ordinary CI where stable. Use performance thresholds on controlled dedicated runners with a recorded baseline, drift detection and review of uncertainty; do not add brittle laptop timing assertions. Protect the mechanism where possible (for example, one lookup build per lifecycle or bounded request fanout) with behavioral instrumentation, without merely asserting source text.

Delivery includes the reviewed plan, accepted diff, rerun command, raw artifacts, gate results and limitations. Distinguish validated local behavior, supported inference and untested production conditions. An inconclusive no-change outcome with a reproducible bottleneck is useful; invented precision is not.

## Concise findings for every target

Use this for browser, CPU, GPU, service, build/import and prompt/agent investigations. Lead with the result and the next useful action. Keep raw details in linked artifacts. Give a summary even when all checks passed, no change was worthwhile, or the work is blocked.

1. **Outcome:** accepted gain, rejected/no-change candidate, diagnosis or blocker; include the key metric, workload/environment and confidence/limits.
2. **Checked:** a compact scope line listing instruments, scenarios, gates and evidence paths actually examined. Mention consequential not-run checks rather than implying complete coverage.
3. **Findings:** prioritize actionable rows, grouping minor observations where useful.

| Priority / finding | Evidence status and support | Action / smallest next proof |
|---|---|---|
| <user impact> | **Proved**: reproduced/measured under named conditions | <fix or keep, validation> |
| <likely contributor> | **Supported suspicion**: correlated evidence; cause not isolated | <discriminating test> |
| <remaining question> | **Unknown / blocked**: what cannot yet be established and why | <specific access, capture or user decision needed> |

Separate an observed symptom from its suspected cause: a two-second TTFB may be proved while a geographic CDN detour is still unproved. “Proved” applies to the stated experiment, not universal behavior. State where evidence is difficult to obtain and what would resolve it; ask for narrow useful help, not a vague request to debug. Finish with the recommended next action and any material remaining risk/coverage gap. Avoid overwhelming the user with tool names, speculative fixes or unsupported precision.
