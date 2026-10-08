# Remote compute extraction

Reviewed local ExploitHunter checkout `/Users/dan/code/oss/agent-security` at `098eeaa66b10ef69cf17704716b763de16a756f3` on 2026-10-07. This review concerns general compute orchestration; no provider credentials were read, no accounts were queried and no resources were rented.

## Source review and disposition

| Source in ExploitHunter | Reusable behavior | Shared package adaptation |
|---|---|---|
| `.agents/skills/run-ephemeral-hosts/SKILL.md` | Frozen workload, isolated jobs, per-project configured budgets, measured admission, attempt/evidence retention | Generic build/eval/import queue, durable run IDs, project-owned policy, scoped fault recovery |
| `.agents/skills/manage-remote-resources/SKILL.md` | Exact ownership, pre-creation inventory, independent cleanup, ambiguous-create reconciliation, retained spend, verified teardown | Provider-neutral lifecycle and thin adapter contract; preserve borrowed hosts |
| `.agents/skills/run-remote-builds/SKILL.md` | Exact source/dirty snapshot, actual non-interactive environment, isolated workspaces, worker fixes returned to coordinator | Generic reproducibility and artifact/source synchronization |
| `.agents/skills/manage-remote-resources/references/{cpu,gpu}-provider-cost-snapshot.md` | Whole allocation versus components, hardware/runtime boundaries, short-job commitment costs, configured-access distinction | Official discovery links and current-quote procedure; no stale prices or private access inventory copied |
| `.agents/skills/run-ephemeral-hosts/references/gpu-inference.md` | Weight + KV memory, real client/context preflight, compatible runtime, measured concurrency | Private model workflow; remove specific models, host incidents and universal context/output floors |
| `docs/remote-watchdog.md` and `src/operations/remote-host-observation.ts` | Owner-partitioned supervision, fresh workload signals, drain/inspect before idle reclamation, history preserved | Normalized observation/usage contract and supervisor integration requirements |
| `AGENTS.md` and remote skill credential references | Lifecycle authority on coordinator, workload-specific secret handling, credential disposition | General least-privilege contract; project-local standing approvals are not copied |

The watchdog documentation explicitly says its destructive adapter handles Vast instances, not every provider/resource type. Copying it would create misleading universal cleanup coverage and carry the application's Node/schema/runtime dependencies. The package instead includes a dependency-free Node/Python scaffolder with Bash runtime dispatch and saved-status/forecast helper; live query, provisioning and supervision mechanics remain selected-provider operations under the skill's documented contract. A future automation adapter should be added only with real lifecycle coverage and provider evidence.

## Public package shape

One implicitly discoverable `remote-compute` skill exposes setup/status/run modes. Node and Python implement equivalent setup/status/estimate commands; Bash dispatches to an installed compatible runtime with explicit project selection. Project config and protected operational records live under `.remote-compute/`; global installs retain no user budgets or accounts. Existing project config may be mapped rather than replaced. Setup defaults to no paid authorization and preserves existing files.

Status distinguishes provider inventory from billing coverage, account credits from project budget, current thread/run attribution from account usage, measured from inferred/committed charges, retired-host accrual from current rates, and unknowns from zero. Forecasts expose extra 1–5h and unchanged-fleet 24h scenarios; no status command claims to enforce limits.

Official provider authentication, billing, pricing and model documentation was checked during extraction; the linked entry points are in the skill's provider/model references. Prices and API versions remain live verification tasks. No universal SDK-native environment-variable claim is made for project binding aliases.

## Verification boundaries

Offline helper tests exercise preservation, arithmetic, retired/stopped billing, zero/invalid budgets, cross-run aggregate ceilings, borrowed-host exclusion, stale/missing observations and ownership validation. Routing/action cases are included in the existing fixture harness and explicitly remain hand-authored expectations, not evidence of agent behavior. No paid/live model routing or real cloud lifecycle test is implied.

Validation passed: nine helper tests, CLI setup/rerun/status and estimate smoke checks, secret/state git-ignore verification, bundled reference resolution, 41 offline fixture cases, and diff whitespace checks. The skill-creator Python validator could not run because PyYAML was unavailable; skill and UI YAML were parsed successfully with Ruby's standard YAML library instead. No dependency was installed to perform validation.
