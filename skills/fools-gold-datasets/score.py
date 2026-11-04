#!/usr/bin/env python3
"""Score a fool's gold candidate from categorized misses and decide the next step.

Merges misses from the judge, the Describer audit and overlap.py outputs, applies
severity floors, computes a 0-100 score and returns one decision:
  pass          rubric threshold met; coordinator still verifies acceptance evidence
  revise-build  same spec, Builder fixes the build-caused misses (inner loop)
  diagnose      inspect a recurring serious or low-scoring failure before choosing a repair
  rewrite-spec  Describer rewrites the spec from spec_learnings, fresh Builder (outer loop)
  stop          attempts exhausted or no longer improving; reject and report

Stdlib only; run with `python3 -I`. Exit 0 = pass, 1 = any other decision, 2 = usage error.
Migration: reviews must explicitly contain `misses: []` when clean. Every miss
must supply category, severity, cause, where and summary; invalid reports are
errors, never successful reviews. Keep full overlap.py JSON, not a pass-only stub.
Recurrence (category + location) is diagnostic only: flags never change a miss's
reported cause or severity beyond the category floors. Only leaks or explicit
spec-caused high/fatal misses justify rewrite-spec. Diagnose consumes the current
build lane; exhausted rounds or plateau stop a failing lane. Low-scoring failures
also diagnose instead of guessing a spec defect. A final spec attempt may still
use its remaining build rounds; a passing rubric remains eligible at the limits.
Duplicate occurrences incur one maximum-severity penalty; their `reports` retain
every source's reported cause/severity (and effective category floor). Serious
cause or severity disagreement requires diagnosis before a repair is selected.
Overlap failures must agree with the chosen mode, metrics and rounded displays;
contradictory failure text is invalid input, not evidence of a leak.
"""
import argparse
import json
import math
import re
import sys

CATEGORIES = {
    "format",           # container, version, unit count, page size, codec, duration
    "layout",           # block positions, columns, margins, z-order
    "reading-order",
    "typography",       # font classes, sizes, weight, leading
    "table",            # shape, merged cells, header rows, cell content type
    "figure",           # images, charts, captions and their links
    "difficulty",       # a spec difficulty feature missing or made easier
    "content-length",   # block budgets, paraphrase length band
    "content-meaning",  # paraphrase lost meaning; swap/synthetic incoherent
    "mode",             # content mode rules broken in some other way
    "leak",             # source text, entity, image or trade dress in the candidate
    "gold",             # gold labels missing or disagreeing with the rendered file
    "audio",            # speakers, turns, overlaps, noise, loudness
    "file",             # invisible file-level traits vs the spec's File profile
    "realism",          # tells: disclaimers, placeholders, toy names, library metadata, implausible data
}
SEVERITIES = ["low", "medium", "high", "fatal"]
WEIGHTS = {"low": 1, "medium": 5, "high": 15}
# Minimum severity per category. A leak always fails closed.
FLOORS = {"leak": "fatal", "gold": "high", "format": "high"}
PASS_SCORE = 85
DIAGNOSE_BELOW = 50


def sev_rank(s):
    return SEVERITIES.index(s)


