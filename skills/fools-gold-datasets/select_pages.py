#!/usr/bin/env python3
"""Pick dataset rows from candidate PDFs: diverse single pages, multi-page spans, or whole documents.

A row is one page by default. In `spans` mode a row is the smallest contiguous
window that holds a table or image running across a page break, plus
--context pages on each side (a table over pages 5-6 becomes pages 4-7).

Uses `mutool draw -F stext.json` (MuPDF) for text-line and image boxes and
`qpdf` to cut rows out with --extract. Candidate PDFs are untrusted: each
mutool call gets a timeout, a minimal environment and a page cap. Run this
from a shell that holds no secrets.

Stdlib only; run with `python3 -I`. Output: JSONL rows on stdout.
"""
import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Preserve configured tool and scratch paths without forwarding credentials.
SAFE_ENV = {key: os.environ[key] for key in
            ("PATH", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR")
            if key in os.environ}
SAFE_ENV.setdefault("PATH", os.defpath)
SAFE_ENV.update({"LANG": "C", "LC_ALL": "C"})
CHUNK = 50          # pages per mutool call
EDGE = 0.22         # a region within this fraction of the top/bottom counts as touching the break
ROW_TOL = 2.5       # points: lines whose baselines differ by less share a row
MIN_CELLS = 3       # separate line segments in one row to count as a table row
MIN_TABLE_ROWS = 3  # consecutive table rows to count as a table region


def run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, env=SAFE_ENV, check=True).stdout


def page_count(pdf, timeout):
    out = run(["pdfinfo", str(pdf)], timeout).decode("utf-8", "replace")
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise ValueError("no page count")


def stext_pages(pdf, first, last, timeout):
    raw = run(["mutool", "draw", "-q", "-F", "stext.json", "-O", "preserve-images",
               "-o", "-", str(pdf), f"{first}-{last}"], timeout)
    return json.loads(raw)["pages"]


def walk(blocks):
    for b in blocks:
        yield b
        yield from walk(b.get("blocks", []))


def regions(page):
    """Return page size, text lines, image boxes and table regions (y0, y1) for one page."""
    w, h = page.get("width", 612), page.get("height", 792)
    lines, images = [], []
    for b in walk(page.get("blocks", [])):
        if b.get("type") == "image":
            bb = b["bbox"]
            images.append((bb["x"], bb["y"], bb["x"] + bb["w"], bb["y"] + bb["h"]))
        for ln in b.get("lines", []):
            t = ln.get("text", "").strip()
            if t:
                bb = ln["bbox"]
                lines.append((ln.get("y", bb["y"] + bb["h"]), bb["x"], bb["x"] + bb["w"], len(t),
                              ln.get("font", {}).get("size", 0)))
    # Group lines into rows by baseline; a row with several separate segments looks like a table row.
    lines.sort()
    rows, cur = [], []
    for ln in lines:
        if cur and abs(ln[0] - cur[0][0]) > ROW_TOL:
            rows.append(cur)
            cur = []
        cur.append(ln)
    if cur:
        rows.append(cur)
    tables, run_ = [], []
    for r in rows:
        if len(r) >= MIN_CELLS:
            run_.append(r)
            continue
        if len(run_) >= MIN_TABLE_ROWS:
            tables.append((run_[0][0][0], run_[-1][0][0]))
        run_ = []
    if len(run_) >= MIN_TABLE_ROWS:
        tables.append((run_[0][0][0], run_[-1][0][0]))
    return w, h, lines, images, tables, len(rows)


def features(w, h, lines, images, tables, nrows):
    chars = sum(l[3] for l in lines)
    img_area = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in images) / max(1.0, w * h)
    # Columns: distinct left edges used by at least 15% of lines.
    lefts = defaultdict(int)
    for l in lines:
        lefts[round(l[1] / 20)] += 1
    cols = max(1, sum(1 for c in lefts.values() if c >= max(3, 0.15 * len(lines))))
    sizes = sorted({round(l[4]) for l in lines if l[4]})
    scanned = img_area > 0.8 and chars < 50
    return {
        "chars": chars,
        "lines": len(lines),
        "columns": min(cols, 4),
        "images": len(images),
        "image_area": round(min(img_area, 1.0), 3),
        "tables": len(tables),
        "font_sizes": len(sizes),
        "scanned": scanned,
        "blank": chars < 20 and not images,
    }


def bucket(f):
    density = "sparse" if f["chars"] < 600 else "medium" if f["chars"] < 2500 else "dense"
    return (
        "scan" if f["scanned"] else "born-digital",
        f"cols{f['columns']}",
        "table" if f["tables"] else "no-table",
        "image" if f["images"] else "no-image",
        density,
    )


def analyse(pdf, max_pages, timeout):
    n = page_count(pdf, timeout)
    scan_to = min(n, max_pages)
    pages = []
    for first in range(1, scan_to + 1, CHUNK):
        last = min(scan_to, first + CHUNK - 1)
        for i, pg in enumerate(stext_pages(pdf, first, last, timeout)):
            w, h, lines, images, tables, nrows = regions(pg)
            pages.append({
                "page": first + i,
                "h": h,
                "images": images,
                "tables": tables,
                "features": features(w, h, lines, images, tables, nrows),
            })
    return n, pages


