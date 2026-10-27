#!/usr/bin/env python3
"""Profile a PDF's invisible file-level traits, or score a candidate against a target profile.

  file_profile.py profile source.pdf > profile.json
  file_profile.py profile --handoff source.pdf > handoff-profile.json
  file_profile.py compare profile.json candidate.pdf > file-misses.json   # for score.py --misses

A profile records what a forensic look at the file would reveal:
- structure: PDF version, linearization (Fast Web View), xref table or stream,
  object streams, incremental updates, encryption, file size
- metadata: Info keys, producer/creator tools, date format and timezone, XMP
  toolkit, PDF/A claims, tagging
- fonts: types, embedding, subsetting
- images: filters, bit depth, colour space, effective PPI, and JPEG internals
  (JFIF, Exif tags, ICC, Adobe marker, progressive or baseline, estimated quality)

Migration: the default profile is explicitly raw-dirty and MUST stay on the
dirty side, as must compare reports. All source strings are untrusted, including
tool names, fonts, namespace names, date forms and encryption diagnostics.
Use --handoff for a separately marked, conservative summary with source strings
omitted (no recognized-tool whitelist). Review even that summary before sharing:
lengths, counts and other structural traits can identify a source. Sanitization
is not a confidentiality proof. Keep the dirty profile for exact comparisons;
handoff profiles deliberately omit traits needed for those comparisons.

Stdlib + poppler (pdfinfo, pdffonts, pdfimages) + qpdf. Run with `python3 -I`.
Inputs are untrusted: every tool call has a timeout and a minimal environment.
Inspection is bounded, not exhaustive: raw scanning stops at MAX_SCAN bytes,
JPEG sampling at JPEG_SAMPLE images from the first 50 pages. No parser isolation
or confidentiality guarantee is provided by this command.
"""
import argparse
import os
import json
import math
import re
import statistics
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

