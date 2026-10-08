# Project configuration and setup

The installed skill is portable; project policy and account/run state are not. Pass an absolute `--project` to the helper resolved relative to this installed skill. Equivalent `scripts/remote_compute.mjs` (Node 20+) and `scripts/remote_compute.py` (Python 3.10+) implement the same JSON schema, flags and exit codes with no packages or network access. `scripts/remote_compute.sh` requires Bash 3.2+ and selects compatible Node first, then Python; it is not standalone Bash arithmetic. Probe availability/version before selection, record the interpreter, and do not install a runtime just for this optional helper. Fall back only when a runtime is absent/incompatible, never when the chosen helper rejects input.

```text
node <skill-directory>/scripts/remote_compute.mjs setup --project /absolute/workspace
bash <skill-directory>/scripts/remote_compute.sh status --project /absolute/workspace
python3 <skill-directory>/scripts/remote_compute.py setup --project /absolute/workspace
python3 <skill-directory>/scripts/remote_compute.py status --project /absolute/workspace
python3 <skill-directory>/scripts/remote_compute.py status --project /absolute/workspace --run RUN_ID
python3 <skill-directory>/scripts/remote_compute.py estimate --rate-low 0.50 --rate-high 0.80 --hours-low 1 --hours-high 5 --fixed 0.20
```

`setup` creates missing files exclusively, preserving existing files:

| Location | Purpose |
|---|---|
| `.remote-compute/config.json` | Non-secret project policy, provider aliases, constraints, authorization record |
| `.remote-compute/.gitignore` | Excludes operational state and secrets; policy may be committed after reviewing account metadata |
| `.remote-compute/secrets.env.example` | Empty key names for the chosen provider; never real values |
| `.remote-compute/state/snapshot.json` | Saved status, resource and usage observations; initially unknown |
| `.remote-compute/state/runs/<run-id>/` | Agent-created ownership manifests, queue checkpoints, accounting events, artifact and cleanup receipts |

The helper creates no cloud accounts, credentials, billable resources or watchdog. It initializes a **disabled** spending policy. It does not load secret files. Preserve owner-only permissions for operational files (or equivalent Windows ACLs). Verify ignore rules before adding credentials; never copy an existing secrets file into an example. Keep secrets in a password manager/provider CLI credential store, process environment, or project-ignored `secrets.env`. Exclude them explicitly from source uploads and container build contexts; gitignore alone does not filter rsync/Docker.

## Policy fields (version 1)

`project_id` must be stable across threads and unique within a shared account. `currency` is USD for helper calculations; retain native currencies in provider records and document timestamped FX conversion before combining them.

- `budget.hourly_usd`, `rolling_24h_usd`, `run_usd`: aggregate ceilings, not per-worker allowances. `cleanup_reserve_usd` is part of the run ceiling, not extra permission. Null means unspecified, zero permits no spend, invalid/negative/non-finite values are errors. Require a bounded total/deadline and a conservatively priced plan before renting. Project/account-wide limits may impose additional ceilings.
- `authorization`: `paid_compute` defaults false; `source`, `scope`, `expires_at` record an actual user decision covering providers, workload, ceilings, duration, cleanup and any standing permission. Filling in numbers alone is not authorization. A run manifest records effective policy and prompt overrides. Do not migrate another project's approvals.
- `constraints`: `regions`, `data_residency`, `allowed_data`, `max_workers`, `max_runtime_hours`, `spot_allowed` and `gpu` requirements. Unknown fields may hold project-specific constraints, but adapters must document how they enforce them. Empty regions means unspecified, not verified worldwide approval.
- `providers`: unique `alias`, provider `kind`, selected `account_ref`/project/profile, `credential_env` names only, allowed regions and optional provider allocation. Use multiple aliases for multiple accounts of one provider. An allocation can tighten aggregate limits but never multiply them. Reuse known configured SSH routes with kind `ssh`; record owner and preserve-host policy.
- `monitoring`: checkpoint interval and stale-observation threshold. A real supervisor/expiry enforces limits; status calculations do not.

If integrating an existing `.env.remote-hosts`, map `DEFAULT_REMOTE_HOURLY_SPENDING_LIMIT` and `DEFAULT_REMOTE_DAILY_SPENDING_LIMIT` to hourly and rolling-24h USD ceilings. Parse only declared fields as data; honor explicitly configured process overrides and current prompt decisions. Do not treat unrelated `.env` files or inherited provider credentials as spending/transfer permission. Keep one canonical policy and record the mapping.

## Interactive onboarding

1. Inspect current project policy and configured provider names without printing secrets. Ask workload goal and important constraints that are still missing.
2. Compare two or three suitable products with fresh official prices and explain billing in plain language. Consider setup effort, transfer overhead, interruptions and data location alongside price.
3. Scaffold policy and a minimal provider entry. Guide the user to the provider console for signup, billing and a restricted token. Tell them the variable name and secure storage location; never ask them to paste a key into chat.
4. Verify read-only identity, account/project, inventory, permissions, quota and available balance. Missing billing API becomes `dashboard-only` or `unknown`; do not create a paid host merely to test authentication.
5. Record the agreed authorization and constraints. Prepare a bounded bootstrap/job command and cleanup mechanism. Start a paid pilot only within that permission. If the user requested setup alone, finish with usable configuration and readiness gaps without renting.