def spans(pages, context, total):
    """Find tables or images that continue across a page break; return windows with context pages."""
    found = []
    for a, b in zip(pages, pages[1:]):
        if b["page"] != a["page"] + 1:
            continue
        kinds = []
        if any(y1 > a["h"] * (1 - EDGE) for _, y1 in a["tables"]) and \
           any(y0 < b["h"] * EDGE for y0, _ in b["tables"]):
            kinds.append("table")
        big = lambda box, p: (box[2] - box[0]) * (box[3] - box[1]) > 0.05 * 612 * p["h"]
        if any(big(i, a) and i[3] > a["h"] * (1 - EDGE) for i in a["images"]) and \
           any(big(i, b) and i[1] < b["h"] * EDGE for i in b["images"]):
            kinds.append("image")
        for k in kinds:
            found.append([a["page"], b["page"], {k}])
    # Merge chains (a table over pages 5-6-7 is one span).
    merged = []
    for s in sorted(found):
        if merged and s[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], s[1])
            merged[-1][2] |= s[2]
        else:
            merged.append(s)
    out = []
    for start, end, kinds in merged:
        lo, hi = max(1, start - context), min(total, end + context)
        out.append({"pages": list(range(lo, hi + 1)), "span": [start, end], "kind": "span-" + "+".join(sorted(kinds))})
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pdfs", nargs="+", help="candidate PDFs or directories of PDFs")
    p.add_argument("--mode", choices=["pages", "spans", "documents"], default="pages")
    p.add_argument("--count", type=int, default=40, help="rows to emit")
    p.add_argument("--per-doc", type=int, default=4, help="max rows from one document")
    p.add_argument("--context", type=int, default=1, help="pages before and after a span")
    p.add_argument("--max-doc-pages", type=int, default=60, help="documents mode: skip longer documents")
    p.add_argument("--max-scan-pages", type=int, default=400, help="analyse at most this many pages per document")
    p.add_argument("--timeout", type=int, default=120, help="seconds per mutool/qpdf call")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--extract", help="write each row as its own PDF into this directory (qpdf)")
    a = p.parse_args()

    files = []
    for x in a.pdfs:
        path = Path(x)
        files += sorted(path.rglob("*.pdf")) if path.is_dir() else [path]
    rng = random.Random(a.seed)

    candidates = []
    for pdf in files:
        try:
            total, pages = analyse(pdf, a.max_scan_pages, a.timeout)
        except (subprocess.SubprocessError, ValueError, json.JSONDecodeError, OSError) as e:
            print(f"[select-pages] skip {pdf.name}: {type(e).__name__}", file=sys.stderr)
            continue
        digest = sha256(pdf)
        print(f"[select-pages] {pdf.name}: {total} pages, analysed {len(pages)}", file=sys.stderr)
        base = {"doc": str(pdf), "sha256": digest, "doc_pages": total}
        if a.mode == "pages":
            for pg in pages:
                if not pg["features"]["blank"]:
                    candidates.append({**base, "pages": [pg["page"]], "kind": "page",
                                       "bucket": "/".join(bucket(pg["features"])), "features": pg["features"]})
        elif a.mode == "spans":
            for s in spans(pages, a.context, total):
                feats = [pg["features"] for pg in pages if pg["page"] in s["pages"]]
                candidates.append({**base, **s, "bucket": s["kind"], "features": feats})
        elif total <= a.max_doc_pages:
            agg = [pg["features"] for pg in pages]
            key = "/".join(sorted({"/".join(bucket(f)[:3]) for f in agg}))[:200]
            candidates.append({**base, "pages": list(range(1, total + 1)), "kind": "document",
                               "bucket": key, "features": {"pages": total,
                                                            "tables": sum(f["tables"] for f in agg),
                                                            "images": sum(f["images"] for f in agg)}})

    # Diverse pick: round-robin over feature buckets, shuffled, capped per document.
    by_bucket = defaultdict(list)
    for c in candidates:
        by_bucket[c["bucket"]].append(c)
    for v in by_bucket.values():
        rng.shuffle(v)
    keys = sorted(by_bucket)
    rng.shuffle(keys)
    per_doc, chosen, used_pages = defaultdict(int), [], defaultdict(set)
    cap = max(a.per_doc, 1)
    while len(chosen) < a.count and any(by_bucket[k] for k in keys):
        for k in keys:
            while by_bucket[k]:
                c = by_bucket[k].pop()
                if per_doc[c["doc"]] >= cap or used_pages[c["doc"]] & set(c["pages"]):
                    continue
                per_doc[c["doc"]] += 1
                used_pages[c["doc"]] |= set(c["pages"])
                chosen.append(c)
                break
            if len(chosen) >= a.count:
                break

    buckets_hit = len({c["bucket"] for c in chosen})
    print(f"[select-pages] {len(candidates)} candidates in {len(by_bucket)} buckets -> "
          f"{len(chosen)} rows across {buckets_hit} buckets, {len(per_doc)} documents", file=sys.stderr)
    if a.extract:
        out = Path(a.extract)
        out.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(chosen):
        c["row_id"] = f"r{i:04d}-{c['sha256'][:10]}-p{c['pages'][0]}-{c['pages'][-1]}"
        if a.extract:
            dest = out / f"{c['row_id']}.pdf"
            rng_ = f"{c['pages'][0]}-{c['pages'][-1]}"
            subprocess.run(["qpdf", "--empty", "--pages", c["doc"], rng_, "--", str(dest)],
                           check=True, timeout=a.timeout, env=SAFE_ENV, capture_output=True)
            c["file"] = str(dest)
        print(json.dumps(c))
    return 0 if chosen else 1


if __name__ == "__main__":
    sys.exit(main())