# Preserve configured tool and scratch paths without forwarding credentials.
SAFE_ENV = {key: os.environ[key] for key in
            ("PATH", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR")
            if key in os.environ}
SAFE_ENV.setdefault("PATH", os.defpath)
SAFE_ENV.update({"LANG": "C", "LC_ALL": "C"})
MAX_SCAN = 256 << 20   # bytes read for raw structure scanning
JPEG_SAMPLE = 12       # embedded JPEGs inspected per file
CONTENT_FIELDS = {"Title", "Subject", "Keywords", "Author"}
OFFICE_TITLE = re.compile(r"^(Microsoft (?:Word|PowerPoint|Excel) - ).*?(\.\w{3,5})?$")


def run(cmd, timeout=120, ok_codes=(0,)):
    r = subprocess.run(cmd, capture_output=True, timeout=timeout, env=SAFE_ENV)
    if r.returncode not in ok_codes:
        raise subprocess.CalledProcessError(r.returncode, cmd, r.stdout, r.stderr)
    return r


def shape(value):
    """Describe a content-bearing string without its content."""
    if not value:
        return None
    m = OFFICE_TITLE.match(value)
    if m:
        return {"pattern": f"{m.group(1)}<name>{m.group(2) or ''}", "length": len(value)}
    words = value.split()
    case = ("upper" if value.isupper() else "lower" if value.islower()
            else "title" if all(w[:1].isupper() for w in words if w[:1].isalpha()) else "mixed")
    ext = re.search(r"\.(docx?|pptx?|xlsx?|indd|ai|psd|tex|odt|pages|key)\b", value, re.I)
    return {"length": len(value), "words": len(words), "case": case,
            "digits": any(c.isdigit() for c in value),
            "looks_like_filename": bool(ext) or bool(re.search(r"[_\\/]", value)),
            "extension": ext.group(0).lower() if ext else None}


def date_shape(value):
    # pdfinfo -rawdates gives D:YYYYMMDDHHmmSS+HH'mm' or similar; keep the form, not the instant.
    if not value:
        return None
    v = value.strip()
    tz = re.search(r"(Z|[+-]\d{2}'?\d{2}'?)$", v)
    digits = re.match(r"D?:?(\d+)", v)
    return {"prefix_D": v.startswith("D:"), "precision_digits": len(digits.group(1)) if digits else 0,
            "timezone": tz.group(1) if tz else None, "raw_form": re.sub(r"\d", "9", v)}


def pdfinfo(pdf):
    out = run(["pdfinfo", "-rawdates", str(pdf)]).stdout.decode("utf-8", "replace")
    info = {}
    for line in out.splitlines():
        k, _, v = line.partition(":")
        info[k.strip()] = v.strip()
    meta = run(["pdfinfo", "-meta", str(pdf)]).stdout.decode("utf-8", "replace")
    return info, meta


def xmp_profile(xml):
    if "<x:xmpmeta" not in xml and "<rdf:RDF" not in xml:
        return {"present": False}

    def grab(tag):
        m = re.search(rf"<{tag}>([^<]*)</{tag}>|{tag}=\"([^\"]*)\"", xml)
        return (m.group(1) or m.group(2)).strip() if m else None

    return {
        "present": True,
        "toolkit": grab("x:xmptk") or (re.search(r'x:xmptk="([^"]*)"', xml) or [None, None])[1],
        "creator_tool": grab("xmp:CreatorTool"),
        "producer": grab("pdf:Producer"),
        "pdfa": (grab("pdfaid:part") or "") + (grab("pdfaid:conformance") or "") or None,
        "pdfua": grab("pdfuaid:part"),
        "document_id": bool(grab("xmpMM:DocumentID")),
        "instance_id": bool(grab("xmpMM:InstanceID")),
        "history_entries": xml.count("<stEvt:action") + xml.count("stEvt:action="),
        "dc_format": grab("dc:format"),
        "namespaces": sorted(set(re.findall(r'xmlns:(\w+)=', xml))),
        "padding": "<?xpacket end=\"w\"?>" in xml,
    }


def raw_structure(pdf):
    data = Path(pdf).open("rb").read(MAX_SCAN)
    head = re.match(rb"%PDF-(\d\.\d)", data[:1024])
    return {
        "header_version": head.group(1).decode() if head else None,
        "binary_comment": bool(re.match(rb"%PDF-\d\.\d\r?\n%[\x80-\xff]{4}", data[:64])),
        "eol": "CRLF" if b"\r\n" in data[:64] else "CR" if b"\r" in data[:16] else "LF",
        "xref_table": len(re.findall(rb"(?m)^xref\s*$", data)),
        "xref_stream": len(re.findall(rb"/Type\s*/XRef\b", data)),
        "object_streams": len(re.findall(rb"/Type\s*/ObjStm\b", data)),
        "eof_markers": data.count(b"%%EOF"),
        "has_id": bool(re.search(rb"/ID\s*\[", data)),
        "catalog_version": (lambda m: m.group(1).decode() if m else None)(re.search(rb"/Version\s*/(\d\.\d)", data)),
        "javascript": bool(re.search(rb"/JavaScript\b|/JS\s*[(<]", data)),
        "embedded_files": bool(re.search(rb"/EmbeddedFiles\b", data)),
        "acroform": bool(re.search(rb"/AcroForm\b", data)),
        "optional_content": bool(re.search(rb"/OCProperties\b", data)),
        "page_labels": bool(re.search(rb"/PageLabels\b", data)),
        "outlines": bool(re.search(rb"/Outlines\b", data)),
        "struct_tree": bool(re.search(rb"/StructTreeRoot\b", data)),
        "output_intent": bool(re.search(rb"/OutputIntents\b", data)),
    }


def fonts(pdf):
    out = run(["pdffonts", str(pdf)]).stdout.decode("utf-8", "replace").splitlines()[2:]
    rows = []
    for line in out:
        parts = line.split()
        if len(parts) < 7:
            continue
        # name type... encoding emb sub uni objnum gen; the type can contain spaces.
        emb, sub, uni = parts[-5], parts[-4], parts[-3]
        name = parts[0]
        rows.append({"type": " ".join(parts[1:-6]), "encoding": parts[-6], "embedded": emb == "yes",
                     "subset": sub == "yes", "unicode": uni == "yes",
                     "subset_prefix": bool(re.match(r"^[A-Z]{6}\+", name)),
                     "family": re.sub(r"^[A-Z]{6}\+", "", name).split(",")[0].split("-")[0]})
    n = len(rows) or 1
    return {
        "count": len(rows),
        "types": dict(Counter(r["type"] for r in rows)),
        "encodings": dict(Counter(r["encoding"] for r in rows)),
        "embedded_share": round(sum(r["embedded"] for r in rows) / n, 2),
        "subset_share": round(sum(r["subset"] for r in rows) / n, 2),
        "unicode_share": round(sum(r["unicode"] for r in rows) / n, 2),
        "families": sorted({r["family"] for r in rows})[:30],
    }


def images(pdf):
    out = run(["pdfimages", "-list", str(pdf)]).stdout.decode("utf-8", "replace").splitlines()[2:]
    rows = []
    for line in out:
        p = line.split()
        if len(p) < 14 or p[2] not in ("image", "mask", "smask", "stencil"):
            continue
        try:
            rows.append({"kind": p[2], "w": int(p[3]), "h": int(p[4]), "color": p[5], "bpc": int(p[7]),
                         "enc": p[8], "interp": p[9] == "yes", "ppi": int(p[12]) if p[12].isdigit() else None})
        except ValueError:
            continue
    ppis = [r["ppi"] for r in rows if r["ppi"]]
    return {
        "count": sum(1 for r in rows if r["kind"] == "image"),
        "masks": sum(1 for r in rows if r["kind"] != "image"),
        "encodings": dict(Counter(r["enc"] for r in rows if r["kind"] == "image")),
        "colors": dict(Counter(r["color"] for r in rows if r["kind"] == "image")),
        "bpc": dict(Counter(str(r["bpc"]) for r in rows if r["kind"] == "image")),
        "ppi_median": int(statistics.median(ppis)) if ppis else None,
        "ppi_range": [min(ppis), max(ppis)] if ppis else None,
        "interpolate_share": round(sum(r["interp"] for r in rows) / len(rows), 2) if rows else None,
    }


# --- JPEG internals -------------------------------------------------------

STD_LUMA = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
            14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
            49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]
ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14,
          21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53,
          60, 61, 54, 47, 55, 62, 63]
