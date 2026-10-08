#!/usr/bin/env python3
"""Local scaffolding and flat-fleet forecasts. No network, secrets, or cloud mutations."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
import re
from pathlib import Path
import sys


def number(value, label, nullable=False):
    if nullable and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return value


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        raise ValueError("timestamp must be an ISO 8601 string with timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def load(path):
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or type(data.get("version")) is not int or data.get("version") != 1:
        raise ValueError(f"{path.name}: expected object with version 1")
    return data


def unique_rows(rows, field, label):
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be an array")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(field), str) or not row[field]:
            raise ValueError(f"{label}: missing {field}")
        if row[field] in seen:
            raise ValueError(f"{label}: duplicate {field}")
        seen.add(row[field])
    return seen


def rounded(value):
    return None if value is None else float(f"{value:.6g}")


def scenarios(low, high, fixed=0):
    if low is None or high is None:
        return {"extra_1_to_5h_usd": None, "unchanged_24h_usd": None}
    return {"extra_1_to_5h_usd": [rounded(low + fixed), rounded(5 * high + fixed)],
            "unchanged_24h_usd": [rounded(24 * low + fixed), rounded(24 * high + fixed)]}


def create_missing(path, content):
    # O_EXCL prevents replacing existing files or following their symlinks.
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as handle:
        handle.write(content)
    return True


def setup(project):
    if not project.is_dir():
        raise ValueError("--project must identify an existing workspace directory")
    base = project / ".remote-compute"
    # Refuse redirected policy/state paths, including when rerun.
    for directory in [base, base / "state"]:
        if directory.is_symlink():
            raise ValueError("configuration/state directory must not be a symlink")
        directory.mkdir(mode=0o700, exist_ok=True)
    config = {
        "version": 1, "project_id": project.name, "currency": "USD",
        "budget": {"hourly_usd": None, "rolling_24h_usd": None, "run_usd": None, "cleanup_reserve_usd": 0},
        "authorization": {"paid_compute": False, "source": None, "scope": None, "expires_at": None},
        "constraints": {"regions": [], "data_residency": None, "allowed_data": [], "max_workers": 1,
                        "max_runtime_hours": None, "spot_allowed": False, "gpu": None},
        "providers": [], "monitoring": {"checkpoint_seconds": 600, "stale_after_seconds": 600}
    }
    snapshot = {"version": 1, "observed_at": None, "coverage": "unknown", "providers": [], "resources": [], "runs": []}
    files = {
        base / "config.json": json.dumps(config, indent=2) + "\n",
        base / ".gitignore": "state/\nsecrets.env\nsecrets.env.*\n!secrets.env.example\n*.key\n*.pem\n",
        base / "secrets.env.example": "# Names only. Add only the selected provider's bindings.\n# RUNPOD_API_KEY=\n# VAST_API_KEY=\n# LAMBDA_API_KEY=\n",
        base / "state/snapshot.json": json.dumps(snapshot, indent=2) + "\n"
    }
    created, preserved = [], []
    for path, content in files.items():
        (created if create_missing(path, content) else preserved).append(str(path))
    return {"created": created, "preserved": preserved,
            "next": "Choose providers, constraints and budget; record authorization and verify access/cleanup before renting."}


def status(project, run_id=None, now=None):
    base = project / ".remote-compute"
    config, snapshot = load(base / "config.json"), load(base / "state/snapshot.json")
    if config.get("currency") != "USD":
        raise ValueError("helper supports USD only; convert native currency explicitly")
    budget = config["budget"]
    for key in ["hourly_usd", "rolling_24h_usd", "run_usd", "cleanup_reserve_usd"]:
        if key not in budget:
            raise ValueError(f"missing budget.{key}; use explicit null for unspecified ceilings")
        number(budget.get(key), f"budget.{key}", nullable=key != "cleanup_reserve_usd")
    aliases = unique_rows(config["providers"], "alias", "config.providers")
    observed = unique_rows(snapshot["providers"], "alias", "snapshot.providers")
    if observed - aliases:
        raise ValueError("snapshot contains an unconfigured provider alias")
    unique_rows(snapshot["runs"], "id", "runs")
    # Resource IDs are unique within a provider account, not across providers.
    resource_keys = set()
    for resource in snapshot["resources"]:
        key = (resource.get("provider"), resource.get("id"))
        if not all(isinstance(v, str) and v for v in key) or key[0] not in aliases or key in resource_keys:
            raise ValueError("resource requires a configured provider and unique provider/id pair")
        resource_keys.add(key)
        for field in ["owned", "billing_ended"]:
            if not isinstance(resource.get(field), bool):
                raise ValueError(f"resource.{field} must be boolean")
        low = number(resource.get("rate_low_usd"), "rate_low_usd", nullable=True)
        high = number(resource.get("rate_high_usd"), "rate_high_usd", nullable=True)
        if low is not None and high is not None and low > high:
            raise ValueError("rate_low_usd exceeds rate_high_usd")
        for field in ["active_jobs", "pending_jobs"]:
            count = number(resource.get(field), field, nullable=True)
            if count is not None and int(count) != count:
                raise ValueError(f"{field} must be an integer or null")
    now = now or datetime.now(timezone.utc)
    threshold = number(config["monitoring"]["stale_after_seconds"], "stale_after_seconds")
    age = None if snapshot.get("observed_at") is None else (now - instant(snapshot["observed_at"])).total_seconds()
    if age is not None and age < -60:
        raise ValueError("snapshot timestamp is in the future")
    stale = age is None or age > threshold
    reasons = []
    if stale:
        reasons.append("missing or stale observations")
    if aliases - observed:
        reasons.append("configured providers missing from snapshot: " + ", ".join(sorted(aliases - observed)))
    if snapshot.get("coverage") not in ["complete", "partial", "unknown"]:
        raise ValueError("invalid coverage")
    if snapshot["coverage"] != "complete":
        reasons.append("inventory/cost coverage is incomplete")
    providers = []
    for provider in snapshot["providers"]:
        for field in ["inventory_status", "billing_status"]:
            if provider.get(field) not in ["verified", "unknown", "invalid-auth", "dashboard-only"]:
                raise ValueError(f"invalid provider.{field}")
        for field in ["balance_usd", "recent_usage_usd"]:
            # Provider balance may be negative; don't normalize debt to zero.
            value = provider.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise ValueError(f"{field} must be finite or null")
        if provider["inventory_status"] != "verified":
            reasons.append(f"inventory not verified for {provider['alias']}")
        providers.append({field: provider.get(field) for field in ["alias", "inventory_status", "billing_status", "balance_usd", "recent_usage_usd", "usage_window", "source"]})
    runs = snapshot["runs"]
    known_run_ids = {run["id"] for run in runs}
    for resource in snapshot["resources"]:
        if resource["owned"] and resource.get("run_id") not in known_run_ids:
            raise ValueError("owned resource requires a recorded run_id")
    if run_id is not None and run_id not in known_run_ids:
        raise ValueError("requested run is not recorded")
    for run in runs:
        for field in ["measured_usd", "estimated_usd", "committed_usd", "eta_hours_low", "eta_hours_high"]:
            number(run.get(field), f"run.{field}", nullable=field.startswith("eta_"))
        if not isinstance(run.get("unknown_cost"), bool):
            raise ValueError("run.unknown_cost must be boolean")
        if run.get("eta_hours_low") is not None and run.get("eta_hours_high") is not None and run["eta_hours_low"] > run["eta_hours_high"]:
            raise ValueError("ETA low exceeds ETA high")
    selected = [run for run in runs if run_id is None or run["id"] == run_id]
    resources = [r for r in snapshot["resources"] if r["owned"] and (run_id is None or r["run_id"] == run_id)]
    live = [r for r in resources if not r["billing_ended"]]
    if any(r.get("rate_low_usd") is None or r.get("rate_high_usd") is None for r in live):
        reasons.append("billable resources have unknown rates")
    if any(run["unknown_cost"] for run in selected):
        reasons.append("selected runs have unknown costs")
    low = sum(r.get("rate_low_usd") or 0 for r in live)
    high = sum(r.get("rate_high_usd") or 0 for r in live)
    complete = not reasons
    totals = {field: rounded(sum(run[field] for run in selected)) for field in ["measured_usd", "estimated_usd", "committed_usd"]}
    forecasts = []
    final_high_raw = {}
    for run in selected:
        run_live = [r for r in live if r["run_id"] == run["id"]]
        final = None
        if complete and run.get("eta_hours_low") is not None and run.get("eta_hours_high") is not None:
            accrued = sum(run[field] for field in totals)
            final_high_raw[run["id"]] = accrued + sum(r["rate_high_usd"] for r in run_live) * run["eta_hours_high"]
            final = [rounded(accrued + sum(r["rate_low_usd"] for r in run_live) * run["eta_hours_low"]),
                     rounded(accrued + sum(r["rate_high_usd"] for r in run_live) * run["eta_hours_high"])]
        forecasts.append({"id": run["id"], "thread_id": run.get("thread_id"), "final_flat_fleet_usd": final})
    warnings = []
    # Hourly project ceiling is always compared to all project-owned live resources.
    project_live = [r for r in snapshot["resources"] if r["owned"] and not r["billing_ended"]]
    project_high = None if any(r.get("rate_high_usd") is None for r in project_live) else sum(r["rate_high_usd"] for r in project_live)
    if budget["hourly_usd"] is not None and project_high is None:
        warnings.append("hourly ceiling cannot be assessed: project rates are unknown")
    if budget["hourly_usd"] is not None and project_high is not None and project_high > budget["hourly_usd"]:
        warnings.append("aggregate project rate exceeds hourly ceiling")
    for forecast in forecasts:
        if budget["run_usd"] is not None and forecast["final_flat_fleet_usd"] is not None and final_high_raw[forecast["id"]] + budget["cleanup_reserve_usd"] > budget["run_usd"]:
            warnings.append(f"run {forecast['id']} forecast plus cleanup reserve exceeds run ceiling")
    return {"mode": "saved-observations-only", "observed_at": snapshot.get("observed_at"), "stale": stale,
            "scope": run_id or "project", "providers": providers,
            "missing_provider_aliases": sorted(aliases - observed),
            "resources": [{k: r.get(k) for k in ["id", "provider", "run_id", "kind", "state", "billing_ended", "active_jobs", "pending_jobs"]} for r in resources],
            "budget": budget, "known_accrual_usd": totals, "complete_forecast": complete,
            "incomplete_reasons": reasons, "known_rate_subtotal_usd_per_hour": [rounded(low), rounded(high)],
            "aggregate_rate_usd_per_hour": [rounded(low), rounded(high)] if complete else None,
            **scenarios(low if complete else None, high if complete else None), "runs": forecasts,
            "warnings": warnings, "enforcement": "none; rolling-24h, authorization and deadlines require the project supervisor",
            "exclusions": "Flat fleet only; incremental non-hourly charges must be included separately."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ["setup", "status"]:
        sub = modes.add_parser(mode)
        sub.add_argument("--project", required=True, type=Path)
        if mode == "status":
            sub.add_argument("--run")
    estimate = modes.add_parser("estimate")
    for flag in ["rate-low", "rate-high", "hours-low", "hours-high"]:
        estimate.add_argument("--" + flag, type=float, required=True)
    estimate.add_argument("--fixed", type=float, default=0)
    args = parser.parse_args()
    try:
        if args.mode == "setup":
            result = setup(args.project.resolve())
        elif args.mode == "status":
            result = status(args.project.resolve(), args.run)
        else:
            for field in ["rate_low", "rate_high", "hours_low", "hours_high", "fixed"]:
                number(getattr(args, field), field)
            if args.rate_low > args.rate_high or args.hours_low > args.hours_high:
                raise ValueError("low bounds must not exceed high bounds")
            result = {"mode": "planning-estimate-only", "currency": "USD",
                      "workload_usd": [rounded(args.rate_low * args.hours_low + args.fixed), rounded(args.rate_high * args.hours_high + args.fixed)],
                      **scenarios(args.rate_low, args.rate_high, args.fixed),
                      "assumption": "Flat whole-fleet rates; fixed charges occur once per scenario. No spending authorization."}
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
