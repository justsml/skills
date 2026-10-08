# Auto-tune performance: source analysis and design

Analyzed [Give Your Agent a Profiler](https://danlevy.net/performance-tuning-with-an-agent/) on 2026-10-07. The web fetch tool could not open the URL, but direct HTTPS retrieval succeeded and the rendered page identified the article and its October 7 update. Also read the current local source at `/Users/dan/code/oss/dans-blog/src/content/posts/2026-10-05--performance-tuning-with-an-agent/index.mdx`. Historical notes guided discovery; current content was read rather than relying on draft-era memory.

## What the article establishes

Benchmarks measure outcomes; profiles locate expensive work. A workload oracle must prove completion and preserved behavior. Diagnostic tracing perturbs timing, so final outcome measurements should be unprofiled. A profile needs the right coverage: JavaScript CPU alone cannot explain off-thread raster/decode. Renderer and cache differences invalidate casual comparisons. Useful improvements can remove unnecessary work; familiar CSS optimizations can regress important interactions. Each candidate needs a hypothesis, preserved constraints, raw artifacts and workload-by-workload acceptance. The dated Emoji Brain results demonstrate this workflow rather than a universal optimization recipe or a fleet-wide causal estimate.

## What the skill adds

The entrypoint defines an autonomous bounded experiment loop with an explicit outcome contract, experiment budget, uncertainty and stop rule. Supporting references provide measurement design, layer-specific instruments, service/GPU/model workload semantics, project preference/search strategy and decision mechanics. The default includes minimal-baseline/clean-rebuild consideration and isolated ablation/add-back rather than treating the current implementation as inevitable.

The user's follow-up requirements are encoded: tuning parameter maps; load-bearing code/instruction analysis instead of code golf; coarse-to-fine instruments and explained tool/access setup; vertical versus horizontal/fleet choices; project-local preference and rerun persistence; and later escalation to structural or breaking alternatives when local gains stall. Requirement relaxations such as delayed counters or cache reuse are explicit semantic tradeoffs, not eligible wins under the original contract.

A further web-focused follow-up lives in the dedicated `references/web-performance.md`: low-level DevTools/CDP access and fallbacks; 60 FPS/higher-refresh pacing and blocking; actual headed/headless renderer verification; recordings/filmstrips/CLS; conventional keyboard and aggressive scroll stress; deep-link/modal/history/reload behavior; and conditional load audits, bundle/transfer/coverage/CSS and CDN investigation. Cross-platform reporting now explicitly separates checked, proved, suspected and unknown/blocked evidence with actions. Headed mode is not equated with guaranteed GPU rendering, and latency/geolocation or limited CSS coverage cannot support stronger routing/deletion claims.

Measurement extensions include offered-load accounting, queue/service distinctions, successful useful throughput, failure/tail censoring, asynchronous device timing, cold/warm compiler/model caches, quality/numerical gates, candidate-search bias and independent confirmation. These are engineering design choices added to the workflow, not claimed Emoji Brain evidence.

## Executable evidence component

`scripts/compare.mjs` and `scripts/compare.py` perform a narrow positive-metric paired block comparison. They share seeded bootstrap draws and JSON/exit-code contracts, with Bash dispatch for runtime selection. The comparator validates declared arm identities, valid work, order balance and hard gates; computes geometric paired effects and approximate Bonferroni-adjusted percentile bootstrap intervals; separates promising screening from confirmatory acceptance; and preserves no-gain/inconclusive decisions. It deliberately does not invent sample independence, verify source manifests, normalize arbitrary provider metrics, enforce production SLOs or execute workloads.

The comparison format is documented in `references/decisions.md`. Its numerical/bootstrap floors are input/precision bounds, not universal sample-size recommendations or guarantees. Unsupported designs—zero/error counts, censored distributions, unpaired fleets and correlated request-level samples—need another analysis. Confirmation freshness and full contract coverage still require agent/harness review.

## Documentation freshness

Checked official upstream sources for Chrome CDP, hyperfine, samply, Node perf, py-spy, perf, strace, BCC, Perfetto, NVIDIA Nsight, Apple Metal, ROCm, k6 load models and vLLM serving metrics. Relevant links and interpretation limits live in the references. Installed-version compatibility and permissions are verified at execution time; the skill does not install a mandatory profiler stack or change host-wide protections.

## Validation scope

Helper tests use synthetic experiments and exercise consequential decisions: confirmation versus screening, higher/lower objectives, guardrail regression, no-gain/noise, insufficient independent blocks, invalid workload/environment/tracing/order, correctness fail/unknown, nonpositive/non-finite/duplicate observations, adjusted intervals, reproducibility and CLI exit/JSON behavior. Routing/action fixtures cover the stated skill contract and user follow-ups. Fixture success is not a live agent decision-quality evaluation; no real application gain or cloud workload is claimed by this package change.

Passed 11 comparison-helper tests, all 53 offline contract fixtures, bundled reference/template resolution, skill/UI YAML parsing with Ruby's standard library, skill discovery and diff whitespace checks. The Python skill-creator validator's PyYAML dependency was unavailable in this environment; no dependency was installed just for metadata validation. Live agent routing and end-to-end application tuning were not run.

Web-playbook update: checked current official Chrome headless, DevTools MCP, Performance, Coverage, Network, Lighthouse, rendering/CLS/bfcache, Playwright/Puppeteer CDP and Resource Timing documentation. Added six contract fixtures for browser/visual/input/history/load behavior and renderer/CDN/coverage overclaims. All 59 offline fixtures, bundled links/report anchors and diff whitespace checks passed. These remain offline expected-behavior fixtures, not browser execution evidence.