EXIF_TAGS = {0x010F: "Make", 0x0110: "Model", 0x0131: "Software", 0x0132: "DateTime", 0x013B: "Artist",
             0x8298: "Copyright", 0x8769: "ExifIFD", 0x8825: "GPS"}


def ijg_quality(table):
    # Estimate the IJG quality factor that would produce this luminance table.
    natural = [0] * 64
    for i, z in enumerate(ZIGZAG):
        natural[z] = table[i]
    scales = [natural[i] * 100 / STD_LUMA[i] for i in range(64) if STD_LUMA[i]]
    s = statistics.median(scales)
    q = (200 - s) / 2 if s <= 100 else 5000 / s
    return max(1, min(100, round(q)))


def exif_ifd0(blob):
    out = {}
    if not blob.startswith(b"Exif\0\0") or len(blob) < 14:
        return out
    t = blob[6:]
    end = "<" if t[:2] == b"II" else ">"
    try:
        off = struct.unpack(end + "I", t[4:8])[0]
        n = struct.unpack(end + "H", t[off:off + 2])[0]
        for i in range(min(n, 64)):
            e = t[off + 2 + 12 * i: off + 14 + 12 * i]
            tag, typ, cnt = struct.unpack(end + "HHI", e[:8])
            name = EXIF_TAGS.get(tag)
            if not name:
                continue
            if name in ("GPS", "ExifIFD"):
                out[name] = True
            elif typ == 2:
                voff = struct.unpack(end + "I", e[8:12])[0] if cnt > 4 else None
                raw = t[voff:voff + cnt] if voff is not None else e[8:8 + cnt]
                out[name] = raw.rstrip(b"\0").decode("latin-1", "replace")
    except (struct.error, IndexError):
        pass
    return out


