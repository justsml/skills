#!/usr/bin/env python3
"""Pixel-diff a candidate document against its source, page by page, to steer a clone.

Renders both PDFs to grayscale at the same pixel size (pdftoppm) and reports,
per page, the mean absolute difference, the share of changed pixels, and the
grid tiles where the differences concentrate, so the next iteration knows
where to look. Convert Office files first (`soffice --headless --convert-to pdf`)
and images with `magick in.png out.pdf`.

Stdlib + poppler only; run with `python3 -I`. Exit 0 when every page is within
--target, 1 otherwise, 2 on usage errors. This is a visual diagnostic only:
small changed values may pass; verify semantic content and native structure separately.
"""
import argparse
import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Preserve configured tool and scratch paths without forwarding credentials.
SAFE_ENV = {key: os.environ[key] for key in
            ("PATH", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR")
            if key in os.environ}
SAFE_ENV.setdefault("PATH", os.defpath)
SAFE_ENV.update({"LANG": "C", "LC_ALL": "C"})


def pages(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, env=SAFE_ENV,
                         timeout=60, check=True).stdout
    return int(next(l.split()[1] for l in out.splitlines() if l.startswith("Pages:")))


def render(pdf, page, w, h, out_prefix):
    cmd = ["pdftoppm", "-gray", "-f", str(page), "-l", str(page), "-singlefile"]
    cmd += ["-scale-to-x", str(w), "-scale-to-y", str(h)] if w else ["-r", "72"]
    subprocess.run(cmd + [str(pdf), str(out_prefix)], check=True, timeout=120, env=SAFE_ENV, capture_output=True)
    return read_pgm(Path(str(out_prefix) + ".pgm"))


def read_pgm(path):
    data = path.read_bytes()
    # Binary PGM: P5 <w> <h> <maxval> then raw bytes (comments are not emitted by pdftoppm).
    parts, idx = [], 0
    while len(parts) < 4:
        while data[idx:idx + 1].isspace():
            idx += 1
        start = idx
        while not data[idx:idx + 1].isspace():
            idx += 1
        parts.append(data[start:idx])
    if parts[0] != b"P5":
        raise ValueError("not a binary PGM")
    w, h = int(parts[1]), int(parts[2])
    return w, h, data[idx + 1: idx + 1 + w * h]


def write_pgm(path, w, h, pixels):
    path.write_bytes(b"P5\n%d %d\n255\n" % (w, h) + bytes(pixels))


def compare(a, b, w, h, grid, threshold):
    tiles = [[0, 0] for _ in range(grid * grid)]  # [sum diff, changed count]
    total, changed = 0, 0
    diff = bytearray(w * h)
    tw, th = max(1, w // grid), max(1, h // grid)
    for y in range(h):
        row = y * w
        ty = min(grid - 1, y // th) * grid
        for x in range(w):
            d = abs(a[row + x] - b[row + x])
            if d:
                total += d
                t = tiles[ty + min(grid - 1, x // tw)]
                t[0] += d
                if d > threshold:
                    changed += 1
                    t[1] += 1
            diff[row + x] = 255 - d
    n = w * h
    tile_px = tw * th
    hot = sorted(
        ({"tile": [i % grid, i // grid], "x_frac": round((i % grid) / grid, 3), "y_frac": round((i // grid) / grid, 3),
          "changed": round(c / tile_px, 3)} for i, (s, c) in enumerate(tiles) if c),
        key=lambda t: -t["changed"])
    return total / (255 * n), changed / n, hot, diff


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("source", help="source PDF")
    p.add_argument("candidate", help="candidate PDF")
    p.add_argument("--width", type=int, default=850, help="render width in pixels (height keeps the source aspect)")
    p.add_argument("--grid", type=int, default=8, help="tiles per side for hot-spot reporting")
    p.add_argument("--threshold", type=int, default=48, help="per-pixel gray difference that counts as changed")
    p.add_argument("--target", type=float, default=0.02, help="max changed-pixel share per page to pass")
    p.add_argument("--diff-dir", help="write per-page diff images (dark = different) here")
    p.add_argument("--top", type=int, default=5, help="hot tiles to report per page")
    a = p.parse_args()

    ns, nc = pages(a.source), pages(a.candidate)
    report = {"source_pages": ns, "candidate_pages": nc, "pages": []}
    with tempfile.TemporaryDirectory(dir=None) as tmp:
        tmp = Path(tmp)
        for i in range(1, min(ns, nc) + 1):
            # Render the source at --width, then force the candidate to the same pixel size.
            sw, sh, _ = render(a.source, i, 0, 0, tmp / "probe")
            w, h = a.width, max(1, round(a.width * sh / sw))
            _, _, src = render(a.source, i, w, h, tmp / "s")
            cw, ch, cand = render(a.candidate, i, w, h, tmp / "c")
            if (cw, ch) != (w, h):
                report["pages"].append({"page": i, "error": f"size mismatch {cw}x{ch} vs {w}x{h}"})
                continue
            mad, changed, hot, diff = compare(src, cand, w, h, a.grid, a.threshold)
            entry = {"page": i, "mean_abs_diff": round(mad, 4), "changed": round(changed, 4),
                     "pass": changed <= a.target, "hot_tiles": hot[: a.top]}
            if a.diff_dir:
                out = Path(a.diff_dir)
                out.mkdir(parents=True, exist_ok=True)
                write_pgm(out / f"diff-p{i:03d}.pgm", w, h, diff)
                entry["diff_image"] = str(out / f"diff-p{i:03d}.pgm")
            report["pages"].append(entry)
    scored = [pg for pg in report["pages"] if "changed" in pg]
    report["worst_page"] = max(scored, key=lambda pg: pg["changed"])["page"] if scored else None
    report["mean_changed"] = round(sum(pg["changed"] for pg in scored) / len(scored), 4) if scored else None
    report["pass"] = ns == nc and bool(scored) and all(pg.get("pass") for pg in report["pages"])
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
