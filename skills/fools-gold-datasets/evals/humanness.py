"""Validate and aggregate independent style reviews; never detect AI authorship.

Usage: python3 humanness.py review.json
The collector binds the review to text/context hashes. Scores need calibrated
human or model reviewers; this program only enforces their declared contract.
"""
import hashlib
import json
import sys

DIMENSIONS = ("register", "jargon", "orthography", "regional_fit", "naturalness", "restraint")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evaluate(data):
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("expected version 1")
    text, context = data["text"], data["context"]
    if not isinstance(text, str) or not text.strip() or not isinstance(context, str) or not context.strip():
        raise ValueError("nonempty text and context required")
    review = data["review"]
    if not isinstance(review, dict):
        raise ValueError("review must be an object")
    if review["text_sha256"] != digest(text) or review["context_sha256"] != digest(context):
        raise ValueError("stale review binding")
    for key in ("reviewer", "rubric_version"):
        if not isinstance(review.get(key), str) or not review[key].strip():
            raise ValueError(f"missing {key}")
    if review["rubric_version"] != "humanness-v1":
        raise ValueError("unsupported rubric")
    if review.get("calibration") not in ("passed", "pending", "failed"):
        raise ValueError("calibration must be passed, pending or failed")
    if review.get("fidelity") not in ("pass", "fail", "unassessed"):
        raise ValueError("fidelity must be pass, fail or unassessed")
    scores = review["dimensions"]
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        raise ValueError("all six dimensions required")
    for name, row in scores.items():
        if not isinstance(row, dict):
            raise ValueError("dimension must be an object")
        score = row["score"]
        if score is not None and (type(score) is not int or not 0 <= score <= 4):
            raise ValueError(f"invalid score: {name}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise ValueError("every score or abstention needs a reason")
        spans = row.get("spans")
        if not isinstance(spans, list) or (score is not None and score < 3 and not spans):
            raise ValueError("weak scores require localized evidence")
        for span in spans:
            if not isinstance(span, dict):
                raise ValueError("span must be an object")
            start, end = span["start"], span["end"]
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
                raise ValueError("invalid Unicode character offsets")
            if text[start:end] != span["quote"]:
                raise ValueError("evidence quote does not match candidate")
    values = [row["score"] for row in scores.values()]
    if review["fidelity"] == "fail" or any(s is not None and s < 3 for s in values):
        verdict = "fail"
    elif None in values or review["calibration"] != "passed" or review["fidelity"] != "pass":
        verdict = "unassessed"
    else:
        verdict = "pass"
    return {"verdict": verdict, "dimensions": {k: v["score"] for k, v in scores.items()},
            "text_sha256": digest(text), "rubric_version": review["rubric_version"],
            "meaning": "contextual style gate, not AI-authorship probability",
            "limits": "Reviewer judgments, calibration and fidelity are supplied claims; collector must verify them."}


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: humanness.py review.json")
        with open(sys.argv[1], encoding="utf-8") as source:
            result = evaluate(json.load(source))
        print(json.dumps(result, indent=2))
        sys.exit({"pass": 0, "fail": 1, "unassessed": 3}[result["verdict"]])
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"verdict": "invalid", "error": str(error)}))
        sys.exit(2)