def jpeg_profile(data):
    p = {"jfif": None, "exif": False, "icc": False, "adobe": None, "photoshop": False, "xmp": False,
         "progressive": False, "quality": None, "subsampling": None, "exif_tags": {}}
    i = 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        if marker in (0xD9, 0xDA):
            break
        size = struct.unpack(">H", data[i + 2:i + 4])[0]
        seg = data[i + 4:i + 2 + size]
        if marker == 0xE0 and seg.startswith(b"JFIF\0"):
            p["jfif"] = {"version": f"{seg[5]}.{seg[6]:02d}", "units": seg[7],
                         "density": list(struct.unpack(">HH", seg[8:12]))}
        elif marker == 0xE1 and seg.startswith(b"Exif\0\0"):
            p["exif"] = True
            tags = exif_ifd0(seg)
            p["exif_tags"] = {k: (v if k in ("Make", "Model", "Software") else
                                  ("present" if v else None) if k not in ("DateTime",) else
                                  re.sub(r"\d", "9", v) if isinstance(v, str) else v)
                              for k, v in tags.items()}
        elif marker == 0xE1 and b"ns.adobe.com/xap" in seg[:64]:
            p["xmp"] = True
        elif marker == 0xE2 and seg.startswith(b"ICC_PROFILE"):
            p["icc"] = True
        elif marker == 0xED:
            p["photoshop"] = True
        elif marker == 0xEE and seg.startswith(b"Adobe"):
            p["adobe"] = {"transform": seg[11] if len(seg) > 11 else None}
        elif marker == 0xDB and p["quality"] is None and len(seg) >= 65 and seg[0] >> 4 == 0:
            p["quality"] = ijg_quality(list(seg[1:65]))
        elif marker in (0xC0, 0xC1, 0xC2):
            p["progressive"] = marker == 0xC2
            ncomp = seg[5]
            if ncomp >= 3:
                h, v = seg[7] >> 4, seg[7] & 15
                p["subsampling"] = {(2, 2): "4:2:0", (2, 1): "4:2:2", (1, 1): "4:4:4"}.get((h, v), f"{h}x{v}")
            else:
                p["subsampling"] = "gray"
        i += 2 + size
    return p


def jpegs(pdf):
    with tempfile.TemporaryDirectory() as tmp:
        run(["pdfimages", "-j", "-l", "50", str(pdf), str(Path(tmp) / "im")], timeout=180)
        files = sorted(Path(tmp).glob("*.jpg"))[:JPEG_SAMPLE]
        profs = [jpeg_profile(f.read_bytes()[:4 << 20]) for f in files]
    if not profs:
        return {"inspected": 0}
    n = len(profs)
    share = lambda key: round(sum(1 for x in profs if x[key]) / n, 2)
    tools = Counter(f"{x['exif_tags'].get('Make', '')} {x['exif_tags'].get('Model', '')} | {x['exif_tags'].get('Software', '')}".strip()
                    for x in profs if x["exif"])
    quals = [x["quality"] for x in profs if x["quality"]]
    return {
        "inspected": n,
        "jfif_share": round(sum(1 for x in profs if x["jfif"]) / n, 2),
        "jfif_versions": dict(Counter(x["jfif"]["version"] for x in profs if x["jfif"])),
        "exif_share": share("exif"),
        "exif_tools": dict(tools),
        "gps_present": any(x["exif_tags"].get("GPS") for x in profs),
        "icc_share": share("icc"),
        "adobe_share": round(sum(1 for x in profs if x["adobe"]) / n, 2),
        "photoshop_share": share("photoshop"),
        "xmp_share": share("xmp"),
        "progressive_share": share("progressive"),
        "quality_median": int(statistics.median(quals)) if quals else None,
        "subsampling": dict(Counter(x["subsampling"] for x in profs if x["subsampling"])),
    }


