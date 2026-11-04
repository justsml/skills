#!/usr/bin/env python3
"""Preflight the tools a fool's gold build needs, and warn loudly about anything missing.

Run with the interpreter that will do the build (a venv's python if you use one):
  python3 "$FOOLS_GOLD_SKILL_DIR"/check_deps.py --targets pdf,docx,charts

Each target has required groups (any one alternative satisfies a group, the
first listed is preferred) and optional extras. A group met only by a fallback
prints FALLBACK so the substitution is visible. A missing required group prints a WARN line with install hints
and makes the exit code 1. Never swap in a weaker tool silently: report it.
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys

# target -> {"required": [(group, [alternatives])], "optional": [...]}
# alternative syntax: bin:<executable>, py:<module>, node:<package>
TARGETS = {
    "pdf": {
        "required": [("PDF writer", ["py:reportlab", "bin:typst", "py:weasyprint"])],
        "optional": [("Office->PDF", ["bin:soffice", "bin:libreoffice"]), ("PDF edits", ["py:pypdf", "py:pikepdf"])],
    },
    "docx": {
        "required": [("DOCX writer", ["py:docx", "node:docx", "bin:soffice", "bin:libreoffice"])],
        "optional": [
            ("DOCX templating", ["py:docxtpl"]),
            ("DOCX -> HTML/Markdown check (mammoth)", ["py:mammoth", "node:mammoth"]),
            ("headless render + UNO API (LibreOffice/OpenOffice SDK)", ["bin:soffice", "bin:libreoffice"]),
            ("UNO bridge", ["py:uno", "bin:unoserver", "bin:unoconvert"]),
            ("format conversion", ["bin:pandoc"]),
        ],
    },
    "pptx": {
        "required": [("PPTX writer", ["py:pptx", "node:pptxgenjs", "bin:soffice", "bin:libreoffice"])],
        "optional": [("render slides to PDF/PNG", ["bin:soffice", "bin:libreoffice"]), ("UNO bridge", ["py:uno", "bin:unoserver"])],
    },
    "xlsx": {
        "required": [("XLSX writer", ["py:openpyxl", "py:xlsxwriter", "node:exceljs", "bin:soffice", "bin:libreoffice"])],
        "optional": [("native Excel charts", ["py:xlsxwriter", "py:openpyxl"]), ("formula recalculation", ["bin:soffice", "bin:libreoffice"])],
    },
    "odf": {
        "required": [("ODT/ODS/ODP writer", ["py:odf", "bin:soffice", "bin:libreoffice"])],
        "optional": [("UNO bridge", ["py:uno", "bin:unoserver"])],
    },
    "epub": {
        "required": [("EPUB packaging", ["bin:zip", "bin:pandoc", "py:ebooklib"])],
        "optional": [("EPUB validation", ["bin:epubcheck"])],
    },
    "html": {"required": [], "optional": [("conversion", ["bin:pandoc"]), ("HTML->PDF", ["py:weasyprint", "bin:chromium", "bin:google-chrome"])]},
    "scan": {
        "required": [("raster degrade", ["bin:magick", "bin:convert", "py:PIL"]), ("PDF->PNG", ["bin:pdftoppm", "bin:mutool"])],
        "optional": [("numeric noise", ["py:numpy"])],
    },
    "audio": {
        "required": [("read/probe (codec, duration, loudness, silences)", ["bin:ffprobe"]),
                     ("decode/mix/encode", ["bin:ffmpeg"]),
                     ("TTS", ["py:kokoro", "bin:piper", "py:piper", "py:TTS", "bin:espeak-ng"])],
        "optional": [("second TTS engine to vary production", ["bin:piper", "py:TTS", "bin:espeak-ng", "py:kokoro"]),
                     ("effects/resample", ["bin:sox"]), ("editing", ["py:pydub"]),
                     ("room acoustics/reverb", ["py:pyroomacoustics"]), ("noise mixing", ["py:numpy"]),
                     ("audio I/O", ["py:soundfile"]), ("diarization check", ["py:pyannote"])],
    },
    "video": {
        "required": [("read/probe", ["bin:ffprobe"]), ("decode/mux/encode", ["bin:ffmpeg"])],
        "optional": [("compositing", ["py:moviepy"]), ("frames", ["py:PIL", "py:matplotlib"]),
                     ("animated charts/diagrams", ["py:manim", "py:matplotlib"])],
    },
    "charts": {
        "required": [("plotting", ["py:matplotlib"])],
        "optional": [("statistical styles", ["py:seaborn"]), ("maps", ["py:cartopy", "py:shapely"])],
    },
    "diagrams": {
        "required": [("diagram renderer", ["bin:dot", "bin:mmdc", "bin:plantuml"])],
        "optional": [("graph layouts", ["py:networkx"])],
    },
    "math": {"required": [("typesetting", ["bin:typst", "bin:pdflatex", "bin:xelatex", "py:matplotlib"])], "optional": []},
    "forms": {
        "required": [("form fields", ["py:reportlab"])],
        "optional": [("QR", ["py:qrcode"]), ("barcodes", ["py:barcode"])],
    },
    "pdfvariants": {
        "required": [("PDF rewrite (version, linearize, xref, object streams)", ["bin:qpdf"])],
        "optional": [("re-distill (DPI, presets, JPEG QFactor)", ["bin:gs"]),
                     ("metadata/XMP stamping", ["py:pikepdf"])],
    },
    "verify": {
        "required": [("page render", ["bin:pdftoppm", "bin:mutool"]), ("text extract", ["bin:pdftotext", "bin:mutool"]),
                     ("page cut", ["bin:qpdf"])],
        "optional": [("OCR", ["bin:tesseract"]), ("transcription", ["bin:whisper-cli", "py:faster_whisper", "py:whisper"]),
                     ("DOCX text check (mammoth)", ["py:mammoth", "node:mammoth"])],
    },
}

# "uv pip install X" assumes an active venv; without uv use `python3 -m venv <dir> && <dir>/bin/pip install X`.
HINTS = {
    "py:reportlab": "uv pip install reportlab", "py:docx": "uv pip install python-docx",
    "py:docxtpl": "uv pip install docxtpl", "py:mammoth": "uv pip install mammoth",
    "py:pptx": "uv pip install python-pptx", "py:openpyxl": "uv pip install openpyxl",
    "py:xlsxwriter": "uv pip install XlsxWriter", "py:odf": "uv pip install odfpy",
    "py:ebooklib": "uv pip install EbookLib", "py:weasyprint": "uv pip install weasyprint",
    "py:PIL": "uv pip install pillow", "py:numpy": "uv pip install numpy",
    "py:matplotlib": "uv pip install matplotlib", "py:seaborn": "uv pip install seaborn",
    "py:networkx": "uv pip install networkx", "py:qrcode": "uv pip install qrcode",
    "py:barcode": "uv pip install python-barcode", "py:pypdf": "uv pip install pypdf",
    "py:pikepdf": "uv pip install pikepdf", "bin:gs": "pacman -S ghostscript | apt install ghostscript",
    "py:faster_whisper": "uv pip install faster-whisper", "py:kokoro": "uv pip install kokoro",
    "py:piper": "uv pip install piper-tts", "py:TTS": "uv pip install coqui-tts",
    "py:pydub": "uv pip install pydub", "py:pyroomacoustics": "uv pip install pyroomacoustics",
    "py:soundfile": "uv pip install soundfile", "py:pyannote": "uv pip install pyannote.audio",
    "py:moviepy": "uv pip install moviepy", "py:manim": "uv pip install manim",
    "bin:sox": "pacman -S sox | apt install sox", "bin:ffprobe": "ships with ffmpeg",
    "bin:piper": "pacman -S piper-tts-bin (AUR) | download from github.com/rhasspy/piper", "py:uno": "ships with LibreOffice (python3-uno / libreoffice-sdk package)",
    "bin:unoserver": "uv pip install unoserver (needs LibreOffice)",
    "node:docx": "npm i docx", "node:mammoth": "npm i mammoth", "node:pptxgenjs": "npm i pptxgenjs",
    "node:exceljs": "npm i exceljs", "bin:mmdc": "npm i -g @mermaid-js/mermaid-cli",
    "bin:soffice": "pacman -S libreoffice-fresh | apt install libreoffice", "bin:libreoffice": "see soffice",
    "bin:typst": "pacman -S typst | cargo install typst-cli", "bin:pandoc": "pacman -S pandoc | apt install pandoc",
    "bin:dot": "pacman -S graphviz | apt install graphviz", "bin:ffmpeg": "pacman -S ffmpeg | apt install ffmpeg",
    "bin:espeak-ng": "pacman -S espeak-ng | apt install espeak-ng", "bin:tesseract": "pacman -S tesseract | apt install tesseract-ocr",
    "bin:pdftoppm": "poppler (pacman -S poppler | apt install poppler-utils)", "bin:pdftotext": "poppler",
    "bin:mutool": "pacman -S mupdf-tools | apt install mupdf-tools", "bin:qpdf": "pacman -S qpdf | apt install qpdf",
    "bin:magick": "pacman -S imagemagick | apt install imagemagick", "bin:zip": "pacman -S zip | apt install zip",
}


def node_has(pkg):
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", f"require.resolve({json.dumps(pkg)})"], capture_output=True, timeout=20)
    return r.returncode == 0


# Install planning ---------------------------------------------------------
CACHE = "~/.cache/fools-gold"
# conda-forge package per binary: installs without root via micromamba into the user cache.
CONDA = {
    "bin:ffmpeg": "ffmpeg", "bin:ffprobe": "ffmpeg", "bin:pdftoppm": "poppler", "bin:pdftotext": "poppler",
    "bin:qpdf": "qpdf", "bin:mutool": "mupdf", "bin:tesseract": "tesseract", "bin:magick": "imagemagick",
    "bin:convert": "imagemagick", "bin:dot": "graphviz", "bin:pandoc": "pandoc", "bin:sox": "sox",
    "bin:espeak-ng": "espeak-ng", "bin:gs": "ghostscript", "bin:typst": "typst", "bin:zip": "zip",
    "bin:pdflatex": "texlive-core", "bin:xelatex": "texlive-core", "bin:plantuml": "plantuml",
    "bin:epubcheck": "epubcheck",
}
# Binaries with a better user-mode route than conda.
USER_ROUTES = {
    "bin:soffice": "LibreOffice AppImage (official): download from https://www.libreoffice.org/download/appimage/ "
                   "into ~/.local/opt, chmod +x, symlink as ~/.local/bin/soffice",
    "bin:libreoffice": "see soffice",
    "bin:piper": "release tarball from https://github.com/rhasspy/piper/releases, extract to ~/.local/opt/piper, "
                 "symlink ~/.local/bin/piper (or pip install piper-tts into the venv)",
    "bin:mmdc": f"npm install --prefix {CACHE}/node @mermaid-js/mermaid-cli; add {CACHE}/node/node_modules/.bin to PATH",
    "bin:whisper-cli": "build whisper.cpp in ~/.local/opt (cmake, no root) or pip install faster-whisper into the venv",
    "bin:unoserver": "pip install unoserver into a venv created with --system-site-packages (needs LibreOffice's uno)",
    "bin:chromium": "pip install playwright into the venv, then playwright install chromium (user cache)",
}
SYSTEM = {  # alt -> {manager: package}
    "bin:ffmpeg": "ffmpeg", "bin:ffprobe": "ffmpeg", "bin:pdftoppm": {"pacman": "poppler", "apt": "poppler-utils", "dnf": "poppler-utils", "brew": "poppler"},
    "bin:pdftotext": {"pacman": "poppler", "apt": "poppler-utils", "dnf": "poppler-utils", "brew": "poppler"},
    "bin:qpdf": "qpdf", "bin:mutool": {"pacman": "mupdf-tools", "apt": "mupdf-tools", "dnf": "mupdf", "brew": "mupdf-tools"},
    "bin:tesseract": {"pacman": "tesseract tesseract-data-eng", "apt": "tesseract-ocr", "dnf": "tesseract", "brew": "tesseract"},
    "bin:magick": "imagemagick", "bin:convert": "imagemagick", "bin:dot": "graphviz", "bin:pandoc": "pandoc",
    "bin:sox": "sox", "bin:espeak-ng": "espeak-ng", "bin:gs": "ghostscript", "bin:typst": "typst", "bin:zip": "zip",
    "bin:soffice": {"pacman": "libreoffice-fresh", "apt": "libreoffice", "dnf": "libreoffice", "brew": "--cask libreoffice"},
    "bin:libreoffice": {"pacman": "libreoffice-fresh", "apt": "libreoffice", "dnf": "libreoffice", "brew": "--cask libreoffice"},
    "py:uno": {"pacman": "libreoffice-fresh", "apt": "python3-uno", "dnf": "libreoffice-pyuno", "brew": "--cask libreoffice"},
    "bin:pdflatex": {"pacman": "texlive-basic texlive-latexextra", "apt": "texlive-latex-extra", "dnf": "texlive-scheme-medium", "brew": "--cask mactex-no-gui"},
    "bin:plantuml": "plantuml", "bin:epubcheck": "epubcheck",
}
# Proprietary families and metric-compatible free substitutes (same advance widths, so layout holds).
FONT_SUBSTITUTES = {
    "calibri": "Carlito", "cambria": "Caladea", "arial": "Liberation Sans", "helvetica": "Liberation Sans",
    "times new roman": "Liberation Serif", "times": "Liberation Serif", "courier new": "Liberation Mono",
    "georgia": "Gelasio", "segoe ui": "Selawik", "arial narrow": "Liberation Sans Narrow",
}
FONT_PACKAGES = {
    "Carlito": {"pacman": "ttf-carlito", "apt": "fonts-crosextra-carlito", "dnf": "google-carlito-fonts"},
    "Caladea": {"pacman": "ttf-caladea", "apt": "fonts-crosextra-caladea", "dnf": "google-caladea-fonts"},
    "Liberation Sans": {"pacman": "ttf-liberation", "apt": "fonts-liberation2", "dnf": "liberation-fonts"},
    "Liberation Serif": {"pacman": "ttf-liberation", "apt": "fonts-liberation2", "dnf": "liberation-fonts"},
    "Liberation Mono": {"pacman": "ttf-liberation", "apt": "fonts-liberation2", "dnf": "liberation-fonts"},
}


def package_manager():
    for mgr in ("pacman", "apt", "dnf", "brew"):
        if shutil.which(mgr if mgr != "apt" else "apt-get"):
            return mgr
    return None


def font_installed(family):
    if not shutil.which("fc-list"):
        return None
    out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True, timeout=30).stdout.lower()
    return family.lower() in out


# Rough installed sizes in MB (packages plus typical dependencies), used to check disk space first.
SIZE_MB = {
    "reportlab": 15, "matplotlib": 80, "python-docx": 5, "docxtpl": 10, "mammoth": 3, "python-pptx": 10,
    "openpyxl": 10, "XlsxWriter": 5, "odfpy": 3, "EbookLib": 3, "weasyprint": 40, "pillow": 15, "numpy": 60,
    "seaborn": 80, "networkx": 20, "qrcode": 2, "python-barcode": 2, "pypdf": 5, "pikepdf": 25,
    "kokoro": 2500, "coqui-tts": 3500, "piper-tts": 150, "faster-whisper": 700, "pyannote.audio": 3000,
    "pydub": 2, "pyroomacoustics": 60, "soundfile": 5, "moviepy": 80, "manim": 300, "unoserver": 2,
    # conda-forge
    "ffmpeg": 150, "poppler": 80, "qpdf": 15, "mupdf": 60, "tesseract": 120, "imagemagick": 150, "graphviz": 80,
    "pandoc": 250, "sox": 20, "espeak-ng": 30, "ghostscript": 80, "typst": 50, "zip": 2, "texlive-core": 800,
    "plantuml": 150, "epubcheck": 60, "_micromamba": 15, "_conda_base": 200,
    # other routes
    "bin:soffice": 400, "bin:libreoffice": 400, "bin:piper": 150, "bin:mmdc": 450, "bin:whisper-cli": 300,
    "bin:chromium": 450, "_font": 5, "_node_pkg": 30,
}
RESERVE_MB = 2048  # keep this much free after installing


def disk_check(plan_items):
    """Estimate install size per target filesystem and compare with free bytes and inodes."""
    need = {}
    home = os.path.expanduser("~")
    for root, mb in plan_items:
        path = os.path.expanduser(root)
        while not os.path.exists(path):
            path = os.path.dirname(path) or home
        st = os.statvfs(path)
        key = st.f_fsid or path
        entry = need.setdefault(key, {"path": path, "need_mb": 0,
                                      "free_mb": st.f_bavail * st.f_frsize // (1 << 20),
                                      "free_inodes": st.f_favail if st.f_files else None})
        entry["need_mb"] += mb
    report, ok = [], True
    for e in need.values():
        want = int(e["need_mb"] * 1.3) + RESERVE_MB  # headroom for pip/conda caches and unpacking
        inode_ok = e["free_inodes"] is None or e["free_inodes"] > e["need_mb"] * 40
        e_ok = e["free_mb"] >= want and inode_ok
        ok &= e_ok
        report.append({**e, "need_with_headroom_mb": want, "ok": e_ok, "inodes_ok": inode_ok})
    return ok, report


def install_plan(missing, fonts):
    mgr = package_manager()
    py = sorted({HINTS[x].split()[-1] for x in missing if x.startswith("py:") and x in HINTS and "uv pip" in HINTS[x]})
    node = sorted({x.split(":", 1)[1] for x in missing if x.startswith("node:")})
    conda = sorted({CONDA[x] for x in missing if x in CONDA})
    routes = sorted({f"{x}: {USER_ROUTES[x]}" for x in missing if x in USER_ROUTES})
    user = []
    if py:
        user.append(f"python3 -m venv --system-site-packages {CACHE}/venv && {CACHE}/venv/bin/pip install {' '.join(py)}")
    if node:
        user.append(f"npm install --prefix {CACHE}/node {' '.join(node)}  # then NODE_PATH={CACHE}/node/node_modules")
    if conda:
        if not shutil.which("micromamba"):
            user.append("# Install micromamba from its official distribution for the detected OS and architecture; "
                        "verify the download before extracting into a user-owned tools directory.")
        user.append(f"micromamba create -y -p {CACHE}/tools -c conda-forge {' '.join(conda)} && "
                    f"export PATH={CACHE}/tools/bin:$PATH")
    user += routes
    font_cmds, font_notes = [], []
    for fam in fonts:
        if font_installed(fam):
            continue
        sub = FONT_SUBSTITUTES.get(fam.lower())
        if sub and font_installed(sub):
            font_notes.append(f"{fam}: missing; metric-compatible {sub} is installed and will be used")
            continue
        font_notes.append(f"{fam}: missing" + (f"; metric-compatible substitute {sub}" if sub else
                          "; no free metric-compatible substitute known: ask the user for licensed font files, "
                          "or pick the closest free family and record it as a typography FALLBACK"))
        target = sub or fam
        user.append(f"# font {target}: copy licensed .ttf/.otf files into ~/.local/share/fonts && fc-cache -f")
        pkg = FONT_PACKAGES.get(target, {}).get(mgr)
        if pkg:
            font_cmds.append(pkg)
    sys_pkgs = set(font_cmds)
    for x in missing:
        spec = SYSTEM.get(x)
        if spec:
            sys_pkgs.add(spec if isinstance(spec, str) else spec.get(mgr, ""))
    sys_pkgs.discard("")
    verb = {"pacman": "sudo pacman -S --needed", "apt": "sudo apt-get install -y", "dnf": "sudo dnf install -y",
            "brew": "brew install"}.get(mgr)
    system = f"{verb} {' '.join(sorted(sys_pkgs))}" if verb and sys_pkgs else None
    sizes = [(f"{CACHE}/venv", sum(SIZE_MB.get(x, 100) for x in py)),
             (f"{CACHE}/node", SIZE_MB["_node_pkg"] * len(node)),
             (f"{CACHE}/tools", (SIZE_MB["_micromamba"] + SIZE_MB["_conda_base"] if conda else 0)
              + sum(SIZE_MB.get(x, 100) for x in conda)),
             ("~/.local/opt", sum(SIZE_MB.get(x, 200) for x in missing if x in USER_ROUTES and not x.startswith("bin:mmdc"))),
             ("~/.local/share/fonts", SIZE_MB["_font"] * len(fonts))]
    disk_ok, disk = disk_check([(root, mb) for root, mb in sizes if mb])
    total = sum(mb for _, mb in sizes)
    heavy = sorted((x for x in py + conda if SIZE_MB.get(x, 0) >= 1000), key=lambda x: -SIZE_MB[x])
    return {"package_manager": mgr, "user_mode": user, "system_command": system, "fonts": font_notes,
            "estimated_install_mb": total, "disk_ok": disk_ok, "disk": disk, "heavy": heavy}


def present(alt):
    kind, name = alt.split(":", 1)
    if kind == "bin":
        return shutil.which(name) is not None
    if kind == "py":
        try:
            return importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            return False
    if kind == "node":
        return node_has(name)
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--targets", default="verify", help=f"comma list from: {','.join(TARGETS)} (verify is always added)")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.add_argument("--plan", action="store_true",
                   help="print user-mode install steps for missing tools, then a copy-paste system command")
    p.add_argument("--with-optional", action="store_true", help="include missing optional tools in the plan")
    p.add_argument("--fonts", default="", help="comma list of font families the build needs, e.g. 'Calibri,Arial'")
    a = p.parse_args()
    targets = [t.strip() for t in a.targets.split(",") if t.strip()]
    unknown = [t for t in targets if t not in TARGETS]
    if unknown:
        print(f"unknown targets: {unknown}", file=sys.stderr)
        return 2
    if "verify" not in targets:
        targets.append("verify")

    report, missing_required = [], 0
    for t in targets:
        for level in ("required", "optional"):
            for group, alts in TARGETS[t][level]:
                found = [x for x in alts if present(x)]
                ok = bool(found)
                if level == "required" and not ok:
                    missing_required += 1
                fallback = ok and found[0] != alts[0]
                report.append({"target": t, "level": level, "group": group, "ok": ok, "using": found[:1],
                               "fallback": fallback, "preferred": alts[0],
                               "alternatives": alts,
                               "hints": [] if ok else [f"{x}: {HINTS[x]}" for x in alts if x in HINTS]})

    fonts = [f.strip() for f in a.fonts.split(",") if f.strip()]
    to_install = sorted({r["alternatives"][0] for r in report
                         if (r["level"] == "required" and (not r["ok"] or r["fallback"]))
                         or (a.with_optional and r["level"] == "optional" and not r["ok"])})
    plan = install_plan(to_install, fonts) if (a.plan or fonts) else None
    if plan:
        missing_required += sum(1 for n in plan["fonts"] if "is installed and will be used" not in n)
        missing_required += 0 if plan["disk_ok"] else 1
    if a.json:
        print(json.dumps({"python": sys.executable, "missing_required": missing_required, "checks": report,
                          "plan": plan}, indent=2))
    else:
        print(f"python: {sys.executable}")
        for r in report:
            if r["ok"] and r["fallback"] and r["level"] == "required":
                hint = HINTS.get(r["preferred"], r["preferred"])
                print(f"FALLBACK {r['target']}: {r['group']} via {r['using'][0]}; preferred {r['preferred']} ({hint})")
            elif r["ok"]:
                print(f"  ok    {r['target']:<8} {r['group']}: {r['using'][0]}")
            elif r["level"] == "required":
                print(f"WARN  REQUIRED {r['target']}: {r['group']} missing. Install one of:")
                for h in r["hints"] or r["alternatives"]:
                    print(f"        {h}")
            else:
                print(f"  note  {r['target']:<8} optional {r['group']} unavailable ({', '.join(r['alternatives'])})")
        if missing_required:
            print(f"WARN  {missing_required} required tool group(s) or font(s) missing. Install them or tell the user "
                  "which outputs are blocked; do not substitute a weaker tool silently.")
        if plan:
            for n in plan["fonts"]:
                print(f"font  {n}")
            if plan["estimated_install_mb"]:
                print(f"\ndisk  estimated install ~{plan['estimated_install_mb']} MB"
                      + (f"; heavy: {', '.join(f'{h} (~{SIZE_MB[h] // 1000} GB)' for h in plan['heavy'])}" if plan["heavy"] else ""))
                for d in plan["disk"]:
                    flag = "ok  " if d["ok"] else "WARN"
                    print(f"{flag}  {d['path']}: need ~{d['need_with_headroom_mb']} MB incl. headroom and "
                          f"{RESERVE_MB} MB reserve, free {d['free_mb']} MB"
                          + ("" if d["inodes_ok"] else ", low on inodes"))
                if not plan["disk_ok"]:
                    print("WARN  not enough disk space: do not install. Prefer lighter alternatives (e.g. piper or "
                          "espeak-ng instead of torch-based TTS), clear your own caches, or ask the user where to install.")
            if plan["user_mode"] and plan["disk_ok"]:
                print("\nUser-mode install (no sudo), try these first:")
                for c in plan["user_mode"]:
                    print(f"  {c}")
            if plan["system_command"]:
                print("\nIf user-mode is not practical, ask the user to run (copy-paste):")
                print(f"  {plan['system_command']}")
    return 1 if missing_required else 0


if __name__ == "__main__":
    sys.exit(main())
