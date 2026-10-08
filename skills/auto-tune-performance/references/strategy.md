# Search strategy, project memory and structural alternatives

## Persist priorities and rerun the same exercise

Use the project's existing memory/config/performance record when available. Otherwise the reviewed `performance/<task>/plan.md` is the source of truth; a project-local index such as `performance/README.md` can identify the current recipe when there are multiple tasks. Store confirmed user preferences, not conjectures about personality. Keep global skill instructions free of project budgets, accounts and data. Sensitive artifacts stay in the project-approved protected store.

Record the objective hierarchy (for example, p95 UX before throughput, then cost), absolute targets, worthwhile effect, allowed degradations, forbidden tradeoffs, reliability/durability, freshness/consistency, data residency, maintenance/complexity appetite, time/spend bounds and any scoped standing authorization. Distinguish a session override from a new saved default. Ask before promoting an ambiguous one-off choice into a durable preference; an explicit “remember this for the project” is enough to save it. Retain the exact benchmark command/fixture/scenario/gates, artifact path and last reviewed revision/tool/environment identities.

On “check the app's performance again,” find the latest matching exercise and run it. Verify the command still applies, refresh build/source/environment/tool identities, and collect fresh baseline data. Keep old evidence as history; new measurements are a new run. If code/schema/workload changes invalidate the old harness, repair it and document why comparison changed. Ask only when several recent recipes fit equally well or the user's new goal changes the decision. Reuse valid setup knowledge, not stale throughput, capacity, budget or permissions.

At meaningful checkpoints, compare progress against time/spend and the user's priorities. If the user is frustrated or tradeoffs are undecided, ask something concrete: “Should I prioritize meeting the latency target, lowering cost, or preserving the current architecture?” State the measured consequence of each option. Continue safe independent diagnosis while waiting. Previously settled requirements remain in force until changed.

## Build a parameter map before a search

Only test knobs with a plausible causal path to the objective. Record current value, legal range/units, mechanism, expected gain, dependencies, cost/risk, constraints and reset method. Prefer coarse ranges to locate useful regimes, then refine near a demonstrated region. Do not brute-force a Cartesian grid when a bottleneck model can eliminate most combinations. Bound trials and preserve unsuccessful configurations.

| Layer | Candidate parameters / structural choices | Coupled constraints to measure |
|---|---|---|
| Work/data representation | algorithm, data structure, work eliminated, precomputation, indexing, compression, representation, allocations/copies | exact outputs, asymptotic behavior across sizes/skew, memory, update cost |
| Browser | render/decode work, asset format/animation activation, invalidation, scheduling, containment/virtualization boundaries, request/loading policy | scroll/focus/accessibility, visual requirements, renderer, network, decode/raster, memory |
| Runtime/CPU | batching, allocation lifetime, process/thread count, SIMD/vectorization, JIT/compiler flags, data locality | wall/CPU time, cache/branch behavior, contention, GC, cycles/instructions per useful operation |
| I/O/network/storage | chunk/buffer size, request fanout, pooling, round trips, queue depth, caching/indexes, transfer compression | tail latency, throughput, errors, memory, downstream pressure, durability, freshness |
| Service/fleet | queue/worker count, admission bounds, sharding, replication, locality, autoscaling/warm capacity | SLO at matched offered load, cost, startup, reliability, skew and backpressure |
| GPU/model | batch/concurrency, shapes, precision, kernel/fusion, transfers, streams, graph capture, KV/prefix cache, context limits | completed work, quality/numerical tolerance, per-device memory, queue/TTFT/tail, cold compilation |
| Prompt/agent | instruction necessity, examples/context, tool schemas, repeated checks, call graph, routing/caching | task completion, quality/safety/tool semantics, token/cost/latency; held-out quality cases remain untouched |

Fewer lines, instructions, tokens or cycles are proxies, not the objective. Instructions per cycle can rise while useful throughput falls; a compact prompt can omit the task. Optimization targets useful work under constraints. A low-maintenance clear solution can beat a marginally faster brittle one. Hardware-counter attribution needs the right workload and enough signal; do not turn IPC or code golf into a universal goal.

## Minimal starting point and add-back experiments

