---
name: remote-compute
description: Set up, inspect, and operate remote CPU or GPU compute with project-specific budgets and cost forecasts. Use for remote workers, large builds, batch evaluations, ingestion or imports, private model hosting, provider price comparisons, or host balance and usage checks; offer remote capacity when a substantial workload is constrained locally.
---

# Remote compute

Help people choose and use remote capacity, from a first hosted worker to a bounded fleet. Support plain-language requests and these modes: `$remote-compute setup`, `$remote-compute status`, and `$remote-compute run <workload>`. These are skill modes, not shell commands. The bundled Node/Python helpers (with Bash runtime dispatchers) implements local `setup`, `status`, and `estimate`; provider operations use the selected provider's current official CLI/API or available connector.

## Choose the mode and project

- **Setup:** discover existing hosts/configuration, compare suitable providers, scaffold project policy and verify access. Read [project configuration](references/project-config.md) and the selected entries in [providers](references/providers.md).
- **Status:** read-only inventory of all configured providers, balances, recent usage, owned resources, and current run/thread spend. Read [monitoring and accounting](references/monitoring.md). Refresh with provider queries before claiming live status; the helper only reports saved observations.
- **Run:** plan, provision or reuse, supervise and retire remote workers. Read [execution](references/execution.md), configuration and monitoring. Use provider references only for relevant candidates.

Choose an installed Node 20+ or Python 3.10+ runtime, or use the Bash 3.2+ dispatcher described in project configuration. Record the interpreter; fall back only for an absent/incompatible runtime, never for an input validation failure.

Resolve the user's target project first; do not write into the global skill installation or infer the project from the skill directory. Read project instructions and existing operational configuration. Store policy in that project and operational records outside tracked source. Reuse existing project formats by documenting a mapping instead of making competing sources of truth. With no project/repository, use an explicit user-selected workspace. A global installation changes discovery, never budget scope.

For an unfamiliar user or an ambiguous long job, briefly offer: “This may take several hours locally. Would you like me to compare remote workers or help configure them?” Continue useful local work while awaiting the answer. Diagnose the bottleneck first; a GPU does not accelerate an ordinary CPU build. Honor a decline and do not repeatedly suggest offloading. Explicit remote requests can proceed through preparation without another opt-in.

## Establish a concrete plan

Identify input size, parallelizable units, platform, CPU/RAM/disk or GPU/VRAM needs, runtime, data sensitivity/residency, transfer size, output destination and success signal. Use a representative local timing or bounded pilot for the ETA. Ask only for consequential missing constraints; give newcomers a small set of choices and a recommended low-commitment starting point.

Prefer an adequate existing host or small worker before a fleet. Compare whole-allocation cost including startup, downloads, failed attempts, idle/warm workers, storage, IPs, egress, API/model calls and cleanup. Verify current official prices, billing units, selected region/offer, quota and capacity; dated catalogs are shortlists. Distinguish VM, container Pod, managed inference endpoint, sandbox and CI runner capabilities. Do not promise SSH, privileged containers or GPU support from a price listing.

Before paid creation, present expected duration/cost range, aggregate hourly burn, an extra 1–5 hours, and an unchanged-fleet 24-hour scenario. State uncertainty and the authorization cap separately. Resolve missing budget/deadline or data-transfer permission with one focused question. Reuse scoped standing authorization; a key's presence, a numeric ceiling alone, or installing this skill grants none. Record an explicit prompt override without silently changing saved defaults. No blanket approval flow is needed for read-only checks or reversible local preparation.

## Carry the work through

Keep lifecycle credentials on the coordinator. Transfer only approved workload inputs and narrowly scoped secrets; never copy credential directories, personal SSH private keys, agent sockets or whole environment files. Parse configured env files as data, never source them. Use authenticated private access or an SSH tunnel for model services; verify the client can actually reach the chosen route.

Establish exact ownership, deadline and independent cleanup before paid admission. Verify cleanup supervision and one representative job under the real environment. Scale concurrency from measured useful throughput and resource pressure. Shared faults pause affected admissions; independent healthy workers can continue within the aggregate budget. Preserve every attempt and partial artifacts; reconnect and inspect a job before resubmitting it.

Report useful work, ETA, spend and forecasts at startup, after the pilot, at project checkpoints (default every ten minutes), and on material rate, capacity, error or budget changes. When forecasts exceed permission, stop new admissions and drain or clean up within the reserve; request an extension only if needed to continue. Do not rely on the conversation staying open to enforce deadlines.

Sync outputs and worker fixes to the project before teardown. Remove only exact owned resources, preserve borrowed hosts and unrelated services, and verify the provider state that ends each charge. Report any continuing storage/endpoint/IP charges or unverified deletion promptly. Finish with artifacts, validation, actual/estimated/unknown spend, cleanup receipts and unresolved items.

For private model serving, read [model hosting](references/model-hosting.md). Confirm the exact available model and runtime rather than guessing from a spoken name such as “Ollama,” “Gemma,” or “Gemini.”
