# Monitoring, accounting and forecasts

## Live status workflow

Read project policy and run manifests. Inventory **every configured provider alias** and authorized existing host. Query current read-only identity, resource state, billing/credits and workload signals using available official CLI/API/connector. A credential failure should not hide the other providers. Record verified, unknown, invalid-auth and dashboard-only coverage separately for inventory and billing, with source/timestamp/lag. Do not call a stale snapshot current.

Display account credits, current burn and estimated runway alongside project limits; credits are neither a budget nor guaranteed headroom for this job. Multiple projects may share an account. Warn when verified credit headroom is below remaining forecast plus reserve or when a configured low-balance threshold is crossed. With other account workloads or auto-topup, label runway conditional. Postpaid providers may have no meaningful prepaid balance.

Report recent account usage for an explicit time window, project usage for its owned resources, and current thread usage via a durable `thread_id -> run_id` mapping. If the harness exposes no stable thread ID, report run-scoped usage and say so. Never attribute all account spend or a balance delta to a thread. Shared resources require an explicit allocation method; unallocated cost stays unallocated.

## Normalized saved snapshot (version 1)

The bundled helper's `status` is **offline**. Use the portable timestamp form `YYYY-MM-DDTHH:mm:ss[.fraction]Z` or an explicit `±HH:mm` offset. The agent/provider adapter refreshes `.remote-compute/state/snapshot.json` atomically with owner-only permissions, then invokes it for consistent arithmetic. It reads only this allowlisted format, not credentials. Minimal example (illustrative rates, not a quote):

```json
{
  "version": 1,
  "observed_at": "2026-10-07T12:00:00Z",
  "coverage": "complete",
  "providers": [{
    "alias": "gpu-primary",
    "inventory_status": "verified",
    "billing_status": "dashboard-only",
    "balance_usd": null,
    "recent_usage_usd": null,
    "usage_window": null,
    "source": "authenticated provider inventory; console needed for billing"
  }],
  "resources": [{
    "id": "pod-123",
    "provider": "gpu-primary",
    "run_id": "import-001",
    "kind": "gpu-pod",
    "owned": true,
    "state": "running",
    "billing_ended": false,
    "rate_low_usd": 0.5,
    "rate_high_usd": 0.8,
    "rate_source": "whole allocation quote including disk",
    "active_jobs": 1,
    "pending_jobs": 10
  }],
  "runs": [{
    "id": "import-001",
    "thread_id": null,
    "measured_usd": 0.2,
    "estimated_usd": 0.3,
    "committed_usd": 0,
    "unknown_cost": false,
    "eta_hours_low": 1,
    "eta_hours_high": 5
  }]
}
```

`coverage` is `complete`, `partial` or `unknown` for this project's selected resource inventory and cost components. Complete does not mean account-wide billing coverage; record that independently per provider. Missing configured aliases, unknown rates, costs or stale observations prevent a complete forecast. `billing_ended: true` requires provider evidence, not a stopped state or lost SSH. Retain such resource rows and run accrual after deletion. `owned: false` rows remain observations and do not enter project forecasts; show their account impact separately where known. Unknown queue counts are null.

Run accrual fields are **non-overlapping totals** as of the snapshot: measured invoice/usage charges, inferred but not yet reconciled charges, and prepaid/non-cancellable commitments not included elsewhere. Replace an estimate when it becomes measured; don't add the same charge twice. Record unknown cost explicitly. ETA is remaining time from this observation. For rolling-24h enforcement, retain timestamped individual events and outstanding commitments in run records; lifetime sums in this snapshot are insufficient.

Never store secret values, raw env content or token-bearing URLs in snapshot fields. Each provider alias must match configuration; IDs and source fields are non-secret display metadata. The helper validates required accounting values, prints selected fields, and refuses malformed versions/duplicates.

## Forecast arithmetic and communication

For a stable fleet with low/high whole-allocation hourly rates `r_low`, `r_high`:

- Extra 1–5h: `r_low × 1` through `r_high × 5`, plus expected new variable/fixed charges.
- Unchanged fleet 24h: `r_low × 24` through `r_high × 24`. This is a scenario, not permission or an ETA.
- Remaining work: rate × remaining ETA range + incremental non-hourly charges.
- Forecast final: measured + unreconciled estimates + non-overlapping commitments + remaining work.
- Admission headroom: remaining aggregate budget minus cleanup reserve and outstanding commitments, checked against hourly, run and rolling-24h ceilings.

Use native billing granularity, minimum charges and monthly commitments in real quotes. Never amortize a mandatory monthly payment as if a one-hour job paid only one hour. Serverless jobs require observed allocated seconds, replica bounds and startup/warm-tail assumptions rather than the flat-fleet calculation. The helper calculates flat USD scenarios only; keep token, egress, tax, FX and other exclusions visible. Unknown totals remain null with known subtotals reported. Do not infer zero from missing telemetry or round a positive cost down to a zero claim.

At each checkpoint show: completed/failed/remaining jobs; active/ready/idle workers; CPU/RAM/GPU/VRAM and I/O where useful; bottleneck/pace; ETA range; measured/estimated/committed/unknown spend; aggregate rate; extra 1–5h and 24h costs; budget/deadline headroom; cleanup health. Confidence should rise only after a representative stable sample; failures, rate changes or stale signals widen the range and lower it. The helper labels current arithmetic as estimates and flags stale/incomplete observations; the agent supplies evidence-based confidence and recommendations. Budget warnings use unrounded calculations; displayed figures are rounded to six significant digits. Missing budget fields are errors (use explicit null for unspecified ceilings), and unknown project rates explicitly prevent assessing the hourly ceiling.

Default reporting cadence is ten minutes, with earlier startup/pilot updates and immediate updates on scale, error or cost changes. Respect project preferences. Routine billing checks need not be as frequent as job telemetry if usage data lags or API queries cost money.

## Enforceable cleanup

Status is not a watchdog. Before provisioning, use verified provider-native expiry that actually ends relevant charges or a durable independently supervised coordinator service with exact ownership, deadline, budgets and cleanup hooks. Verify heartbeat, supervisor identity and its effect on real admissions. If no mechanism is available, prepare it or stop before renting unattended capacity; a shell trap or timer on the rented worker alone is insufficient.

One shared provider account needs coordinated ownership and aggregate allocations across projects/threads. Do not run conflicting cleanup supervisors. Keep historical accrual through retries and replacements. Missing/stale monitoring closes new paid admissions; hard deadlines remain active. Drain queues before idle retirement and inspect useful work, including provider-waiting jobs; low GPU utilization alone does not establish idleness. Keep cleanup active until exact provider state verifies charge termination for every owned resource type.
