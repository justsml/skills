# Measurement design

## Define useful work

A benchmark must demonstrate the operation, not merely return a duration. Keep executable oracles separate from performance metrics. Validate semantic outputs, amount of work, error/cancellation status and user-visible invariants. Parsers preserve records and fidelity; imports verify committed IDs and deduplication; builds verify requested artifacts; browser interactions verify settled state and navigation; services account for arrivals, completions, failures, retries and timeouts. A faster error path or skipped animation is not an improvement.

Keep one canonical input/workload/oracle version across both arms. If the harness changes, collect both arms again and explain the new experiment identity. Test the oracle against an intentional local skipped-work/failure case so it cannot pass vacuously. Do not make such a sentinel destructive or send real production traffic. Read enough real call sites to avoid benchmarking an unused path.

## Define metrics before collecting them

Record unit, numerator/denominator, timing boundaries, aggregation and sample unit. Request latency includes queueing only if timed from arrival; kernel time excludes transfers unless explicitly captured; cumulative counters need phase deltas; summed overlapping thread/task durations can exceed wall time. Count memory peaks and retained growth separately, throughput as successful useful units per second, and cost per valid completed unit. Report cold startup and steady state separately. Never label automation round trips as a native user-experience metric or an aggregate mean as p95.

Freeze important slices: input size/skew, browser interaction, device/renderer, cache state, concurrency and load. Workload-weighted summaries may help business decisions but never hide a failing slice. A small sample's extreme quantiles are unstable; report sample count and quantile method. Keep time series/histograms where tails or periodic stalls matter. Prefer the actual outcome objective over a convenient proxy; supporting counters explain it rather than replace it.

## Control the environment

Record actual build and runtime versions, OS/architecture, CPU/GPU/VRAM/RAM, allocator/GC settings, renderer/driver, container limits, quotas, storage/filesystem and power/thermal conditions where consequential. Pin load generator and fixture distributions. A remote machine must reproduce the relevant execution path, not merely be faster hardware. Diagnose background jobs, frequency scaling, warmup/JIT/compilation and thermal drift without turning off unrelated services.

Separate warm and cold definitions. HTTP cache, service worker, OS page cache, database buffer pool, application memoization, model/prefix cache and GPU compilation caches are different. Say which were reset. Use supported task-scoped reset mechanisms; do not drop shared machine caches or modify host-wide security/power settings without authorization. Stateful imports/builds need a verified reset before each repetition. Restarts may not clear every cache.

## Pair, repeat and preserve raw data

Use matched arms in an isolated workspace or same-build treatment flag. Balanced randomized AB/BA blocks reduce temporal/order effects; deterministic ABBA can be appropriate with recorded rationale. Include adequate warmup outside measured windows. Every observation retains block/order, timestamps, commands, environment, valid-work status and raw outputs. Profilers add overhead: use short diagnostic captures and uninstrumented timing runs, or report both with overhead quantified.

An independent experimental unit is commonly a process/session/load-test block, not every frame, token or request emitted inside it. Resample whole blocks when internal observations are correlated. Serial requests on one warm process are not thousands of independent replications. Prefer per-block summaries for comparison, and retain underlying distributions so aggregation does not erase stalls. Pairing is useful only if matched conditions/reset are valid; use a design-appropriate alternative for unpaired fleets or highly stateful systems.

Choose repetitions and meaningful effect from pilot variability and the engineering decision. Three medians or a fixed ten-run convention does not establish certainty. Do not keep increasing sample size after seeing outcomes until a threshold passes. Use a fixed confirmation schedule or an explicitly planned sequential method. Include all valid runs; exclusions require a predeclared or demonstrable infrastructure cause and appear in the report. Preserve invalid attempts rather than turning them into wins.

## Screen versus confirm

Cheap development cases can reject a hypothesis quickly. Search over candidates/parameters makes the best development measurement optimistic. Freeze a finalist and evaluate with fresh runs and untouched representative cases; reserve confirmatory evidence for the decision rather than iterative tuning. A failed confirmation becomes a recorded rejection/inconclusive result, not a renamed development success. If confirmation drives a revision, plan new independent confirmation and account for the additional search.

Predeclare objectives, tolerances and aggregation. Multiple metrics/slices and many candidates increase opportunities for false wins; use simultaneous intervals or another justified design, keep search/confirmation separate and avoid post-hoc metric selection. Confidence intervals quantify uncertainty conditional on the experiment, not the probability a hypothesis is true. Tight intervals cannot rescue bias, invalid oracles, drift or an unrepresentative workload.