def load(path):
    def unique_object(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError("duplicate JSON field")
            result[k] = v
        return result
    with open(path, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=unique_object)


def review_misses(report):
    if not isinstance(report, dict) or not isinstance(report.get("misses"), list):
        raise ValueError("review requires an explicit misses list (use [] for a completed clean review)")
    if "error" in report or report.get("status", "complete") != "complete":
        raise ValueError("review reports an error or incomplete status")
    return report["misses"]


def normalize(m, source, report=None):
    if not isinstance(m, dict):
        raise ValueError("each miss must be an object")
    for field in ("category", "severity", "cause", "where", "summary"):
        if not isinstance(m.get(field), str) or not m[field].strip():
            raise ValueError(f"miss requires nonempty string field: {field}")
    cat, sev, cause = m["category"], m["severity"], m["cause"]
    if cat not in CATEGORIES or sev not in SEVERITIES or cause not in ("spec", "build", "unknown"):
        raise ValueError("unknown miss category, severity or cause; use rubric enum values")
    floor = FLOORS.get(cat)
    if floor and sev_rank(sev) < sev_rank(floor):
        sev = floor
    return {
        "category": cat,
        "severity": sev,
        "reported_severity": m["severity"],
        "cause": cause,
        "where": m.get("where", "document"),
        "summary": m.get("summary", "").strip(),
        "source": source,
        "report": report,
        "known_category": cat in CATEGORIES,
    }


def overlap_misses(where, report):
    # Map overlap.py failures to misses. Its text can quote the source; keep only counts here.
    if not isinstance(report, dict) or report.get("status", "complete") != "complete" or "error" in report:
        raise ValueError("overlap report is incomplete or indeterminate; rerun the check")
    if report.get("mode") not in ("verbatim", "paraphrase", "public-domain-swap", "synthetic"):
        raise ValueError("invalid overlap mode")
    for field in ("source_words", "candidate_words", "ngram_n", "shared_ngrams", "longest_shared_run"):
        value = report.get(field)
        if type(value) is not int or value < (1 if field in ("source_words", "candidate_words", "ngram_n") else 0):
            raise ValueError(f"invalid overlap count: {field}")
    for field in ("length_ratio", "ngram_overlap"):
        value = report.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(f"invalid overlap metric: {field}")
    if report["ngram_overlap"] > 1:
        raise ValueError("invalid overlap fraction")
    if (report["longest_shared_run"] > min(report["source_words"], report["candidate_words"])
            or abs(report["length_ratio"] - report["candidate_words"] / report["source_words"]) > 0.000501
            or report["shared_ngrams"] == 0 and report["ngram_overlap"] != 0):
        raise ValueError("inconsistent overlap metrics")
    n, shared, run = report["ngram_n"], report["shared_ngrams"], report["longest_shared_run"]
    source_positions = max(0, report["source_words"] - n + 1)
    candidate_positions = max(0, report["candidate_words"] - n + 1)
    if (shared > min(source_positions, candidate_positions)
            or bool(shared) != (run >= n)):
        raise ValueError("shared n-gram count contradicts token counts or longest run")
    # overlap.py divides DISTINCT shared grams by DISTINCT candidate grams, then
    # rounds to four decimals. The denominator is not reported, but an integer
    # in [shared, candidate_positions] must exist within half a rounding unit.
    # Use integer bounds to avoid treating a legitimately rounded zero as zero
    # evidence, or accepting a fraction no possible denominator can produce.
    rounded = round(report["ngram_overlap"] * 10000)
    if report["ngram_overlap"] != round(report["ngram_overlap"], 4):
        raise ValueError("overlap fraction is not rounded to four decimal places")
    min_distinct_candidate, max_distinct_candidate = 0, candidate_positions
    if shared:
        scaled = 20000 * shared
        min_distinct_candidate = max(shared, (scaled + 2 * rounded) // (2 * rounded + 1))
        if rounded:
            max_distinct_candidate = min(candidate_positions, scaled // (2 * rounded - 1))
        if min_distinct_candidate > max_distinct_candidate:
            raise ValueError("overlap fraction cannot match shared n-gram count after rounding")
    for field in ("failures", "entity_hits"):
        if not isinstance(report.get(field), list) or any(not isinstance(x, str) or not x for x in report[field]):
            raise ValueError(f"overlap requires a string list: {field}")
    if type(report.get("pass")) is not bool or report["pass"] != (not report["failures"]):
        raise ValueError("overlap pass flag contradicts failures")
    if report["entity_hits"] and not any(f.startswith("denylisted terms present:") for f in report["failures"]):
        raise ValueError("overlap omitted denylist failures")
    if "length_checked" in report and type(report["length_checked"]) is not bool:
        raise ValueError("invalid length_checked flag")
    if report.get("length_checked") and report["mode"] == "paraphrase":
        if (100 * report["candidate_words"] < 85 * report["source_words"]
                or 100 * report["candidate_words"] > 115 * report["source_words"]) and not any(
                f.startswith("length ratio ") for f in report["failures"]):
            raise ValueError("overlap omitted length failure")
    if report["mode"] != "verbatim":
        max_overlap = 0.02 if report["mode"] == "paraphrase" else 0.005
        threshold_denominator = 50 if report["mode"] == "paraphrase" else 200
        if ((report["ngram_overlap"] > max_overlap or shared * threshold_denominator > max_distinct_candidate)
                and not any("-gram overlap " in f for f in report["failures"])):
            raise ValueError("overlap omitted n-gram failure")
        if report["longest_shared_run"] > 7 and not any(f.startswith("shared run of ") for f in report["failures"]):
            raise ValueError("overlap omitted shared-run failure")
    out = []
    for f in report["failures"]:
        gram = re.fullmatch(r"([0-9]+)-gram overlap ([0-9]+(?:\.[0-9]+)?) > ([0-9]+(?:\.[0-9]+)?)", f)
        run_failure = re.fullmatch(r"shared run of ([0-9]+) words > ([0-9]+)", f)
        entities = re.fullmatch(r"denylisted terms present: ([0-9]+)", f)
        length = re.fullmatch(r"length ratio ([0-9]+(?:\.[0-9]+)?) outside ([0-9]+(?:\.[0-9]+)?)-([0-9]+(?:\.[0-9]+)?)", f)
        if gram:
            shown, threshold = float(gram[2]), float(gram[3])
            if (report["mode"] == "verbatim" or not shared or int(gram[1]) != n
                    or threshold != max_overlap or not math.isfinite(shown) or shown > 1
                    or shown != round(shown, 3)):
                raise ValueError("n-gram failure contradicts mode, metric or threshold")
            # The displayed 3-decimal fraction and report's 4-decimal fraction
            # must share a possible denominator with an actual threshold breach.
            shown_units = round(shown * 1000)
            scaled = 2000 * shared
            min_distinct_candidate = max(min_distinct_candidate,
                                         (scaled + 2 * shown_units) // (2 * shown_units + 1))
            max_distinct_candidate = min(max_distinct_candidate, shared * threshold_denominator - 1)
            if shown_units:
                max_distinct_candidate = min(max_distinct_candidate, scaled // (2 * shown_units - 1))
            if min_distinct_candidate > max_distinct_candidate:
                raise ValueError("n-gram failure's rounded metric is inconsistent")
        elif run_failure:
            if (report["mode"] == "verbatim" or int(run_failure[1]) != run
                    or int(run_failure[2]) != 7 or run <= 7):
                raise ValueError("shared-run failure contradicts mode, metric or threshold")
        elif entities:
            if int(entities[1]) != len(report["entity_hits"]) or not report["entity_hits"]:
                raise ValueError("denylist failure contradicts entity hits")
        elif length:
            actual_ratio = report["candidate_words"] / report["source_words"]
            outside_band = (100 * report["candidate_words"] < 85 * report["source_words"]
                            or 100 * report["candidate_words"] > 115 * report["source_words"])
            if (report["mode"] != "paraphrase" or report.get("length_checked") is False
                    or (float(length[2]), float(length[3])) != (0.85, 1.15) or not outside_band
                    or abs(float(length[1]) - actual_ratio) > 0.005000001):
                raise ValueError("length failure contradicts mode, metric or band")
        else:
            raise ValueError("unrecognized overlap failure; use a supported full overlap.py report")
        if length:
            # Same bands as the rubric: up to 30% off is medium, beyond that high.
            off = abs(report.get("length_ratio", 0) - 1)
            out.append({"category": "content-length", "severity": "medium" if off <= 0.30 else "high",
                        "cause": "build", "where": where, "summary": "length outside mode band"})
        else:
            # n-gram, shared run or denylisted terms: protected content got through.
            out.append({"category": "leak", "severity": "fatal", "cause": "spec",
                        "where": where, "summary": f.split(":")[0]})
    return out


def key(m):
    return (m["category"], m["where"])


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--judge", help="judge.json with a misses list")
    p.add_argument("--audit", help="Describer audit.json with a misses list")
    p.add_argument("--misses", action="append", default=[],
                   help="extra miss report in rubric format, e.g. check_tells.py output (repeatable)")
    p.add_argument("--overlap", action="append", default=[],
                   help="overlap.py output, as path or where=path (repeatable)")
    p.add_argument("--history", help="attempts.jsonl; read for recurrence and plateau, then appended")
    p.add_argument("--attempt", type=int, default=1, help="spec attempt, 1-based")
    p.add_argument("--max-attempts", type=int, default=3)
    p.add_argument("--round", type=int, default=1, help="build round within this attempt, 1-based")
    p.add_argument("--max-rounds", type=int, default=4)
    p.add_argument("--stage", choices=["audit", "judge"], default="audit",
                   help="which review produced this report (judge runs reuse the attempt's last round)")
    p.add_argument("--no-record", action="store_true", help="read --history but do not append (trial runs)")
    p.add_argument("--patience", type=int, default=2,
                   help="stop after this many spec attempts in a row fail to beat the best by more than 3 points")
    a = p.parse_args()
    if min(a.attempt, a.round, a.max_attempts, a.max_rounds, a.patience) < 1:
        p.error("attempts, rounds and patience must be positive")
    if a.attempt > a.max_attempts or a.round > a.max_rounds:
        p.error("attempt and round must not exceed their configured maximums")
    if not (a.judge or a.audit or a.overlap or a.misses):
        print("need at least one of --judge, --audit, --overlap, --misses", file=sys.stderr)
        return 2

    raw = []
    for src, path in (("judge", a.judge), ("audit", a.audit)):
        if path:
            raw += [normalize(m, src, path) for m in review_misses(load(path))]
    for path in a.misses:
        raw += [normalize(m, "checks", path) for m in review_misses(load(path))]
    for spec in a.overlap:
        where, _, path = spec.rpartition("=")
        raw += [normalize(m, "overlap", path) for m in overlap_misses(where or "document", load(path))]

    # One occurrence incurs one maximum-severity penalty, but independent source
    # records are evidence. Never discard a reviewer just because another agrees
    # on the wording or reports a higher severity.
    groups = {}
    for m in raw:
        k = (m["category"], m["where"], m["summary"].lower())
        groups.setdefault(k, []).append(m)
    misses = []
    for records in groups.values():
        records.sort(key=lambda m: (m["source"], m["report"] or "", m["cause"], m["reported_severity"], m["summary"]))
        occurrence = dict(records[0])
        causes = {m["cause"] for m in records}
        occurrence.update({"severity": max((m["severity"] for m in records), key=sev_rank),
                           "cause": next(iter(causes)) if len(causes) == 1 else "unknown",
                           "source": records[0]["source"] if len({m["source"] for m in records}) == 1 else "multiple",
                           "cause_disagreement": len(causes) > 1,
                           "severity_disagreement": len({m["reported_severity"] for m in records}) > 1,
                           "reports": records})
        # Reported severity belongs to the individual source records, not to
        # the aggregate arithmetic severity chosen above.
        occurrence.pop("reported_severity", None)
        occurrence.pop("report", None)
        misses.append(occurrence)
    misses.sort(key=lambda m: (-sev_rank(m["severity"]), m["category"], m["where"], m["summary"]))

    history = []
    if a.history:
        try:
            with open(a.history, encoding="utf-8") as f:
                history = [json.loads(l) for l in f if l.strip()]
        except FileNotFoundError:
            pass
    # A matching category/location suggests recurrence, not its cause. Old
    # history rows without all_keys can only identify previously serious misses.
    prev_keys = {tuple(k) for h in history
                 if h["attempt"] == a.attempt and h["round"] < a.round
                 for k in h.get("all_keys", h.get("serious_keys", []))}
    earlier_keys = {tuple(k) for h in history if h["attempt"] < a.attempt
                    for k in h.get("all_keys", h.get("serious_keys", []))}
    for m in misses:
        m["recurring_within_attempt"] = key(m) in prev_keys
        m["recurring_across_attempts"] = key(m) in earlier_keys
    counts = {s: sum(1 for m in misses if m["severity"] == s) for s in SEVERITIES}
    score = 0 if counts["fatal"] else max(0, 100 - sum(WEIGHTS[m["severity"]] for m in misses))
    passed = counts["fatal"] == 0 and counts["high"] == 0 and score >= PASS_SCORE
    # Final score of each earlier attempt (its last recorded round), then this one.
    finals = {}
    for h in history:
        if h["attempt"] < a.attempt:
            finals[h["attempt"]] = h["score"]
    sequence = [finals[k] for k in sorted(finals)] + [score]
    stale, best = 0, None
    for s_ in sequence:
        if best is not None and s_ <= best + 3:
            stale += 1
        else:
            stale = 0
        best = s_ if best is None else max(best, s_)

    serious = [m for m in misses if m["severity"] in ("high", "fatal")]
    disagreements = [m for m in serious if m["cause_disagreement"] or m["severity_disagreement"]]
    needs_spec = any((m["category"] == "leak" or m["cause"] == "spec") and m not in disagreements for m in serious)
    recurring_serious = [m for m in serious if m["cause"] in ("build", "unknown")
                         and (m["recurring_within_attempt"] or m["recurring_across_attempts"])]
    needs_diagnosis = bool(disagreements or recurring_serious) or score < DIAGNOSE_BELOW
    reasons = []
    for m in serious:
        if m in disagreements:
            reasons.append(f"reviewer cause/severity disagreement at {m['where']}; adjudicate source reports")
        elif m["category"] == "leak":
            reasons.append(f"leak at {m['where']}")
        elif m["cause"] == "spec":
            reasons.append(f"spec-caused {m['severity']} {m['category']} at {m['where']}")
        elif m in recurring_serious:
            reasons.append(f"recurring {m['severity']} {m['category']} at {m['where']} (reported cause={m['cause']}); diagnose")
    if not passed and a.round >= a.max_rounds:
        reasons.append(f"build rounds exhausted ({a.round}/{a.max_rounds})")
    if score < DIAGNOSE_BELOW:
        reasons.append(f"score {score} < {DIAGNOSE_BELOW}; diagnose without inferring cause")

    if passed:
        decision = "pass"
    elif stale >= a.patience:
        decision = "stop"
        reasons.append(f"plateau: {stale} attempt(s) without beating best score {best} by more than 3")
    elif disagreements:
        decision = "stop" if a.round >= a.max_rounds else "diagnose"
    elif needs_spec:
        if a.attempt >= a.max_attempts:
            decision = "stop"
            reasons.append(f"spec attempts exhausted ({a.attempt}/{a.max_attempts})")
        else:
            decision = "rewrite-spec"
    elif a.round >= a.max_rounds:
        decision = "stop"
    elif needs_diagnosis:
        decision = "diagnose"
    else:
        decision = "revise-build"

    def by_category(items):
        out = {}
        for m in items:
            out.setdefault(m["category"], []).append(m)
        return out

    result = {
        "attempt": a.attempt,
        "round": a.round,
        "score": score,
        "pass": passed,
        "decision": decision,
        "reasons": reasons,
        "counts": counts,
        "fatal_or_high": [f"{m['severity']}: {m['category']} @ {m['where']} - {m['summary']}" for m in serious],
        "by_category": by_category(misses),
        # Dirty-side evidence: retain reported cause, including build/unknown.
        # Only populate spec learnings when evidence actually warrants a rewrite.
        "spec_learnings": [f"{m['category']} @ {m['where']} ({m['severity']}, cause={m['cause']}"
                           f"{', recurring across attempts' if m.get('recurring_across_attempts') else ''}): {m['summary']}"
                           for m in misses if needs_spec and not disagreements and decision in ("rewrite-spec", "stop")],
        # Coordinator investigates the implementation, tooling and review evidence
        # before changing the spec. These notes are not Builder instructions.
        "diagnosis_notes": [f"{m['category']} @ {m['where']} ({m['severity']}, cause={m['cause']}, "
                            f"cause_disagreement={m['cause_disagreement']}, severity_disagreement={m['severity_disagreement']}, "
                            f"recurring_within_attempt={m['recurring_within_attempt']}, "
                            f"recurring_across_attempts={m['recurring_across_attempts']}): {m['summary']}"
                            for m in misses if needs_diagnosis and decision in ("diagnose", "stop")],
        # For the Builder on revise-build. Run overlap.py --no-length on these before sending.
        "builder_notes": [f"{m['where']}: {m['summary']}" for m in misses
                          if decision == "revise-build" and m["category"] != "leak"],
        "unknown_categories": sorted({m["category"] for m in misses if not m["known_category"]}),
        "serious_keys": sorted({key(m) for m in serious}),
        "all_keys": sorted({key(m) for m in misses}),
        "stage": a.stage,
    }
    if a.history and not a.no_record:
        with open(a.history, "a", encoding="utf-8") as f:
            f.write(json.dumps({k: result[k] for k in ("attempt", "round", "stage", "score", "decision", "counts", "serious_keys", "all_keys")}) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, KeyError) as e:
        # Do not echo untrusted report values (or write a successful history row).
        print(f"[score] invalid input ({type(e).__name__}); require complete rubric/overlap reports", file=sys.stderr)
        sys.exit(2)
