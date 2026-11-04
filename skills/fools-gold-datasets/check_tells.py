#!/usr/bin/env python3
"""Flag possible generation tells for contextual review.

Matches are diagnostics, not proof of a defect: legitimate technical language
and truthful producer metadata may match. Retain raw flags and adjudicate exact
occurrences; do not hide a real producer or rewrite meaningful prose to evade them.

Input: extracted text of the candidate (and optionally the file itself, for
metadata). Output: a miss report in the judge-rubric format, ready for
`score.py --misses`. Stdlib + pdfinfo; run with `python3 -I`.
Exit 0 = no tells, 1 = tells found, 2 = usage error.
Office metadata requires well-formed supported OOXML/ODF namespaces. XML text
is decoded before matching (including character references and CDATA). DTDs,
unsupported roots/structured values, and bounded-parser limit failures are
indeterminate, not clean inspections. Locations refer to decoded field text.
"""
import argparse
import os
import json
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

MAX_METADATA_BYTES = 200_000
MAX_METADATA_DEPTH = 64
MAX_METADATA_NODES = 4096
DC_NS = "http://purl.org/dc/elements/1.1/"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
META_NS = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
METADATA_ROOTS = {"docProps/core.xml": {f"{{{CORE_NS}}}coreProperties"},
                  "docProps/app.xml": {f"{{{APP_NS}}}Properties"},
                  "meta.xml": {f"{{{OFFICE_NS}}}document-meta"}}
METADATA_FIELDS = {
    **{f"{{{DC_NS}}}{field}": f"dc:{field}" for field in ("title", "creator", "subject", "description")},
    **{f"{{{CORE_NS}}}{field}": f"cp:{field}" for field in ("lastModifiedBy", "keywords")},
    f"{{{APP_NS}}}Application": "Application",
    **{f"{{{META_NS}}}{field}": f"meta:{field}" for field in ("generator", "initial-creator", "keyword")},
}
METADATA_LOCAL_NAMES = {tag.rsplit("}", 1)[-1] for tag in METADATA_FIELDS}


class MetadataTree(ET.TreeBuilder):
    """Reject DTDs before entity expansion and bound parsed tree complexity."""
    def __init__(self):
        super().__init__()
        self.depth = self.nodes = 0

    def doctype(self, name, pubid, system):
        raise ValueError("DTD metadata is unsupported")

    def start(self, tag, attrs):
        self.depth += 1
        self.nodes += 1
        if self.depth > MAX_METADATA_DEPTH or self.nodes > MAX_METADATA_NODES:
            raise ValueError("metadata tree exceeds inspection limits")
        return super().start(tag, attrs)

    def end(self, tag):
        result = super().end(tag)
        self.depth -= 1
        return result

# (pattern, severity, label). Case-insensitive, word-bounded where it matters.
TEXT_TELLS = [
    (r"\b(synthetic|synthesi[sz]ed|fabricated|fictitious|fictional|made[- ]up|not real|simulated)\b", "high", "generation disclaimer"),
    (r"\b(ai|llm|model)[- ]generated\b|\bgenerated (by|with|for) (ai|an? (llm|model))\b", "high", "generation disclaimer"),
    (r"\bfor (illustration|illustrative|demonstration|testing) (purposes|only)\b", "high", "illustration disclaimer"),
    (r"\b(sample|dummy|placeholder|example|test) (data|document|text|figures?|values?|company)\b", "high", "placeholder wording"),
    (r"\blorem ipsum\b|\bdolor sit amet\b", "high", "lorem ipsum"),
    (r"\[(insert|todo|tbd|placeholder|name|date|company)[^\]]*\]|\{\{[^}]+\}\}|<(insert|todo)[^>]*>", "high", "unfilled template slot"),
    (r"\b(todo|tbd|fixme|xxx+)\b", "medium", "editing marker"),
    (r"\bwatermark\b|\bdo not distribute\b|\bconfidential draft\b", "medium", "watermark or banner text"),
    (r"\b(acme|initech|globex|contoso|fabrikam|northwind|widgets? inc|xyz corp|abc corp|foo ?bar)\b", "high", "stock fictional company"),
    (r"\b(john|jane) (doe|smith)\b|\bcompany [a-d]\b|\bperson [a-d]\b|\bcustomer [0-9]+\b", "high", "stock fictional person or label"),
    (r"\bexample\.(com|org|net)\b|@test\.|\btest@", "high", "reserved example domain"),
    (r"\(?\b555\)?[-. ]01[0-9]{2}\b", "medium", "fictional 555 phone number"),
    (r"\b(123 main st(reet)?|anytown|springfield, usa)\b", "medium", "stock fictional address"),
]
# Metadata strings worth contextual inspection; genuine producers are not defects.
META_TELLS = [
    (r"^untitled$|^anonymous$|^unknown$|^document$", "medium", "default title/author metadata"),
    (r"python-docx|python-pptx|openpyxl|reportlab|matplotlib|xlsxwriter|weasyprint|pdfkit|fpdf", "medium",
     "generator library named in metadata"),
]


