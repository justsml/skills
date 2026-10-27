#!/usr/bin/env python3
"""Write one visible document as many PDF file variants (version, Fast Web View, xref, images, metadata).

Each variant runs three passes:
  1. Ghostscript (optional): re-distill at a PDF compatibility level, with image
     downsampling (DPI), JPEG QFactor and an export preset (/screen /ebook /printer /prepress).
  2. Metadata stamp (pikepdf, optional): set Info and XMP to a prescribed profile,
     only as an explicit metadata test factor; preserve actual production history
     in the manifest. Do not imply that a stamped producer generated the file.
  3. qpdf: header version, linearization (Fast Web View), object streams and
     xref streams on or off, stream compression level.

  pdf_variants.py base.pdf --out variants/ --presets all
  pdf_variants.py base.pdf --out variants/ --matrix 12 --seed 3 --meta meta.json

meta.json: {"Producer": "...", "Creator": "...", "Title": "...", "Author": "...",
            "CreationDate": "D:20240314091502-05'00'", "ModDate": "...",
            "xmp": {"xmp:CreatorTool": "...", "pdf:Producer": "..."}, "strip_xmp": false}

Output: variants/*.pdf plus variants/variants.jsonl with the parameters,
warnings and a file-profile summary for each one. Run with `python3 -I` from
the build venv; a missing gs or pikepdf is reported per variant, never skipped silently.
"""
import argparse
import os
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Preserve configured tool and scratch paths without forwarding credentials.
SAFE_ENV = {key: os.environ[key] for key in
            ("PATH", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR")
            if key in os.environ}
SAFE_ENV.setdefault("PATH", os.defpath)
SAFE_ENV.update({"LANG": "C", "LC_ALL": "C"})

# Approximations of common export choices. When a source profile exists, it wins.
PRESETS = {
    "legacy-1.3":         {"version": "1.3", "gs": True, "objstm": "disable"},
    "screen-1.4":         {"version": "1.4", "gs": True, "pdfsettings": "/screen", "objstm": "disable"},
    "ebook-1.5":          {"version": "1.5", "gs": True, "pdfsettings": "/ebook", "objstm": "generate"},
    "web-1.6-linearized": {"version": "1.6", "linearize": True, "objstm": "generate"},
    "print-1.7":          {"version": "1.7", "gs": True, "pdfsettings": "/printer", "objstm": "generate"},
    "prepress-1.7":       {"version": "1.7", "gs": True, "pdfsettings": "/prepress", "objstm": "disable"},
    "dpi96-1.4":          {"version": "1.4", "gs": True, "dpi": 96, "qfactor": 0.76, "objstm": "disable"},
    "dpi200-1.6-web":     {"version": "1.6", "gs": True, "dpi": 200, "linearize": True, "objstm": "generate"},
    "uncompressed-1.4":   {"version": "1.4", "compress": False, "objstm": "disable"},
    "pdf-2.0":            {"version": "2.0", "objstm": "generate"},
}
AXES = {
    "version": ["1.3", "1.4", "1.5", "1.6", "1.7", "2.0"],
    "linearize": [False, True],
    "objstm": ["disable", "generate"],
    "pdfsettings": [None, "/screen", "/ebook", "/printer", "/prepress"],
    "dpi": [None, 72, 96, 150, 200, 300],
    "qfactor": [None, 0.15, 0.4, 0.76, 1.3],
    "compression_level": [None, 1, 6, 9],
}


def run(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, env=SAFE_ENV)


def gs_pass(src, dst, v):
    if not shutil.which("gs"):
        return "gs missing: version/DPI/preset re-distill skipped"
    cmd = ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite",
           f"-dCompatibilityLevel={min(float(v['version']), 1.7) if v['version'] != '2.0' else 2.0}"]
    if v.get("pdfsettings"):
        cmd.append(f"-dPDFSETTINGS={v['pdfsettings']}")
    if v.get("dpi"):
        d = v["dpi"]
        cmd += ["-dDownsampleColorImages=true", "-dDownsampleGrayImages=true", "-dDownsampleMonoImages=true",
                f"-dColorImageResolution={d}", f"-dGrayImageResolution={d}", f"-dMonoImageResolution={d * 2}",
                "-dColorImageDownsampleThreshold=1.0", "-dGrayImageDownsampleThreshold=1.0"]
    post = []
    if v.get("qfactor"):
        q = v["qfactor"]
        cmd += ["-dAutoFilterColorImages=false", "-dColorImageFilter=/DCTEncode",
                "-dAutoFilterGrayImages=false", "-dGrayImageFilter=/DCTEncode"]
        post = ["-c", f"<< /ColorImageDict << /QFactor {q} /Blend 1 /HSamples [2 1 1 2] /VSamples [2 1 1 2] >> "
                      f"/GrayImageDict << /QFactor {q} /Blend 1 /HSamples [2 1 1 2] /VSamples [2 1 1 2] >> >> "
                      "setdistillerparams", "-f"]
    r = run(cmd + [f"-sOutputFile={dst}"] + post + [str(src)])
    if r.returncode:
        return f"gs failed ({r.returncode}): {r.stderr.decode('utf-8', 'replace')[:200]}"
    return None


