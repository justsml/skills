# Choose instruments by question

Official upstream entry points checked 2026-10-07. Verify commands and APIs against the **installed** versions. Tools below are optional, not dependencies to install indiscriminately. Use supported local/browser tooling already available; in a managed environment, honor its preferred automation surface. If a browser session cannot export a needed profile, report that gap and add a project harness using authorized tooling rather than claiming a trace was captured.

## Browser rendering and interaction

Read [web performance](web-performance.md) for browser access/fallbacks, frame budgets, renderer verification, visual/input/navigation checks and targeted load/coverage/delivery analysis. Production build behavior can differ substantially from development. [CDP](https://chromedevtools.github.io/devtools-protocol/) exposes several distinct instruments; use their actual semantics below.

`Performance.getMetrics` exposes cumulative metrics; compute phase deltas and preserve units. Input automation time is not Interaction to Next Paint; use actual browser UX instrumentation for INP/LCP claims. CPU emulation slows CPU execution, not GPU throughput or an entire phone. Cache-disabled networking does not automatically disable service workers or application caches.

For network emulation, current protocol exposes `Network.emulateNetworkConditionsByRule` and `Network.overrideNetworkState`; the legacy `Network.emulateNetworkConditions` is deprecated. These newer APIs may be experimental/version-specific. Match the pinned protocol and verify effective conditions; fail setup if a requested setting is unsupported rather than silently timing a different network. Throughput units are bytes/second; latency is milliseconds.

`Profiler` captures sampled JavaScript CPU stacks. For raster, decode, compositor, GPU and main-thread relationships, collect `Tracing` events covering the slow phase. Select relevant supported categories, bound duration/buffer, wait for trace completion and preserve the entire artifact. A quiet JS profile does not establish a cheap rendering path. [Perfetto](https://perfetto.dev/docs/analysis/trace-processor) can query repeated captures; inspect event names, thread identities, inclusive/exclusive durations, overlap and dropped events before summing them.

Diagnose with tracing, decide with it off. Trace-guided hypotheses do not justify blanket virtualization, layer promotion, memoization or visual removal; the web playbook's product/visual/input gates still apply.

## CPU and runtime

| Question | Instrument | Interpretation boundary |
|---|---|---|
| Did a command's useful work speed up? | [hyperfine](https://github.com/sharkdp/hyperfine), project timing harness | JSON export/repeats help; default multi-command runs are not a randomized paired trial. Explicit orchestration/reset is needed for confirmation. |
| Where is native CPU spent? | [samply](https://github.com/mstange/samply), Linux [perf](https://perfwiki.github.io/main/tutorial/) | Optimized builds with symbols; sample coverage and unwinding quality matter. CPU samples omit waiting. |
| Where does Node execute/allocate? | [`--cpu-prof`](https://nodejs.org/api/cli.html#--cpu-prof), runtime allocation/GC instrumentation | Preserve profile and runtime identity. Linux [perf integration](https://nodejs.org/en/learn/diagnostics/poor-performance/using-linux-perf) is needed to interpret JIT code. |
| Where does Python CPU go? | [py-spy](https://github.com/benfred/py-spy), supported native profiler | Distinguish Python, native extension and subprocess coverage. Attaching may require OS permission. |

Example diagnostics, adapted to the installed tool and exact approved workload:

```text
hyperfine --warmup 3 --runs 10 --export-json timings.json './command fixture'
samply record ./command fixture
perf record -F 99 --call-graph dwarf -- ./command fixture
node --cpu-prof app.mjs
```

These examples are not a universal repeat count or full correctness harness. Profile optimized code with symbols and record sampling overhead. Inspect allocations, GC pauses, RSS and retained growth when memory churn may mediate latency; do not infer a leak from RSS alone or an improvement from fewer collections if retained memory increases.

## Waiting, contention and I/O

When wall time is high but CPU is low, inspect scheduler/lock waits, I/O, network and downstream services. Linux [sysstat](https://github.com/sysstat/sysstat) supplies `pidstat` and `iostat`; [strace](https://strace.io/) observes syscalls; [BCC](https://github.com/iovisor/bcc) supplies off-CPU and I/O latency tools where permitted.

```text
pidstat -u -r -d -w -p WORKLOAD_PID 1 10
iostat -xz -y 1 10
strace -f -c -o syscall-summary.txt ./command fixture
strace -f -tt -T -e trace=%file,read,futex -o syscall-timing.txt ./command fixture
```

Syscall summaries, per-call wall times and CPU/off-CPU samples answer different questions. Repeated file metadata calls suggest wasted fanout; lock waits suggest contention, but neither identifies the owner without further evidence. Network waiting needs a request/queue/service timeline and downstream measurements. Use ltrace only for a specific supported library-call question; dynamic/linking coverage is limited. Tracers perturb execution and may expose paths or input data; capture only authorized workload artifacts and remeasure without them.

Do not run Linux-only tools on macOS because their names are familiar. Use samply or Instruments on macOS and native Windows tools where appropriate; diagnose Linux behavior on the actual authorized Linux worker. Privilege failure is an instrument limitation: do not loosen global perf/eBPF/ptrace protections as a routine workaround.

## GPU: timeline before kernels

Coarse utilization/memory from [nvidia-smi](https://docs.nvidia.com/deploy/nvidia-smi/index.html) identifies gross starvation or pressure, not efficient throughput; interval sampling misses short stalls. [Nsight Systems](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) aligns CPU, transfers, launches, synchronization and device work:

```text
nsys profile --trace=cuda,nvtx --sample=none --cpuctxsw=none -o workload ./cuda-app
nsys stats workload.nsys-rep
```

If the device waits for tokenization, reads, transfers, batching or launch overhead, kernel tuning is premature. Once a kernel is demonstrated to limit the outcome, use [Nsight Compute](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html); counter collection/replay changes execution and is diagnostic evidence, not end-to-end latency. Apple [Metal tools](https://developer.apple.com/metal/tools/) and AMD [ROCm profilers](https://rocm.docs.amd.com/projects/rocprofiler-sdk/en/latest/) answer corresponding hardware questions. Confirm permissions, counter availability and artifact capture.

## Read the map correctly

In a [flame graph](https://www.brendangregg.com/flamegraphs.html), width represents sample mass; horizontal position is not elapsed time. A timeline/flame chart preserves order. Name self versus inclusive cost and check missing/unresolved stacks. A broad serializer frame may be caused by too many calls or bytes, not a slow serialization implementation. Sum overlapping activity carefully; distinguish a bottleneck on the critical path from expensive background work. Preserve original profiles, not only screenshots or agent summaries.