def profile(pdf):
    info, meta = pdfinfo(pdf)
    # Linearized (Fast Web View): pdfinfo's "Optimized", or a /Linearized dict in the first 1 KB.
    with open(pdf, "rb") as f:
        linear = info.get("Optimized") == "yes" or b"/Linearized" in f.read(1024)
    enc = run(["qpdf", "--show-encryption", str(pdf)], ok_codes=(0, 3)).stdout.decode("utf-8", "replace")
    size = Path(pdf).stat().st_size
    docinfo = {}
    for k in ("Title", "Subject", "Keywords", "Author", "Creator", "Producer", "CreationDate", "ModDate"):
        v = info.get(k)
        if k in CONTENT_FIELDS:
            docinfo[k] = shape(v)
        elif k.endswith("Date"):
            docinfo[k] = date_shape(v)
        else:
            docinfo[k] = v or None
    pages = int(info.get("Pages", "0") or 0)
    return {
        "profile_version": 2,
        "profile_kind": "raw-dirty",
        "sharing": "restricted: contains untrusted source strings; use profile --handoff and review before sharing",
        "structure": {**raw_structure(pdf), "pdfinfo_version": info.get("PDF version"), "linearized": linear,
                      "encrypted": not enc.startswith("File is not encrypted"),
                      "encryption": None if enc.startswith("File is not encrypted") else enc.splitlines()[:6],
                      "size_bytes": size, "bytes_per_page": size // max(1, pages)},
        "docinfo": docinfo,
        "xmp": xmp_profile(meta),
        "tagged": info.get("Tagged") == "yes",
        "pages": {"count": pages, "size": info.get("Page size"), "rotation": info.get("Page rot")},
        "fonts": fonts(pdf),
        "images": images(pdf),
        "jpeg": jpegs(pdf),
    }


def handoff_profile(raw):
    """Project only fixed field names, numeric traits and string shapes.

    No literal string from a PDF (including dictionary keys) is copied. This
    intentionally loses identity and exact metadata fidelity, and does not
    establish that the remaining numeric/structural information is non-sensitive.
    """
    def numeric(value):
        if value is None or type(value) in (bool, int):
            return value
        if type(value) is float and math.isfinite(value):
            return value
        return None

    def text_shape(value):
        if value is None:
            return None
        if isinstance(value, str):
            # Even purported version/date/format strings are never forwarded.
            return {"present": bool(value), "length": len(value)}
        if isinstance(value, dict):
            return {k: numeric(value.get(k)) for k in ("length", "words", "digits", "looks_like_filename")}
        return {"present": True}

    def metrics(section, fields):
        data = raw.get(section, {})
        return {k: numeric(data.get(k)) for k in fields}

    def collection_shape(value):
        # Source-defined names are dictionary keys in several dirty sections.
        if isinstance(value, dict):
            return {"distinct_count": len(value),
                    "total_count": sum(v for v in value.values() if type(v) is int and v >= 0)}
        return {"distinct_count": len(value) if isinstance(value, list) else 0}

    structure = metrics("structure", (
        "binary_comment", "xref_table", "xref_stream", "object_streams", "eof_markers", "has_id",
        "javascript", "embedded_files", "acroform", "optional_content", "page_labels", "outlines",
        "struct_tree", "output_intent", "linearized", "encrypted", "size_bytes", "bytes_per_page"))
    for field in ("header_version", "catalog_version", "pdfinfo_version", "eol"):
        structure[field] = text_shape(raw.get("structure", {}).get(field))
    # Restricted numeric syntax, not tool-name recognition. Never copy the text.
    for field in ("header_version", "catalog_version", "pdfinfo_version"):
        value = raw.get("structure", {}).get(field)
        if isinstance(value, str) and re.fullmatch(r"[12]\.[0-9]", value):
            structure[field] = [int(value[0]), int(value[2])]
    xmp = metrics("xmp", ("present", "document_id", "instance_id", "history_entries", "padding"))
    for field in ("toolkit", "creator_tool", "producer", "pdfa", "pdfua", "dc_format"):
        xmp[field] = text_shape(raw.get("xmp", {}).get(field))
    xmp["namespace_count"] = len(raw.get("xmp", {}).get("namespaces", []))
    font = metrics("fonts", ("count", "embedded_share", "subset_share", "unicode_share"))
    for field in ("types", "encodings", "families"):
        font[field] = collection_shape(raw.get("fonts", {}).get(field))
    image = metrics("images", ("count", "masks", "ppi_median", "interpolate_share"))
    for field in ("encodings", "colors", "bpc"):
        image[field] = collection_shape(raw.get("images", {}).get(field))
    jpeg = metrics("jpeg", ("inspected", "jfif_share", "exif_share", "gps_present", "icc_share", "adobe_share",
                             "photoshop_share", "xmp_share", "progressive_share", "quality_median"))
    for field in ("jfif_versions", "exif_tools", "subsampling"):
        jpeg[field] = collection_shape(raw.get("jpeg", {}).get(field))
    docinfo = {}
    for field in ("Title", "Subject", "Keywords", "Author", "Creator", "Producer"):
        docinfo[field] = text_shape(raw.get("docinfo", {}).get(field))
    for field in ("CreationDate", "ModDate"):
        value = raw.get("docinfo", {}).get(field)
        docinfo[field] = None if value is None else {
            "prefix_D": numeric(value.get("prefix_D")),
            "precision_digits": numeric(value.get("precision_digits")),
            "timezone_present": bool(value.get("timezone"))}
    pages = {"count": numeric(raw.get("pages", {}).get("count"))}
    page_size = raw.get("pages", {}).get("size")
    size_match = re.fullmatch(r"([0-9]{1,6}(?:\.[0-9]{1,6})?) x ([0-9]{1,6}(?:\.[0-9]{1,6})?) pts(?: \([^\n]*\))?",
                             page_size or "")
    pages["size_points"] = [float(x) for x in size_match.groups()] if size_match else None
    rotation = raw.get("pages", {}).get("rotation")
    pages["rotation_degrees"] = int(rotation) if rotation in ("0", "90", "180", "270") else None
    return {"profile_version": 2, "profile_kind": "sanitized-handoff",
            "sharing": "source strings omitted; structural information still requires dirty-side review before sharing",
            "comparison": "not an exact-comparison target; retain the raw-dirty profile",
            "structure": structure, "docinfo": docinfo, "xmp": xmp,
            "tagged": numeric(raw.get("tagged")),
            "pages": pages,
            "fonts": font, "images": image, "jpeg": jpeg}


# --- comparison ------------------------------------------------------------

def miss(sev, field, want, got):
    return {"category": "file", "severity": sev, "cause": "build", "where": f"file:{field}",
            "summary": f"{field}: want {json.dumps(want)[:80]}, got {json.dumps(got)[:80]}"}


def compare(target, cand):
    if target.get("profile_kind") == "sanitized-handoff" or cand.get("profile_kind") == "sanitized-handoff":
        raise ValueError("handoff profiles cannot verify exact traits; use a raw-dirty profile or source PDF")
    if target.get("profile_version") not in (1, 2) or cand.get("profile_version") not in (1, 2):
        raise ValueError("unsupported profile version")
    m = []
    ts, cs = target["structure"], cand["structure"]
    eq = lambda a, b: a == b

    checks = [
        ("high", "structure.encrypted", ts["encrypted"], cs["encrypted"], eq),
        ("medium", "structure.header_version", ts["header_version"], cs["header_version"], eq),
        ("medium", "structure.linearized", ts["linearized"], cs["linearized"], eq),
        ("medium", "structure.xref", "stream" if ts["xref_stream"] else "table", "stream" if cs["xref_stream"] else "table", eq),
        ("low", "structure.object_streams", bool(ts["object_streams"]), bool(cs["object_streams"]), eq),
        ("low", "structure.incremental_updates", ts["eof_markers"] > 1 + ts["linearized"],
         cs["eof_markers"] > 1 + cs["linearized"], eq),
        ("low", "structure.catalog_version", ts["catalog_version"], cs["catalog_version"], eq),
        ("low", "structure.has_id", ts["has_id"], cs["has_id"], eq),
        ("low", "structure.binary_comment", ts["binary_comment"], cs["binary_comment"], eq),
        ("medium", "structure.struct_tree", ts["struct_tree"], cs["struct_tree"], eq),
        ("high", "structure.javascript", ts["javascript"], cs["javascript"], eq),
        ("low", "structure.output_intent", ts["output_intent"], cs["output_intent"], eq),
        ("low", "structure.size_bytes", ts["size_bytes"], cs["size_bytes"], lambda a, b: 0.5 <= b / max(1, a) <= 2),
        ("medium", "docinfo.Producer", target["docinfo"]["Producer"], cand["docinfo"]["Producer"], eq),
        ("medium", "docinfo.Creator", target["docinfo"]["Creator"], cand["docinfo"]["Creator"], eq),
        ("medium", "xmp.present", target["xmp"]["present"], cand["xmp"]["present"], eq),
        ("high", "xmp.pdfa", target["xmp"].get("pdfa"), cand["xmp"].get("pdfa"), eq),
        ("low", "xmp.toolkit", target["xmp"].get("toolkit"), cand["xmp"].get("toolkit"), eq),
        ("low", "xmp.creator_tool", target["xmp"].get("creator_tool"), cand["xmp"].get("creator_tool"), eq),
        ("medium", "tagged", target["tagged"], cand["tagged"], eq),
        ("medium", "pages.size", target["pages"]["size"], cand["pages"]["size"], eq),
    ]
    for k in ("Title", "Subject", "Keywords", "Author"):
        t, c = target["docinfo"][k], cand["docinfo"][k]
        checks.append(("low", f"docinfo.{k}.present", t is not None, c is not None, eq))
        if t and c and t.get("pattern"):
            checks.append(("medium", f"docinfo.{k}.pattern", t["pattern"], c.get("pattern"), eq))
    for k in ("CreationDate", "ModDate"):
        t, c = target["docinfo"][k], cand["docinfo"][k]
        checks.append(("low", f"docinfo.{k}.form", t and t["raw_form"], c and c["raw_form"], eq))

    tf, cf = target["fonts"], cand["fonts"]
    checks += [
        ("medium", "fonts.embedded_share", tf["embedded_share"], cf["embedded_share"], lambda a, b: abs(a - b) <= 0.2),
        ("low", "fonts.subset_share", tf["subset_share"], cf["subset_share"], lambda a, b: abs(a - b) <= 0.25),
        ("low", "fonts.types", sorted(tf["types"]), sorted(cf["types"]), eq),
    ]
    ti, ci = target["images"], cand["images"]
    checks += [
        ("medium", "images.count", ti["count"], ci["count"], lambda a, b: abs(a - b) <= max(1, a // 10)),
        ("medium", "images.encodings", sorted(ti["encodings"]), sorted(ci["encodings"]), eq),
        ("medium", "images.ppi_median", ti["ppi_median"], ci["ppi_median"],
         lambda a, b: a is None and b is None or (a and b and 0.75 <= b / a <= 1.33)),
        ("low", "images.colors", sorted(ti["colors"]), sorted(ci["colors"]), eq),
        ("low", "images.bpc", sorted(ti["bpc"]), sorted(ci["bpc"]), eq),
    ]
    tj, cj = target["jpeg"], cand["jpeg"]
    if tj.get("inspected") and cj.get("inspected"):
        near = lambda a, b: abs(a - b) <= 0.34
        checks += [
            ("low", "jpeg.jfif_share", tj["jfif_share"], cj["jfif_share"], near),
            ("low", "jpeg.exif_share", tj["exif_share"], cj["exif_share"], near),
            ("low", "jpeg.exif_tools", sorted(tj["exif_tools"]), sorted(cj["exif_tools"]), eq),
            ("low", "jpeg.icc_share", tj["icc_share"], cj["icc_share"], near),
            ("low", "jpeg.adobe_share", tj["adobe_share"], cj["adobe_share"], near),
            ("low", "jpeg.progressive_share", tj["progressive_share"], cj["progressive_share"], near),
            ("low", "jpeg.quality_median", tj["quality_median"], cj["quality_median"],
             lambda a, b: a is None or b is None or abs(a - b) <= 10),
            ("low", "jpeg.subsampling", sorted(tj["subsampling"]), sorted(cj["subsampling"]), eq),
        ]
    elif bool(tj.get("inspected")) != bool(cj.get("inspected")):
        checks.append(("medium", "jpeg.present", bool(tj.get("inspected")), bool(cj.get("inspected")), eq))
    if cj.get("gps_present") and not tj.get("gps_present"):
        m.append(miss("high", "jpeg.gps", False, True))

    for sev, field, want, got, ok in checks:
        try:
            good = ok(want, got)
        except (TypeError, ZeroDivisionError):
            good = want == got
        if not good:
            m.append(miss(sev, field, want, got))
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("profile", help="print a profile for one PDF")
    a1.add_argument("pdf")
    a1.add_argument("--handoff", action="store_true",
                    help="omit ALL source string literals; review structural information before sharing")
    a2 = sub.add_parser("compare", help="score a candidate against a profile JSON (or a source PDF)")
    a2.add_argument("target", help="profile.json, or a PDF to profile on the fly")
    a2.add_argument("candidate")
    a = p.parse_args()
    try:
        if a.cmd == "profile":
            result = profile(a.pdf)
            print(json.dumps(handoff_profile(result) if a.handoff else result, indent=2))
            return 0
        target = profile(a.target) if a.target.lower().endswith(".pdf") else json.load(open(a.target))
        misses = compare(target, profile(a.candidate))
        print(json.dumps({"misses": misses}, indent=2))
        return 1 if misses else 0
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, TypeError, IndexError, struct.error) as e:
        print(f"[file-profile] failed ({type(e).__name__}); use a complete raw-dirty v1/v2 profile or source PDF; "
              "handoff profiles are not comparison targets", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