Always consider a minimal faithful implementation or a clean experimental arm. State whether the proposed arm can preserve the task and what it would teach. An obviously inapplicable or disproportionately expensive rewrite can be declined with a reason; the default consideration still happens. Do not assume the current architecture is the best baseline just because it exists.

Map dependencies and rank likely load-bearing components from contracts, call sites and observed work—not intuition alone. Separate required outcomes from the current mechanism. Clone/isolate the experiment and retain a recoverable baseline. For prompt tuning, start with the indispensable task/constraints and restore instructions/examples by demonstrated need on development cases. For code, strip incidental layers/features in the experimental arm while preserving required outputs and interfaces. For compute, isolate the essential algorithm/data path. Never remove correctness checks from the acceptance harness.

Use ablation to ask what removal changes and add-back to ask what restores necessary behavior. Check semantic/task quality, feature coverage and performance after each step. Prune clearly non-load-bearing overhead; restore dependencies before interpreting a failed component in isolation. Include interaction/group ablations when components cooperate; a greedy single-line test does not prove global necessity or sufficiency. Attribute results to the tested mechanism/bundle, not to an arbitrary line count. Confirm the finalist on fresh cases/runs and real workloads after iterative search.

Removing required visuals, safety checks, durability or functionality yields a **relaxed-contract ceiling experiment**, not an eligible winner. It can quantify the price of a requirement for a later discussion. Label it, keep it isolated and never ship it without a changed user decision and new acceptance contract. The fastest empty implementation is not a baseline for useful work.

## Vertical versus horizontal scaling

Profile and model first. A serial critical path, lock, single backend quota or saturated network does not improve just because more workers exist. Vertical sizing may fit a working set or avoid OOM; horizontal partitioning can accelerate independent builds, imports, evaluations or jobs when results can be combined safely. Define partitions, atomic claims/idempotence, skew, transfer/startup overhead, shared dependency limits, durable checkpoints, retry budgets and output reconciliation.

Compare end-to-end completion time, useful throughput, total/hourly cost, reliability and operational effort. More cheap workers can cost more after startup, transfer, failures and idle tails; a larger GPU can solve memory capacity without improving every latency. Ephemeral fleets need bounded lifecycle and artifact persistence; durable services need reliability/availability semantics rather than a short-lived benchmark fleet.

When offloading is plausible, explain a bounded pilot and cost estimate. If available, use `remote-compute` for project configuration, authorized providers, aggregate limits, fleet ownership, monitoring and verified retirement. Otherwise use the project's equivalent workflow or prepare a plan; do not assume the optional skill is installed or that possession of a provider key permits spending. Scaling is a named architectural/capacity treatment, not a claimed code-only speedup.

## Escalate to structural alternatives when evidence warrants it

Do not lead with a breaking rewrite before understanding the workload. Trigger an architectural discussion when local hypotheses fail to produce worthwhile gains, measured bounds make the target unreachable, the budget is being consumed without progress, or a required semantic constraint dominates the critical path. Stop low-value retries and explain the bottleneck and the best confirmed result.

Present two or three concrete choices: preserve requirements and accept the measured ceiling; change capacity/architecture; or explicitly relax a costly requirement. For each give predicted improvement range and confidence, evidence/falsifying pilot, compatibility and migration impact, quality/reliability/freshness/security consequences, cost and rollback. Estimate honestly when no pilot exists. Suggest breaking alternatives when relevant but implement them only when the user chooses or existing authorization clearly covers that change.

Examples: a counter need not be transactionally exact on every request if five-minute staleness is acceptable; an existing suitable cache might serve aggregates with explicit TTL/invalidation and failure fallback. Cross-region chatty calls might become batches or locally computed snapshots. Full synchronous work might become a queued job with progress/status and durable retry. A read-heavy path might use a materialized view; repeated computation might move to ingestion. Each changes semantics or failure modes—quantify stale/incorrect states, cache stampedes, write/update cost and recovery rather than treating “use a cache” as an answer.

Once a tradeoff is approved, version the new contract and store the decision in project preferences. Rebaseline both arms where workload/semantics changed; do not compare different amounts of useful work as a code-only win. Keep original-contract measurements so the user can assess the price of the relaxed requirement.
