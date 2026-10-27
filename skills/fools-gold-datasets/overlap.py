#!/usr/bin/env python3
"""Deterministic leak and length check for fool's gold fixtures.

Compares candidate text (extracted fixture text, a spec, or revision notes)
against source text. Stdlib only; run with `python3 -I`.

Exit 0 = pass, 1 = fail for the chosen mode, 2 = usage error.
NFKC/casefold normalization and Unicode letters/numbers/marks are used on both
sides. Punctuation separates tokens. Han/Kana/Hangul use character units, not
linguistic words; reported length ratios and runs use those same mixed units.
Thai/Lao/Khmer/Myanmar segmentation and control/format characters are unsupported:
the report is indeterminate (exit 2), never a clean pass. This is a heuristic
overlap check, not a multilingual semantic or confusable-character detector.
"""
import argparse
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher

# Capitalized tokens that are not entities often enough to ignore.
COMMON = set(
    "a an the and or but if of in on at to for by with from as is it its this that these those "
    "he she they we you i his her their our your my me him them us chapter page table figure "
    "january february march april may june july august september october november december "
    "monday tuesday wednesday thursday friday saturday sunday mr mrs ms dr".split()
)

THRESHOLDS = {
    # mode: (max 8-gram overlap fraction, max shared word run, length band, enforce entities)
    "verbatim": (None, None, None, False),
    "paraphrase": (0.02, 7, (0.85, 1.15), False),
    "public-domain-swap": (0.005, 7, None, True),
    "synthetic": (0.005, 7, None, True),
}


def normalized(text):
    return unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", text).casefold())


def character_unit(c):
    # Stable non-linguistic segmentation, including Han extension planes.
    n = ord(c)
    return (0x3400 <= n <= 0x9FFF or 0x20000 <= n <= 0x323AF
            or 0x3040 <= n <= 0x30FF or 0xAC00 <= n <= 0xD7AF)


def words(text):
    tokens, word = [], ""
    for c in normalized(text):
        category = unicodedata.category(c)
        if character_unit(c) and category[0] in "LN":
            if word:
                tokens.append(word)
                word = ""
            tokens.append(c)
        elif category[0] in "LN" or category[0] == "M" and word:
            word += c
        else:
            if word:
                tokens.append(word)
                word = ""
            # Attach combining marks to a preceding character unit.
            if category[0] == "M" and tokens:
                tokens[-1] += c
    if word:
        tokens.append(word)
    return tokens


def unsupported(text):
    for c in normalized(text):
        n = ord(c)
        if (0x0E00 <= n <= 0x0EFF or 0x1000 <= n <= 0x109F or 0x1780 <= n <= 0x17FF
                or 0xA9E0 <= n <= 0xA9FF or 0xAA60 <= n <= 0xAA7F):
            return True
        if c == "\ufffd" or unicodedata.category(c)[0] == "C" and c not in "\t\n\r":
            return True
    return False


def ngrams(ws, n):
    return {tuple(ws[i : i + n]) for i in range(len(ws) - n + 1)}


def longest_run(src, cand):
    # Longest contiguous shared word sequence.
    m = SequenceMatcher(None, src, cand, autojunk=False)
    best = m.find_longest_match(0, len(src), 0, len(cand))
    return best.size, " ".join(cand[best.b : best.b + best.size])


def source_entities(text):
    # Capitalized words not at a sentence start, seen in the source.
    ents = set()
    for sent in re.split(r"(?<=[.!?])\s+|\n+", text):
        toks = re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", sent))
        for t in toks[1:]:
            if t[:1].isupper() and t.lower() not in COMMON and len(t) > 2:
                ents.add(normalized(t))
    return ents


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--source", required=True, help="source text file (dirty side)")
    p.add_argument("--candidate", required=True, help="candidate text, spec, or notes")
    p.add_argument("--mode", required=True, choices=sorted(THRESHOLDS))
    p.add_argument("--denylist", help="extra terms to forbid, one per line")
    p.add_argument("--entities", action="store_true", help="also forbid auto-detected source entities (implied by swap/synthetic)")
    p.add_argument("--no-length", action="store_true", help="skip length band (specs, notes)")
    p.add_argument("-n", type=int, default=8, help="n-gram size (default 8)")
    a = p.parse_args()
    if a.n < 1:
        p.error("-n must be positive")

    src_text = open(a.source, encoding="utf-8").read()
    cand_text = open(a.candidate, encoding="utf-8").read()
    src, cand = words(src_text), words(cand_text)
    deny = set()
    if a.denylist:
        deny |= {l.strip() for l in open(a.denylist, encoding="utf-8") if l.strip()}
    if THRESHOLDS[a.mode][3] or a.entities:
        deny |= source_entities(src_text)
    if (not src or not cand or unsupported(src_text) or unsupported(cand_text)
            or any(unsupported(t) or not words(t) for t in deny)):
        print(json.dumps({"status": "indeterminate", "mode": a.mode, "pass": False,
                          "failures": ["empty or unsupported text/tokenization; manual review required"]}))
        return 2

    src_grams, cand_grams = ngrams(src, a.n), ngrams(cand, a.n)
    shared = cand_grams & src_grams
    overlap = len(shared) / max(1, len(cand_grams))
    run, run_text = longest_run(src, cand)
    ratio = len(cand) / len(src)

    max_overlap, max_run, band, _ = THRESHOLDS[a.mode]
    # Exact normalized token sequences: same boundary policy for terms and text.
    # CJK character units let explicit terms match inside unspaced passages.
    term_tokens = {t: tuple(words(t)) for t in deny}
    candidates_by_size = {size: ngrams(cand, size) for size in {len(ts) for ts in term_tokens.values()}}
    entity_hits = sorted(t for t, ts in term_tokens.items() if ts in candidates_by_size[len(ts)])

    failures = []
    if max_overlap is not None and overlap > max_overlap:
        failures.append(f"{a.n}-gram overlap {overlap:.3f} > {max_overlap}")
    if max_run is not None and run > max_run:
        failures.append(f"shared run of {run} words > {max_run}")
    if band and not a.no_length and not (band[0] <= ratio <= band[1]):
        failures.append(f"length ratio {ratio:.2f} outside {band[0]}-{band[1]}")
    if entity_hits:
        failures.append(f"denylisted terms present: {len(entity_hits)}")

    # Output is for the Orchestrator only: it can quote source text, so never forward it to the Builder.
    print(json.dumps({
        "status": "complete",
        "tokenization": "unicode-nfkc-casefold-words-cjk-characters-v1",
        "length_checked": bool(band and not a.no_length),
        "mode": a.mode,
        "source_words": len(src),
        "candidate_words": len(cand),
        "length_ratio": round(ratio, 3),
        "ngram_n": a.n,
        "ngram_overlap": round(overlap, 4),
        "shared_ngrams": len(shared),
        "longest_shared_run": run,
        "longest_shared_run_text": run_text if a.mode != "verbatim" else None,
        "entity_hits": entity_hits,
        "pass": not failures,
        "failures": failures,
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, UnicodeError) as e:
        print(json.dumps({"status": "indeterminate", "pass": False,
                          "failures": [f"input unavailable or not UTF-8 ({type(e).__name__})"]}))
        sys.exit(2)
