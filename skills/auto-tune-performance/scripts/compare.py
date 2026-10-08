#!/usr/bin/env python3
"""Compare declared independent paired performance blocks. Never runs a workload."""
import argparse
import json
import math
from pathlib import Path
import random
import statistics
import sys


EXIT_CODES = {"accept": 0, "reject": 1, "keep_baseline": 1, "invalid": 2,
              "inconclusive": 3, "needs_confirmation": 3}


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def numeric(value, label, low=0, high=math.inf, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be finite and numeric")
    if not low <= value <= high or (integer and not isinstance(value, int)):
        raise ValueError(f"{label} outside supported bounds [{low}, {high}]")
    return value


def records(rows, label):
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{label} requires a nonempty array")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} entries must be objects")
        identity = text(row.get("id"), f"{label}.id")
        if identity in seen:
            raise ValueError(f"duplicate {label} id {identity}")
        seen.add(identity)
    return rows


def quantile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def effect(log_ratio, direction):
    ratio = math.exp(log_ratio)
    return 100 * (1 - ratio) if direction == "lower" else 100 * (ratio - 1)


def compare(data):
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("expected experiment object with version 1")
    identity = text(data.get("experiment_id"), "experiment_id")
    if data.get("phase") not in ["screen", "confirm"]:
        raise ValueError("phase must be screen or confirm")
    design = data["design"]
    if design.get("unit") != "independent-paired-block":
        raise ValueError("helper requires independent-paired-block design")
    min_blocks = numeric(design["min_blocks"], "min_blocks", 4, 100000, integer=True)
    confidence = numeric(design["confidence"], "confidence", .8, .999)
    resamples = numeric(design["resamples"], "resamples", 2000, 200000, integer=True)
    seed = numeric(design["seed"], "seed", 0, 2**32 - 1, integer=True)
    if not isinstance(design.get("profiled"), bool):
        raise ValueError("profiled must be boolean")
    invalid, rejected, unknown = [], [], []
    if design["profiled"]:
        invalid.append("profiled outcome measurements")
    for arm in ["baseline", "candidate"]:
        for key in ["revision", "environment_id", "workload_id", "harness_id"]:
            text(data[arm].get(key), f"{arm}.{key}")
    for key in ["environment_id", "workload_id", "harness_id"]:
        if data["baseline"][key] != data["candidate"][key]:
            invalid.append(f"arm mismatch: {key}")
    if data["baseline"]["revision"] == data["candidate"]["revision"]:
        invalid.append("treatment identities are identical")
    checks = records(data["hard_checks"], "hard_checks")
    for check in checks:
        text(check.get("evidence"), "hard_check.evidence")
        for arm in ["baseline", "candidate"]:
            if check.get(arm) not in ["pass", "fail", "unknown"]:
                raise ValueError("hard check must be pass, fail or unknown")
        if check["baseline"] == "fail":
            invalid.append(f"baseline hard check failed: {check['id']}")
        if check["candidate"] == "fail":
            rejected.append(f"candidate hard check failed: {check['id']}")
        if "unknown" in [check["baseline"], check["candidate"]]:
            unknown.append(f"hard check unknown: {check['id']}")
    metrics = records(data["metrics"], "metrics")
    if not any(metric.get("role") == "primary" for metric in metrics):
        raise ValueError("at least one primary metric is required")
    for metric in metrics:
        text(metric.get("unit"), "metric.unit")
        if metric.get("direction") not in ["lower", "higher"] or metric.get("role") not in ["primary", "guardrail"]:
            raise ValueError("metric requires supported direction and role")
        threshold = numeric(metric["threshold_pct"], "threshold_pct", 0, 99.999)
        if metric["role"] == "primary" and threshold == 0:
            raise ValueError("primary threshold_pct must be positive")
        blocks = records(metric["blocks"], "blocks")
        orders = {"AB": 0, "BA": 0}
        for block in blocks:
            if block.get("order") not in orders:
                raise ValueError("block.order must be AB or BA")
            orders[block["order"]] += 1
            if not isinstance(block.get("valid"), bool):
                raise ValueError("block.valid must be boolean")
            if not block["valid"]:
                invalid.append(f"invalid work: {metric['id']}/{block['id']}")
            for arm in ["baseline", "candidate"]:
                numeric(block[arm], f"block.{arm}")
                if block[arm] <= 0:
                    raise ValueError("ratio analysis requires strictly positive metrics")
        if not all(orders.values()) or abs(orders["AB"] - orders["BA"]) > 1:
            invalid.append(f"unbalanced paired order: {metric['id']}")
    report = {"version": 1, "experiment_id": identity, "phase": data["phase"],
              "method": "paired log-ratio percentile bootstrap with Bonferroni-adjusted bounds",
              "family_confidence": confidence, "metric_count": len(metrics), "seed": seed,
              "resamples": resamples, "metrics": [], "hard_checks": checks,
              "limitations": ["Approximate intervals assume independent comparable blocks.",
                              "Does not verify artifacts, manifest identities, omitted metrics or fresh confirmation.",
                              "Does not correct repeated peeking or candidate selection; use preplanned confirmation."]}

    def finish(decision, reasons):
        report.update(decision=decision, reasons=reasons)
        return report

    if invalid:
        return finish("invalid", invalid + rejected + unknown)
    if rejected:
        return finish("reject", rejected + unknown)
    # Ten expected bootstrap draws in each adjusted tail is only a numerical floor.
    tail = (1 - confidence) / (2 * len(metrics))
    resolution_ok = resamples * tail >= 10
    for metric in metrics:
        blocks = metric["blocks"]
        baseline = [block["baseline"] for block in blocks]
        candidate = [block["candidate"] for block in blocks]
        logs = [math.log(c) - math.log(b) for b, c in zip(baseline, candidate)]
        point = effect(statistics.fmean(logs), metric["direction"])
        row = {"id": metric["id"], "unit": metric["unit"], "role": metric["role"],
               "direction": metric["direction"], "threshold_pct": metric["threshold_pct"],
               "independent_blocks": len(blocks), "baseline_median": statistics.median(baseline),
               "candidate_median": statistics.median(candidate),
               "baseline_range": [min(baseline), max(baseline)], "candidate_range": [min(candidate), max(candidate)],
               "paired_improvement_pct": point, "adjusted_interval_pct": None,
               "warning": "identical paired ratios; inspect measurement resolution/duplication" if max(logs) - min(logs) <= 1e-12 else None}
        if len(blocks) < min_blocks or not resolution_ok:
            row.update(gate="inconclusive", reason="insufficient independent blocks or bootstrap tail resolution")
        else:
            rng = random.Random(seed)
            count = len(logs)
            distribution = sorted(statistics.fmean(rng.choices(logs, k=count)) for _ in range(resamples))
            bounds = sorted(effect(quantile(distribution, p), metric["direction"]) for p in [tail, 1 - tail])
            row["adjusted_interval_pct"] = bounds
            boundary = metric["threshold_pct"] if metric["role"] == "primary" else -metric["threshold_pct"]
            if bounds[0] >= boundary:
                row["gate"] = "pass"
            elif bounds[1] < boundary:
                row["gate"] = "regression" if metric["role"] == "guardrail" or bounds[1] < 0 else "no_meaningful_gain"
            else:
                row["gate"] = "inconclusive"
        report["metrics"].append(row)
    gates = [row["gate"] for row in report["metrics"]]
    if "regression" in gates:
        return finish("reject", [row["id"] + ": regression" for row in report["metrics"] if row["gate"] == "regression"] + unknown)
    if unknown or "inconclusive" in gates:
        return finish("inconclusive", unknown + [row["id"] + ": inconclusive" for row in report["metrics"] if row["gate"] == "inconclusive"])
    if "no_meaningful_gain" in gates:
        return finish("keep_baseline", [row["id"] + ": gain below meaningful threshold" for row in report["metrics"] if row["gate"] == "no_meaningful_gain"])
    return finish("accept" if data["phase"] == "confirm" else "needs_confirmation",
                  ["all declared gates pass; fresh confirmation required"] if data["phase"] == "screen" else ["all declared confirmation gates pass"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", type=Path)
    args = parser.parse_args()
    try:
        report = compare(json.loads(args.experiment.read_text()))
        # Validate finiteness before writing any partial JSON to stdout.
        output = json.dumps(report, indent=2, allow_nan=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, OverflowError) as error:
        report = {"decision": "invalid", "reasons": [str(error)]}
        output = json.dumps(report, indent=2)
    print(output)
    return EXIT_CODES[report["decision"]]


if __name__ == "__main__":
    sys.exit(main())