def stamp(src, dst, meta):
    try:
        import pikepdf
    except ImportError:
        return "pikepdf missing: metadata not stamped (a gs pass leaves 'GPL Ghostscript' as Producer)"
    with pikepdf.open(src) as pdf:
        info = pdf.docinfo
        for k in ("Title", "Author", "Subject", "Keywords", "Creator", "Producer", "CreationDate", "ModDate"):
            if k in meta:
                if meta[k] is None:
                    if f"/{k}" in info:
                        del info[f"/{k}"]
                else:
                    info[f"/{k}"] = pikepdf.String(meta[k])
        if meta.get("strip_xmp"):
            if "/Metadata" in pdf.Root:
                del pdf.Root["/Metadata"]
        elif meta.get("xmp"):
            with pdf.open_metadata(set_pikepdf_as_editor=False, update_docinfo=False) as m:
                for k, val in meta["xmp"].items():
                    m[k] = val
        pdf.save(dst)
    return None


def qpdf_pass(src, dst, v):
    cmd = ["qpdf", str(src), f"--object-streams={v.get('objstm', 'preserve')}"]
    if float(v["version"]) < 1.5:
        cmd[-1] = "--object-streams=disable"  # object and xref streams arrived in PDF 1.5
    cmd.append(f"--force-version={v['version']}")
    if v.get("linearize"):
        cmd.append("--linearize")
    if v.get("compress") is False:
        cmd += ["--compress-streams=n", "--decode-level=generalized"]
    elif v.get("compression_level"):
        cmd += ["--recompress-flate", f"--compression-level={v['compression_level']}"]
    r = run(cmd + [str(dst)])
    if r.returncode not in (0, 3):  # 3 = succeeded with warnings
        return f"qpdf failed ({r.returncode}): {r.stderr.decode('utf-8', 'replace')[:200]}"
    return "qpdf warnings: " + r.stderr.decode("utf-8", "replace")[:160] if r.returncode == 3 else None


def summarize(pdf):
    r = run([sys.executable, "-I", str(HERE / "file_profile.py"), "profile", str(pdf)])
    if r.returncode:
        return {"error": "profile failed"}
    p = json.loads(r.stdout)
    s = p["structure"]
    return {"header_version": s["header_version"], "linearized": s["linearized"],
            "xref": "stream" if s["xref_stream"] else "table", "object_streams": s["object_streams"],
            "size_bytes": s["size_bytes"], "producer": p["docinfo"]["Producer"], "xmp": p["xmp"]["present"],
            "image_encodings": p["images"]["encodings"], "ppi_median": p["images"]["ppi_median"],
            "jpeg_quality": p["jpeg"].get("quality_median")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base", help="base PDF (visible content to keep)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--presets", default="", help="comma list of preset names, or 'all'")
    ap.add_argument("--matrix", type=int, default=0, help="also draw N random combinations from the axes")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--meta", help="metadata profile JSON to stamp on every variant")
    ap.add_argument("--list", action="store_true", help="print presets and axes, then exit")
    a = ap.parse_args()
    if a.list:
        print(json.dumps({"presets": PRESETS, "axes": AXES}, indent=2))
        return 0

    chosen = []
    names = list(PRESETS) if a.presets == "all" else [n for n in a.presets.split(",") if n]
    for n in names:
        if n not in PRESETS:
            print(f"unknown preset {n}", file=sys.stderr)
            return 2
        chosen.append((n, dict(PRESETS[n])))
    rng = random.Random(a.seed)
    for i in range(a.matrix):
        v = {k: rng.choice(vals) for k, vals in AXES.items()}
        v["gs"] = bool(v["pdfsettings"] or v["dpi"] or v["qfactor"]) or rng.random() < 0.3
        chosen.append((f"mx{i:02d}", v))
    if not chosen:
        print("choose --presets and/or --matrix", file=sys.stderr)
        return 2

    meta = json.load(open(a.meta)) if a.meta else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    work = out / ".work"
    work.mkdir(exist_ok=True)
    rows, failed = [], 0
    with open(out / "variants.jsonl", "w") as log:
        for name, v in chosen:
            warnings, cur = [], Path(a.base)
            if v.get("gs"):
                nxt = work / f"{name}.gs.pdf"
                w = gs_pass(cur, nxt, v)
                if w:
                    warnings.append(w)
                else:
                    cur = nxt
            if meta:
                nxt = work / f"{name}.meta.pdf"
                w = stamp(cur, nxt, meta)
                if w:
                    warnings.append(w)
                else:
                    cur = nxt
            dst = out / f"{Path(a.base).stem}.{name}.pdf"
            w = qpdf_pass(cur, dst, v)
            if w:
                warnings.append(w)
            ok = dst.exists()
            failed += not ok
            row = {"variant": name, "file": str(dst) if ok else None, "params": v, "warnings": warnings,
                   "profile": summarize(dst) if ok else None}
            rows.append(row)
            log.write(json.dumps(row) + "\n")
            flag = "WARN " if warnings else "ok   "
            print(f"{flag}{name:<20} {row['profile'] and row['profile'].get('header_version')} "
                  f"lin={row['profile'] and row['profile'].get('linearized')} "
                  f"ppi={row['profile'] and row['profile'].get('ppi_median')} "
                  f"{'; '.join(warnings)[:120]}", file=sys.stderr)
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({"variants": len(rows), "failed": failed, "log": str(out / "variants.jsonl")}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
