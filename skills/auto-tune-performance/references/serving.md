# Services, queues, GPU and model serving

## Latency and capacity are different objectives

Compare at matched offered load and workload mix. A closed-loop client waits for responses before making more requests, so slower service can reduce arrivals and conceal queue buildup. An open arrival model can expose overload but needs enough generator capacity and explicit accounting for scheduled, dropped and admitted work. Choose deliberately; see [k6's open/closed model guidance](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/). Verify the generator's actual rate, CPU/network headroom and completion counts rather than trusting requested concurrency.

Sweep several preplanned loads: below saturation, near the operating point and a bounded overload case if authorized. Separate client round trip, queue wait, service time and downstream dependencies. Count timeouts, errors, retries, rejection, cancellations and partial results. Do not calculate a tail only over fast successful requests while censoring slow failures. Keep successful-throughput and error-rate gates beside latency. Retrying adds offered work and cost; request accounting must make that visible.

Use the queueing relation `L = λW` only for a stable population with matching boundaries and long-run arrival/completion rates. It is a consistency check, not a universal latency predictor. Near saturation, a small service-time change can have a nonlinear tail impact. Amdahl's serial bound does not model that queue amplification. More threads, connections or replicas can increase contention, memory and downstream overload; identify the limit before raising concurrency.

Databases need representative distributions, plan/runtime evidence, lock/I/O behavior and transaction correctness. A cached/explain-only plan or one tiny fixture does not prove production performance. Verify actual rows/work, index write/space costs, migration impact and sustained resource use. Batch/vector/import workloads need per-valid-item throughput plus partial failure and checkpoint/durability behavior, not just wall-clock progress.

## GPU timing boundaries

Accelerator calls are asynchronous. CPU wall time around a launch can measure enqueue latency rather than completed work. Use supported device events or synchronization at declared timing boundaries, and record overlap/stream behavior; do not insert global synchronization throughout a supposedly representative throughput run. Framework and hardware profilers have different timing semantics. Warmup can include compilation, graph capture, autotuning and allocation; make cold and steady-state experiments explicit. Verify completed outputs and numerical tolerances on relevant shapes.

A tensor/kernel microbenchmark isolates a mechanism; it cannot establish service or training throughput. Measure end-to-end data loading, preprocessing, host/device copies, kernels, synchronization and output handling. Watch device memory headroom, OOMs, fragmentation, allocator behavior and scaling efficiency. Avoid trading more expensive hardware or reduced numerical/quality guarantees for a claimed code-only gain.

## LLM inference and agent workloads

Preserve exact model/weights, precision/quantization, runtime, context/output limits, sampling, tool behavior and quality requirements unless the user specifically authorizes a tradeoff. Changing the model or truncating responses is a different treatment. Freeze realistic input/output length distributions and count actual generated valid tokens, not configured maxima. Distinguish requested output budget from realized tokens.

Measure time to first token, inter-token latency/time per output token, end-to-end latency, successful request/token throughput, queue time, resource/cost per valid completion and quality gates. Define how each is aggregated. Speculative decoding, prefix caching, continuous batching and KV-cache management can shift benefits by input/output mix and arrival rate. Test cache-cold and realistic cache-hit cases separately; repeated identical prompts may only prove a cache shortcut. Keep tokenization/network/client overhead visible and avoid comparing different streams or omitted outputs.

[vLLM's serving benchmark](https://docs.vllm.ai/en/latest/cli/bench/serve/) is a possible instrument, not a mandatory dependency. Verify its installed flags, endpoint compatibility, request-rate model, dataset selection and metric definitions. Engine throughput, GPU utilization and client-visible latency are separate measurements. A quality/performance claim requires the existing task-quality oracle, especially after quantization or decoding changes. Do not tune on held-out quality cases or replace quality gates with model self-reports.

Agent workflows need useful-task completion and answer/tool correctness beside tokens/sec. Faster incomplete trajectories or skipped verification are failures. Separate provider delay, orchestration overhead, tool/worker queueing, retries and local work with spans; tracing health/counts alone do not prove complete telemetry. Avoid attributing all account spend to this benchmark. Record known actual/estimated/unknown API and infrastructure cost, failures and retry overhead.

## Rollout

Local load tests support the measured conditions. Fleet claims need representative hardware, traffic, tenancy and deployment evidence. If authorized, canary a frozen patch, watch all declared gates and costs, and roll back on breaches. Keep a stable comparison period and account for mix/rate changes; deployment dashboards can correlate a change without proving causality. Do not silently modify autoscaling, production caches, quotas or SLO thresholds to make a candidate pass.