# Preserve configured tool and scratch paths without forwarding credentials.
SAFE_ENV = {key: os.environ[key] for key in
            ("PATH", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR")
            if key in os.environ}
SAFE_ENV.setdefault("PATH", os.defpath)
SAFE_ENV.update({"LANG": "C", "LC_ALL": "C"})

def pdf_meta(path):
    out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=60,
                         env=SAFE_ENV, check=True).stdout
    meta = {}
    for line in out.splitlines():
        k, _, v = line.partition(":")
        if k in ("Title", "Subject", "Keywords", "Author", "Creator", "Producer"):
            meta[k] = v.strip()
    return meta


def office_meta(path):
    meta = {}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist()) & set(METADATA_ROOTS)
        if not names:
            raise ValueError("no supported metadata parts")
        for name in sorted(names):
            if z.namelist().count(name) != 1:
                raise ValueError("ambiguous duplicate metadata parts")
            if z.getinfo(name).compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("unsupported metadata ZIP compression")
            if z.getinfo(name).flag_bits & 1:
                raise ValueError("encrypted metadata part is unsupported")
            try:
                with z.open(name) as part:
                    data = part.read(MAX_METADATA_BYTES + 1)
            except (RuntimeError, NotImplementedError) as error:
                raise ValueError("unsupported metadata ZIP member") from error
            if len(data) > MAX_METADATA_BYTES:
                raise ValueError("metadata part exceeds inspection limit")
            root = ET.fromstring(data, parser=ET.XMLParser(target=MetadataTree()))
            if root.tag not in METADATA_ROOTS[name]:
                raise ValueError("unsupported metadata root or namespace")
            for index, node in enumerate(root.iter()):
                tag = METADATA_FIELDS.get(node.tag)
                if not tag and node.tag.rsplit("}", 1)[-1] in METADATA_LOCAL_NAMES:
                    raise ValueError("unsupported metadata field namespace")
                if tag:
                    if len(node):
                        raise ValueError("structured metadata field is unsupported")
                    # Canonical namespace labels ignore source-selected prefixes;
                    # the node index preserves repeated fields rather than dropping them.
                    meta[f"{name}:{tag}:{index}"] = (node.text or "").strip()
    return meta


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--text", required=True, help="extracted candidate text (pdftotext, mammoth, transcript)")
    p.add_argument("--file", help="candidate file, to check PDF or Office metadata")
    p.add_argument("--allow", action="append", default=[],
                   help="context regex; suppress only tell matches overlapping its nonempty spans, e.g. 'synthetic biology'")
    p.add_argument("--where", default="document")
    a = p.parse_args()

    text = open(a.text, encoding="utf-8").read()
    allow = [re.compile(x, re.I) for x in a.allow]
    misses = []

    def add(severity, label, match, context, where):
        start, end = match.span()
        if any(x.start() < end and start < x.end()
               for r in allow for x in r.finditer(context) if x.start() < x.end()):
            return
        misses.append({"category": "realism", "severity": severity, "cause": "build", "where": where,
                       "summary": f"{label}: '{match.group(0)[:60]}'",
                       "start": start, "end": end,
                       "line": context.count("\n", 0, start) + 1,
                       "column": start - context.rfind("\n", 0, start)})

    for pattern, sev, label in TEXT_TELLS:
        for m in re.finditer(pattern, text, re.I):
            add(sev, label, m, text, a.where)

    if a.file:
        meta = pdf_meta(a.file) if a.file.lower().endswith(".pdf") else office_meta(a.file)
        for key, value in meta.items():
            for pattern, sev, label in META_TELLS:
                for m in re.finditer(pattern, value or "", re.I):
                    add(sev, f"{label} ({key})", m, value, f"metadata:{key}")
            for pattern, sev, label in TEXT_TELLS:
                for m in re.finditer(pattern, value or "", re.I):
                    add(sev, f"{label} ({key})", m, value, f"metadata:{key}")

    print(json.dumps({"misses": misses}, indent=2))
    return 1 if misses else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, ET.ParseError, re.error, zipfile.BadZipFile, subprocess.SubprocessError) as e:
        print(json.dumps({"status": "indeterminate", "error": f"tell inspection failed ({type(e).__name__})"}))
        sys.exit(2)
