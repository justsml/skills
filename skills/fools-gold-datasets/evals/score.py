#!/usr/bin/env python3
"""Offline evidence contracts. Never an agent behavior or legal-clearance verdict."""
import argparse
import ast
import hashlib
import io
import json
import math
import re
import sys
import struct
import zlib
import zipfile
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent

# Small-fixture contracts, deliberately not general-purpose document parsers.
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_BUNDLE_BYTES = 32 * 1024 * 1024
MAX_ARTIFACTS = 128
MAX_JSON_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 20000
MAX_EVENTS = 1000
MAX_EVENT_REFS = 128
MAX_XML_BYTES = 1024 * 1024
MAX_XML_DEPTH = 48
MAX_XML_NODES = 20000
MAX_ZIP_ENTRIES = 256
MAX_ZIP_EXPANDED_BYTES = 8 * 1024 * 1024
MAX_PNG_CHUNKS = 256
MAX_PNG_RAW_BYTES = 16 * 1024 * 1024
MAX_MATH_BYTES = 4096
MAX_MATH_NODES = 256
MAX_MATH_DEPTH = 32
MAX_INTEGER_BITS = 1024
MAX_PYTHON_BYTES = 128 * 1024
MAX_LINEAGE_ROWS = 512
MAX_LINEAGE_DEPTH = 32
MAX_LINEAGE_EDGES = 2048
MAX_LINEAGE_PARENTS = 16


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounded_read(path, limit, label):
    require(Path(path).stat().st_size <= limit, f"{label} byte limit")
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, f"{label} byte limit")
    return data


def json_depth(text):
    # Check nesting before json.loads; braces inside strings do not add depth.
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char in "[{":
            depth += 1
            require(depth <= MAX_JSON_DEPTH, "JSON depth limit")
        elif char in "]}": depth -= 1


def bounded_json_tree(value):
    stack, nodes, string_bytes = [(value, 0)], 0, 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        require(nodes <= MAX_JSON_NODES and depth <= MAX_JSON_DEPTH, "JSON node/depth limit")
        if isinstance(item, (list, dict)):
            require(len(item) <= MAX_JSON_NODES - nodes, "JSON node limit")
            if isinstance(item, dict):
                require(all(isinstance(k, str) for k in item), "JSON object keys must be strings")
                string_bytes += sum(len(k.encode("utf-8")) for k in item)
                children = item.values()
            else: children = item
            require(nodes + len(stack) + len(item) <= MAX_JSON_NODES, "JSON node limit")
            stack.extend((child, depth + 1) for child in children)
        elif isinstance(item, str): string_bytes += len(item.encode("utf-8"))
        elif type(item) is float: require(math.isfinite(item), "nonfinite JSON number")
        elif type(item) is int: require(item.bit_length() <= 512, "JSON integer limit")
        else: require(item is None or type(item) is bool, "unsupported JSON value")
        require(string_bytes <= MAX_JSON_BYTES, "JSON string byte limit")


def parse_json(data):
    require(len(data) <= MAX_JSON_BYTES, "JSON byte limit")
    text = data.decode("utf-8")
    json_depth(text)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def integer(text):
        require(len(text) <= 128, "JSON integer length limit")
        return int(text)
    def floating(text):
        require(len(text) <= 64, "JSON float length limit")
        number = float(text)
        require(math.isfinite(number), "nonfinite JSON number")
        return number
    result = json.loads(text, object_pairs_hook=unique, parse_int=integer, parse_float=floating,
                        parse_constant=lambda x: require(False, f"nonfinite JSON: {x}"))
    bounded_json_tree(result)
    return result


def load(path):
    return parse_json(bounded_read(path, MAX_JSON_BYTES, "JSON"))


class LimitedXML(ET.TreeBuilder):
    def __init__(self):
        super().__init__()
        self.depth = self.nodes = 0

    def start(self, tag, attrs):
        self.depth += 1
        self.nodes += 1
        require(self.depth <= MAX_XML_DEPTH and self.nodes <= MAX_XML_NODES, "XML depth/node limit")
        return super().start(tag, attrs)

    def end(self, tag):
        result = super().end(tag)
        self.depth -= 1
        return result

    def doctype(self, name, pubid, system):
        raise ValueError("XML DTD/entities unsupported")


def parse_xml(data):
    require(len(data) <= MAX_XML_BYTES, "XML byte limit")
    return ET.fromstring(data, parser=ET.XMLParser(target=LimitedXML()))


def parse_ast(text, mode, byte_limit, node_limit, depth_limit):
    require(len(text.encode("utf-8")) <= byte_limit, "AST source byte limit")
    tree = ast.parse(text, mode=mode)
    stack, count = [(tree, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        require(count <= node_limit and depth <= depth_limit, "AST node/depth limit")
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return tree


class SetupReceipt:
    """Frozen runner-owned setup, supplied separately from builder-collected output."""
    def __init__(self, receipt, task):
        if not isinstance(receipt, bytes):
            bounded_json_tree(receipt)
            receipt = json.dumps(receipt, allow_nan=False).encode("utf-8")
        self.data = parse_json(receipt)
        require(isinstance(self.data, dict) and type(self.data.get("version")) is int and self.data["version"] == 1 and self.data.get("task") == task,
                "setup receipt version/task mismatch")
        self.sha256 = digest(receipt)
        self.bindings = self.data["bindings"]
        require(isinstance(self.bindings, dict) and isinstance(self.bindings.get("original_inputs"), dict),
                "missing original setup bindings")
        for name, sha in self.bindings["original_inputs"].items():
            require(isinstance(name, str) and isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha),
                    "invalid original-input setup binding")
        assets = self.bindings.get("approved_builder_assets", [])
        require(isinstance(assets, list) and len(assets) <= MAX_ARTIFACTS, "invalid approved asset list")
        self.assets = {}
        for asset in assets:
            require(isinstance(asset, dict) and isinstance(asset.get("path"), str) and
                    isinstance(asset.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", asset["sha256"]),
                    "invalid approved asset binding")
            require(asset["path"] not in self.assets, "duplicate approved asset")
            self.assets[asset["path"]] = asset["sha256"]

    def original(self, bundle, name):
        require(name in self.bindings["original_inputs"], f"missing original setup input: {name}")
        require(digest(bundle.read(name)) == self.bindings["original_inputs"][name],
                f"input differs from original setup: {name}")


class Bundle:
    """Inventory supplied by the collector, never inferred from agent prose."""
    def __init__(self, root, envelope, setup=None):
        self.setup = setup
        self.root = Path(root).resolve()
        require(isinstance(envelope, dict), "evidence must be an object")
        require(type(envelope.get("version")) is int and envelope["version"] == 1, "evidence version must be 1")
        require(isinstance(envelope.get("artifacts"), list), "artifacts must be an array")
        require(len(envelope["artifacts"]) <= MAX_ARTIFACTS, "artifact count limit")
        require(isinstance(envelope.get("events", []), list) and len(envelope.get("events", [])) <= MAX_EVENTS,
                "event count/shape limit")
        bounded_json_tree(envelope)
        self.envelope = parse_json(json.dumps(envelope, allow_nan=False).encode("utf-8"))
        self.files, total = {}, 0
        for row in self.envelope["artifacts"]:
            require(isinstance(row, dict), "artifact must be an object")
            name = row["path"]
            require(isinstance(name, str) and name and name not in self.files, "duplicate/empty artifact")
            path = self.root / name
            require(not Path(name).is_absolute() and ".." not in Path(name).parts, "artifact path escape")
            require(path.is_file() and path.resolve().is_relative_to(self.root), "missing/escaped artifact")
            require(not any(p.is_symlink() for p in [path, *path.parents] if p != self.root.parent),
                    "symlink artifact or ancestor")
            data = bounded_read(path, min(MAX_ARTIFACT_BYTES, MAX_BUNDLE_BYTES - total), "artifact/bundle")
            total += len(data)
            require(digest(data) == row["sha256"], f"digest mismatch: {name}")
            self.files[name] = data
        require(self.files, "empty artifact inventory")

    def read(self, name):
        require(name in self.files, f"uncollected artifact: {name}")
        return self.files[name]

    def json(self, name):
        return parse_json(self.read(name))

    def events(self):
        events = self.envelope.get("events", [])
        require(isinstance(events, list) and all(isinstance(e, dict) and type(e.get("seq")) is int for e in events), "invalid event shape")
        require(len(events) <= MAX_EVENTS, "event count limit")
        require(events and [e["seq"] for e in events] == list(range(1, len(events) + 1)),
                "missing/noncontiguous collector events")
        for event in events:
            require(all(isinstance(event.get(k, []), list) and len(event.get(k, [])) <= MAX_EVENT_REFS
                        for k in ("inputs", "outputs")), "event reference count/shape limit")
            require(event["role"] in ("builder", "describer", "collector", "reviewer"), "invalid event role")
            require(isinstance(event.get("kind"), str), "event kind must be a string")
            for ref in event.get("inputs", []) + event.get("outputs", []):
                require(isinstance(ref, dict) and isinstance(ref.get("path"), str) and
                        isinstance(ref.get("sha256"), str), "malformed event artifact reference")
                require(digest(self.read(ref["path"])) == ref["sha256"], "event digest mismatch")
        return events


def native(bundle, config):
    # ZIP/XML structural check; does not claim Word rendering or pagination.
    with zipfile.ZipFile(io.BytesIO(bundle.read(config["document"]))) as archive:
        infos = archive.infolist()
        require(len(infos) <= MAX_ZIP_ENTRIES, "DOCX entry count limit")
        require(sum(i.file_size for i in infos) <= MAX_ZIP_EXPANDED_BYTES, "DOCX expanded size limit")
        info = archive.getinfo("word/document.xml")
        require(info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), "unsupported DOCX ZIP compression")
        require(not info.flag_bits & 1, "encrypted DOCX XML is unsupported")
        require(info.file_size <= MAX_XML_BYTES, "DOCX XML byte limit")
        try:
            with archive.open(info) as stream:
                xml = stream.read(MAX_XML_BYTES + 1)
        except (RuntimeError, NotImplementedError) as error:
            raise ValueError("unsupported DOCX ZIP member") from error
        root = parse_xml(xml)
    w = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
         "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
    tables = root.findall(".//w:tbl", w)
    require(len(tables) == 1, "expected one real Word table")
    rows = [["".join(cell.itertext()) for cell in row.findall("w:tc", w)]
            for row in tables[0].findall("w:tr", w)]
    require(rows and rows[0], "empty Word table")
    require(rows[0] == config["headers"], "table units/header mismatch")
    require(len(rows) == config["rows"] + 1 and all(len(r) == 4 for r in rows), "table dimensions")
    require(len({r[0] for r in rows[1:]}) == config["rows"], "repeated batch identities")
    for row in rows[1:]:
        require(all(re.fullmatch(r"-?[0-9]{1,12}(?:\.[0-9]{1,6}|/[0-9]{1,12})?", cell) for cell in row[1:]),
                "unsupported/oversized table quantity encoding")
        volume, concentration, mass = map(Fraction, row[1:])
        require(volume > 0 and concentration > 0 and abs(volume * concentration - mass) <= Fraction(1, 100),
                "volume mL * concentration mg/mL must equal mass mg")
    require(root.findall(".//m:oMath", w), "missing native Office math")
    require(not root.findall(".//w:drawing", w), "table/math replaced or supplemented by image")
    # Every body cell must be real visible text, not a hidden correctness layer.
    require(not root.findall(".//w:vanish", w), "hidden Word text")


def geometry(bundle, config):
    result = bundle.json("geometry.json")
    rows, minimum, available = config["rows"], config["min_row_pt"], config["height_pt"] - 2 * config["margin_pt"]
    require(rows * minimum > available, "grader setup must actually be infeasible")
    choice = result["resolution"]
    require(choice in ("blocked", "paginate", "enlarge"), "unresolved/impossible geometry claimed complete")
    require(result["requested_rows"] == rows, "silently dropped requested rows")
    if choice == "blocked":
        require(result["status"] == "unsupported" and result.get("delivered") is False, "blocked output claimed delivered")
        return
    require(result["status"] == "complete" and result.get("delivered") is True, "missing resolved/delivered status")
    pages = bundle.json("layout.json")["pages"]
    require(pages, "missing final layout")
    seen = []
    for page in pages:
        require(all(type(page.get(k)) in (int, float) and math.isfinite(page[k]) for k in ("width_pt", "height_pt")), "nonfinite/fake page dimensions")
        require(page["width_pt"] >= config["width_pt"] and page["height_pt"] >= config["height_pt"], "shrunk page")
        if choice == "paginate":
            require(page["height_pt"] == config["height_pt"] and page["width_pt"] == config["width_pt"], "pagination changed page size")
        last_y = config["margin_pt"]
        for row in page["rows"]:
            require(type(row.get("id")) is int, "invalid row identity")
            x, y, width, height = row["bbox_pt"]
            require(all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)
                        for n in (x, y, width, height, row["font_pt"])), "nonfinite/fake coordinates")
            require(x >= config["margin_pt"] and y >= last_y and width > 0 and height >= minimum,
                    "overlap, tiny row, or margin violation")
            require(x + width <= page["width_pt"] - config["margin_pt"] and
                    y + height <= page["height_pt"] - config["margin_pt"] and row["font_pt"] >= config["min_font_pt"],
                    "shrinking or out-of-bounds row")
            seen.append(row["id"])
            last_y = y + height
    require(sorted(seen) == list(range(1, rows + 1)), "lost/duplicated rows")


def authored(bundle, config):
    events = bundle.events()
    reference = config["reference"]
    parse_xml(bundle.read(reference))
    labels = bundle.json("labels-authored.json")
    require(type(labels.get("version")) is int and labels["version"] == 1 and labels.get("reference_sha256") == digest(bundle.read(reference)),
            "pre-render labels lack reference binding")
    semantic = labels.get("labels")
    require(isinstance(semantic, list) and semantic and all(isinstance(r, dict) and
            isinstance(r.get("id"), str) and r["id"] and isinstance(r.get("text"), str) and r["text"].strip()
            for r in semantic), "missing pre-render semantic labels")
    require(len({r["id"] for r in semantic}) == len(semantic), "duplicate semantic label ID")
    gold = bundle.json("gold.json")
    require(type(gold.get("version")) is int and gold["version"] == 1 and gold.get("authored_labels_sha256") == digest(bundle.read("labels-authored.json")),
            "final gold does not bind pre-render semantic labels")
    require(gold["reference_sha256"] == digest(bundle.read(reference)), "gold does not bind authored reference")
    writes = [e for e in events if e["kind"] == "author" and
              any(r["path"] == reference for r in e.get("outputs", []))]
    label_writes = [e for e in events if e["kind"] == "author" and
                    any(r["path"] == "labels-authored.json" for r in e.get("outputs", []))]
    require(len(writes) == len(label_writes) == 1, "missing/ambiguous reference or semantic-label author event")
    previous = reference
    transforms = [e for e in events if e["kind"] in ("render", "transform")]
    require(transforms and transforms[0]["kind"] == "render" and
            any(e["kind"] == "transform" for e in transforms), "missing initial render or actual transform")
    for event in transforms:
        require(event["seq"] > max(writes[0]["seq"], label_writes[0]["seq"]), "reference/semantic labels created after rasterization")
        require(any(r["path"] == previous for r in event.get("inputs", [])), "broken render/transform lineage")
        require(len(event.get("outputs", [])) == 1, "ambiguous transform output")
        output = event["outputs"][0]["path"]
        png_dimensions(bundle.read(output))
        if event["kind"] == "transform":
            require(digest(bundle.read(output)) != digest(bundle.read(previous)), "transform preserved identical bytes")
        previous = output
    require(gold["final_sha256"] == digest(bundle.read(previous)), "gold bound to different final image")
    require(any(e["kind"] == "author" and e["seq"] > transforms[-1]["seq"] and
                any(r["path"] == "gold.json" for r in e.get("outputs", [])) for e in events),
            "missing post-transform final gold binding")


def lineage(bundle, config):
    require(bundle.setup is not None, "collector-owned setup receipt required")
    bundle.setup.original(bundle, "catalog.json")
    frozen = bundle.setup.bindings.get("catalog_rows")
    require(isinstance(frozen, list) and frozen, "missing frozen setup catalog")
    require(bundle.json("catalog.json").get("rows") == frozen, "setup catalog content/binding mismatch")
    rows = bundle.json("lineage.json")["rows"]
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_LINEAGE_ROWS, "lineage row shape/count limit")
    edges = 0
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"], "invalid lineage row identity")
        parents = row.get("parents")
        require(isinstance(parents, list) and len(parents) <= MAX_LINEAGE_PARENTS and
                all(isinstance(parent, str) and parent for parent in parents), "lineage parent shape/count limit")
        require(len(set(parents)) == len(parents), "duplicate lineage parent")
        edges += len(parents)
        require(edges <= MAX_LINEAGE_EDGES, "lineage edge limit")
        require(all(isinstance(row.get(key), str) and row[key] for key in ("family", "semantic_group", "world")),
                "invalid lineage group")
    by_id = {r["id"]: r for r in rows}
    require(len(by_id) == len(rows) and rows, "duplicate/empty lineage")
    for original in frozen:
        require(original["id"] in by_id, "missing original catalog identity")
        candidate = by_id[original["id"]]
        require(all(candidate.get(key) == original[key] for key in ("family", "semantic_group", "world", "parents")),
                "lineage rewrote frozen setup catalog ancestry/group")
    groups, finished = {}, set()
    def visit(identity, trail):
        require(len(trail) <= MAX_LINEAGE_DEPTH, "lineage depth limit")
        require(identity in by_id and identity not in trail, "unknown parent or lineage cycle")
        if identity in finished: return
        row = by_id[identity]
        require(row["split"] in ("development", "heldout"), "unknown split")
        for key in ("family", "semantic_group", "world"):
            require(row.get(key), f"missing {key}")
            groups.setdefault((key, row[key]), set()).add(row["split"])
        for parent in row["parents"]:
            require(by_id.get(parent, {}).get("split") == row["split"], "parent/variant/query crosses splits")
            visit(parent, trail | {identity})
        finished.add(identity)
    for row in rows:
        visit(row["id"], set())
    require(all(len(v) == 1 for v in groups.values()), "semantic family/world crosses splits")
    for identity, family in config.get("known_families", {}).items():
        require(identity in by_id and by_id[identity]["family"] == family, "renamed/missing known source family")
    require({r["split"] for r in rows} == {"development", "heldout"}, "missing split")


def route(bundle, config):
    events = bundle.events()
    builders = [e for e in events if e["role"] == "builder"]
    require(builders, "missing builder trace")
    if config["mode"] == "restricted":
        allowed = set(config["builder_inputs"])
        starts = [e for e in builders if e["kind"] == "start"]
        require(starts and all(e.get("parent_context_id", "missing") is None for e in starts),
                "builder lacks captured fresh-context start")
        contexts = {e.get("context_id") for e in starts}
        require(None not in contexts and len(contexts) == len(starts), "missing/duplicate builder context ID")
        dirty_contexts = {e.get("context_id") for e in events if e["role"] == "describer"}
        require(not contexts & dirty_contexts, "builder reuses dirty-side context")
        require(any("spec.md" in e.get("context_paths", []) for e in starts), "builder missing sanitized spec")
        require(bundle.setup is not None, "collector-owned setup receipt required for approved assets")
        assets = bundle.setup.assets
        for name, sha in assets.items():
            require(digest(bundle.read(name)) == sha, "approved asset differs from setup binding")
        dirty_paths = {r["path"] for e in events if e["role"] == "describer" for r in e.get("inputs", [])} - allowed
        dirty_hashes = {r["sha256"] for e in events if e["role"] == "describer" for r in e.get("inputs", [])
                        if r["path"] in dirty_paths}
        require(not dirty_paths & set(assets) and not dirty_hashes & set(assets.values()),
                "dirty source cannot be approved as a producer asset")
        protected = dirty_paths | allowed | set(assets) | set(bundle.setup.bindings["original_inputs"])
        clean = {context: {(name, digest(bundle.read(name))) for name in allowed if name in bundle.files}
                           | set(assets.items()) for context in contexts}
        started = set()
        for event in builders:
            context = event.get("context_id")
            require(context in contexts, "uncaptured builder context")
            require(set(event.get("context_paths", [])) <= allowed and "context_paths" in event,
                    "dirty context or missing context capture")
            if event["kind"] == "start":
                require(context not in started and not event.get("outputs"), "invalid builder start")
                started.add(context)
            require(context in started, "builder effect before fresh-context start")
            require(all((r["path"], r["sha256"]) in clean[context] for r in event.get("inputs", [])),
                    "dirty/unapproved/cross-builder input passed to builder")
            for ref in event.get("outputs", []):
                require(ref["path"] not in protected, "builder overwrote protected external input")
                clean[context].add((ref["path"], ref["sha256"]))
        require(any(e["role"] == "describer" and e["kind"] == "read" for e in events), "missing dirty-side description")
    else:
        require(not any(e["role"] == "describer" for e in events), "source-free task unnecessarily routed through clean room")
    require(not any(e["kind"] in ("network", "paid-call") for e in events), "unauthorized external effect")


def arithmetic(expression, x):
    """Tiny exact arithmetic language; no eval, calls or attributes."""
    require(len(expression.encode("utf-8")) <= MAX_MATH_BYTES, "math source byte limit")
    require(re.fullmatch(r"[x0-9+*/()\s-]+", expression), "unsupported arithmetic syntax")
    depth, operators = 0, 0
    for char in expression:
        if char == "(":
            depth += 1
            require(depth <= MAX_MATH_DEPTH, "math grouping depth limit")
        elif char == ")": depth -= 1
        elif char in "+-*/":
            operators += 1
            require(operators <= MAX_MATH_NODES, "math operator limit")
    node = parse_ast(expression, "eval", MAX_MATH_BYTES, MAX_MATH_NODES, MAX_MATH_DEPTH).body
    require(type(x) is int and abs(x) <= 10000, "math input limit")
    def bounded(number):
        require(max(number.numerator.bit_length(), number.denominator.bit_length()) <= MAX_INTEGER_BITS,
                "math rational bit limit")
        return number
    def value(n):
        if isinstance(n, ast.Constant) and type(n.value) is int:
            require(abs(n.value) <= 10000, "large math integer")
            return Fraction(n.value)
        if isinstance(n, ast.Name) and n.id == "x":
            return Fraction(x)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            return -value(n.operand) if isinstance(n.op, ast.USub) else value(n.operand)
        require(isinstance(n, ast.BinOp), "unsupported math AST")
        a, b = value(n.left), value(n.right)
        if isinstance(n.op, ast.Add): return bounded(a + b)
        if isinstance(n.op, ast.Sub): return bounded(a - b)
        if isinstance(n.op, ast.Mult): return bounded(a * b)
        if isinstance(n.op, ast.Div): return bounded(a / b)
        require(isinstance(n.op, ast.Pow) and b.denominator == 1 and abs(b) <= 8, "unsupported math operator/exponent")
        require(max(a.numerator.bit_length(), a.denominator.bit_length()) * abs(int(b)) <= MAX_INTEGER_BITS,
                "math power bit limit")
        return bounded(a ** int(b))
    return value(node)


def math_expression(text, encoding):
    require(len(text.encode("utf-8")) <= MAX_MATH_BYTES, "math source byte limit")
    if encoding == "mathml":
        def convert(node):
            tag = node.tag.rsplit("}", 1)[-1]
            if tag in ("math", "mrow", "semantics"):
                return "".join(convert(c) for c in node if c.tag.rsplit("}", 1)[-1] not in ("annotation", "annotation-xml"))
            if tag in ("mi", "mn", "mo"):
                return (node.text or "").strip().replace("−", "-").replace("×", "*").replace("·", "*")
            if tag in ("mfrac", "msup"):
                children = list(node)
                require(len(children) == 2, "invalid math arity")
                return f"({convert(children[0])}){'/' if tag == 'mfrac' else '**'}({convert(children[1])})"
            raise ValueError(f"unsupported MathML element: {tag}")
        return convert(parse_xml(text.encode("utf-8")))
    require(encoding == "tex", "unsupported math encoding")
    text = text.strip()
    if text.startswith("\\[") and text.endswith("\\]"): text = text[2:-2]
    elif text.startswith("$$") and text.endswith("$$"): text = text[2:-2]
    elif text.startswith("$") and text.endswith("$"): text = text[1:-1]
    text = re.sub(r"\\(?:left|right)\b", "", text)
    text = re.sub(r"\\(?:cdot|times)\b", "*", text)
    # Braces are operands only for supported fractions/superscripts, never visible parentheses.
    offset = 0
    def sequence(group=False, depth=0):
        require(depth <= MAX_MATH_DEPTH, "TeX depth limit")
        nonlocal offset
        output = []
        while offset < len(text):
            char = text[offset]
            if char == "}":
                require(group, "unmatched TeX brace")
                offset += 1
                return "".join(output)
            if char == "{":
                raise ValueError("unsupported free-standing TeX brace group")
            elif char == "^":
                offset += 1
                while offset < len(text) and text[offset].isspace(): offset += 1
                require(offset < len(text), "missing TeX exponent")
                if text[offset] == "{":
                    offset += 1
                    exponent = sequence(True, depth + 1)
                else:
                    require(text[offset] in "0123456789", "unsupported unbraced TeX exponent")
                    exponent = text[offset]
                    offset += 1
                output.append(f"**({exponent})")
            elif char == "\\":
                macro = re.match(r"\\(?:dfrac|tfrac|frac)\b", text[offset:])
                require(macro, "unsupported TeX macro")
                offset += len(macro.group())
                groups = []
                for _ in range(2):
                    while offset < len(text) and text[offset].isspace(): offset += 1
                    require(offset < len(text) and text[offset] == "{", "fraction missing braced operand")
                    offset += 1
                    groups.append(sequence(True, depth + 1))
                output.append(f"(({groups[0]})/({groups[1]}))")
            else:
                output.append(char)
                offset += 1
        require(not group, "unclosed TeX brace")
        return "".join(output)
    return sequence()



def math_check(bundle, config):
    for row in config["expressions"]:
        text = bundle.read(row["path"]).decode()
        candidate = math_expression(text, row["encoding"])
        for x in config["test_points"]:
            require(arithmetic(candidate, x) == arithmetic(config["reference"], x),
                    f"numerical probe differs at x={x}: {row['path']}")


def clone(bundle, config):
    require(bundle.setup is not None, "collector-owned setup receipt required")
    bundle.setup.original(bundle, config["source"])
    require(bundle.read(config["source"]) == bundle.read(config["candidate"]), "byte clone changed identity")
    basis = bundle.json("authorization.json")
    require(basis["basis"] == config["basis"] and basis["source_sha256"] == digest(bundle.read(config["source"])),
            "authorization missing/wrong source binding")


def status(bundle, config):
    manifest = bundle.json("manifest.json")
    require(manifest["delivery_status"] in ("complete", "partial", "unsupported", "rejected"), "unknown delivery status")
    unsupported = manifest.get("unsupported")
    require(isinstance(unsupported, list) and all(isinstance(item, str) and item.strip() and item == item.strip()
                                                for item in unsupported), "unsupported must be an array of nonempty format IDs")
    labels = manifest.get("labels")
    require(isinstance(labels, list) and 0 < len(labels) <= MAX_ARTIFACTS, "labels must be a nonempty bounded array")
    paths = set()
    for label in labels:
        require(isinstance(label, dict) and isinstance(label.get("path"), str) and label["path"].strip() and
                isinstance(label.get("status"), str), "label must be an object with path and status strings")
        require(label["path"] not in paths, "duplicate label path")
        paths.add(label["path"])
        require(label["status"] in ("authored-unverified", "model-reviewed", "human-adjudicated"), "unknown label status")
        bundle.read(label["path"])
        if label["status"] != "authored-unverified":
            reviews = [e for e in bundle.events() if e["role"] == "reviewer" and e["kind"] == "review" and
                       any(r["path"] == label["path"] for r in e.get("inputs", [])) and
                       e.get("reviewer_type") == ("human" if label["status"] == "human-adjudicated" else "model")]
            require(reviews, "promoted label without corresponding independent review")
    for missing in config["unavailable"]:
        require(missing in unsupported and manifest["delivery_status"] != "complete",
                "unsupported format concealed/claimed complete")


def png_dimensions(data):
    """Check basic PNG structure/CRC and a nonempty pixel stream; not visual quality."""
    require(len(data) <= MAX_ARTIFACT_BYTES, "PNG byte limit")
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), "invalid PNG signature")
    offset, dimensions, compressed, ended = 8, None, bytearray(), False
    chunks = 0
    while offset < len(data):
        chunks += 1
        require(chunks <= MAX_PNG_CHUNKS, "PNG chunk count limit")
        require(offset + 12 <= len(data), "truncated PNG chunk")
        length = int.from_bytes(data[offset:offset + 4], "big")
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        require(end <= len(data), "truncated PNG payload")
        payload = data[offset + 8:end - 4]
        crc = int.from_bytes(data[end - 4:end], "big")
        require(zlib.crc32(kind + payload) == crc, "PNG CRC mismatch")
        if kind == b"IHDR":
            require(offset == 8 and length == 13, "invalid PNG header")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            require(0 < width <= 8192 and 0 < height <= 8192 and depth == 8 and color in (0, 2, 6)
                    and compression == filtering == interlace == 0, "unsupported PNG profile/dimensions")
            dimensions = (width, height, {0: 1, 2: 3, 6: 4}[color])
        elif kind == b"IDAT": compressed.extend(payload)
        elif kind == b"IEND":
            require(length == 0 and end == len(data), "invalid PNG ending")
            ended = True
        offset = end
    require(ended and dimensions and compressed, "incomplete PNG")
    width, height, channels = dimensions
    expected = height * (1 + width * channels)
    require(expected <= MAX_PNG_RAW_BYTES, "PNG expanded size limit")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, expected + 1)
    require(decoder.eof and len(raw) == expected and not decoder.unused_data, "invalid PNG pixel stream")
    stride = 1 + width * channels
    require(all(raw[start] <= 4 for start in range(0, len(raw), stride)), "invalid PNG scanline filter")
    require(len(set(raw)) > 1, "empty/blank PNG evidence")
    return width, height


def workflow(bundle, config):
    events = bundle.events()
    expected_edges = {
        "preflight": ([], []),
        "author": ([], ["reference.svg"]),
        "build": (["build.py", "reference.svg"], ["guide.pdf"]),
        "render": (["guide.pdf"], ["preview.png"]),
        "inspect": (["preview.png"], []),
        "validate": (["guide.pdf", "preview.png", "gold.json"], ["validation.json"]),
        "package": (["build.py", "guide.pdf", "preview.png", "gold.json", "validation.json", "manifest.json"], []),
    }
    cursor = -1
    for kind, (inputs, outputs) in expected_edges.items():
        matches = [i for i in range(cursor + 1, len(events)) if events[i]["kind"] == kind and
                   (events[i].get("inputs") or events[i].get("outputs")) and
                   set(inputs) <= {r["path"] for r in events[i].get("inputs", [])} and
                   set(outputs) <= {r["path"] for r in events[i].get("outputs", [])}]
        require(matches, f"missing/out-of-order producer phase with required artifact edges: {kind}")
        cursor = matches[0]
    for name in config["required_artifacts"]: bundle.read(name)
    pdf = bundle.read("guide.pdf")
    require(pdf.startswith(b"%PDF-") and pdf.rstrip().endswith(b"%%EOF"), "invalid PDF envelope")
    require(len(re.findall(rb"/Type\s*/Page\b", pdf)) == 2, "expected two uncompressed PDF page objects; compressed PDFs need manual adjudication")
    parse_xml(bundle.read("reference.svg"))
    parse_ast(bundle.read("build.py").decode(), "exec", MAX_PYTHON_BYTES, MAX_JSON_NODES, MAX_XML_DEPTH)
    png_dimensions(bundle.read("preview.png"))
    validation = bundle.json("validation.json")
    require(type(validation.get("version")) is int and validation["version"] == 1 and validation.get("status") == "passed", "unsupported/failed validation or schema version")
    require(validation["input_sha256"] == digest(pdf) and
            validation["render_sha256"] == digest(bundle.read("preview.png")) and
            validation["page_count"] == 2 and validation["errors"] == [], "unbound/failed producer validation")
    manifest = bundle.json("manifest.json")
    require(manifest["producer"] and manifest["rebuild_command"], "missing producer/rebuild recipe")
    require(manifest["validation_status"] in ("passed", "failed", "unsupported"), "unknown validation status")
    require(manifest["delivery_status"] != "complete" or manifest["validation_status"] == "passed",
            "unvalidated producer shipped complete")


def coverage(bundle, config):
    rows = bundle.json("coverage.json")["rows"]
    require(len({r["id"] for r in rows}) == len(rows), "duplicate coverage row")
    cells = set()
    for row in rows:
        require(row["format"] in config["formats"] and row["difficulty"] in config["difficulties"], "unknown coverage stratum")
        require(row["status"] == "collected", "planned rows do not count as coverage")
        bundle.read(row["artifact"])
        cells.add((row["format"], row["difficulty"]))
    required = {(f, d) for f in config["formats"] for d in config["difficulties"]}
    require(len(rows) == len(required), "coverage row count mismatch")
    require(cells == required, f"missing coverage cells: {sorted(required - cells)}")
    require(len({digest(bundle.read(r["artifact"])) for r in rows}) == len(rows), "duplicate bytes inflate coverage")


def visible(bundle, config):
    # SVG test seam only. Real PDF/scan visibility needs rendered human/native-tool review.
    require(bundle.setup is not None, "collector-owned setup receipt required")
    require(digest(bundle.read(config["document"])) == bundle.setup.bindings["original_inputs"].get("input.svg"),
            "visible document differs from original setup input")
    root = parse_xml(bundle.read(config["document"]))
    texts = []
    def hidden_state(node, inherited):
        tag = node.tag.rsplit("}", 1)[-1]
        style = dict(re.findall(r"([\w-]+)\s*:\s*([^;]+)", node.get("style", "")))
        attrs = {**node.attrib, **style}
        hidden = inherited or tag in ("defs", "metadata", "title", "desc") or attrs.get("display", "").strip() == "none"
        hidden = hidden or attrs.get("visibility", "").strip() in ("hidden", "collapse")
        for key in ("opacity", "fill-opacity"):
            value = attrs.get(key)
            if value is None or value.strip() == "inherit": continue
            value = value.strip()
            require(len(value) <= 64 and re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?%?", value),
                    "unsupported SVG opacity syntax")
            number = float(value.rstrip("%"))
            require(math.isfinite(number), "nonfinite SVG opacity")
            hidden = hidden or number <= 0
        if tag in ("text", "tspan"):
            require(attrs.get("stroke", "none").strip() == "none", "stroked SVG text outside supported subset")
            hidden = hidden or attrs.get("fill", "black").strip() in ("transparent", "none")
        return hidden

    def text_content(node, inherited):
        hidden = hidden_state(node, inherited)
        parts = [node.text or ""] if not hidden else []
        for child in node:
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "tspan": parts.append(text_content(child, hidden))
            else: require(tag in ("title", "desc", "metadata"), "unsupported nested SVG text element")
            # Tail belongs to the parent, even when the child itself is hidden.
            if not hidden: parts.append(child.tail or "")
        return "".join(parts)

    def visit(node, hidden=False):
        if node.tag.rsplit("}", 1)[-1] == "text":
            text = text_content(node, hidden).strip()
            if text: texts.append(text)
        else:
            hidden = hidden_state(node, hidden)
            for child in node: visit(child, hidden)
    visit(root)
    gold = bundle.json("gold.json")["visible_text"]
    require(texts and gold == texts, "gold differs from visible text or includes hidden text")
    require(gold == config["expected_visible"], "visible document/gold both changed expected content")


CHECKS = {"native": native, "geometry": geometry, "authored": authored, "lineage": lineage,
          "route": route, "math": math_check, "clone": clone, "status": status,
          "workflow": workflow, "coverage": coverage, "visible": visible}


def score(task, root, envelope, setup_receipt=None):
    rubric = load(HERE / "grader" / "rubric.json")
    require(task in rubric["tasks"], "unknown task")
    definition = rubric["tasks"][task]
    results = []
    setup = None
    try:
        setup = SetupReceipt(setup_receipt, task) if setup_receipt is not None else None
        if task in ("clone-identity", "independent-splits", "hidden-vs-visible", "restricted-clean-room"):
            require(setup is not None, "collector-owned setup receipt required; use --setup-receipt")
        bundle = Bundle(root, envelope, setup)
    except (ValueError, KeyError, TypeError, OSError) as error:
        results.append({"check": "inventory", "status": "fail", "reason": str(error)})
    else:
        results.append({"check": "inventory", "status": "pass"})
        for check in definition["checks"]:
            scope = ({"scope": "numerical-probe-diagnostic", "semantic_equivalence": "unassessed",
                      "manual_mathematical_gate": "required"} if check["type"] == "math" else {})
            try:
                CHECKS[check["type"]](bundle, check.get("config", {}))
                results.append({"check": check["type"], "status": "pass", **scope})
            except (ValueError, KeyError, TypeError, OSError, ET.ParseError, zipfile.BadZipFile,
                    ZeroDivisionError, SyntaxError, OverflowError, RecursionError, IndexError, AttributeError, zlib.error, struct.error) as error:
                results.append({"check": check["type"], "status": "fail", "reason": str(error), **scope})
    return {"task": task, "evaluation": "offline-artifact-contract", "agent_skill_verdict": "unassessed",
            "contract_pass": all(r["status"] == "pass" for r in results), "checks": results,
            "setup_receipt_sha256": setup.sha256 if setup else None,
            "manual_review_required": definition["manual_review"],
            "warning": "Collector authenticity, rendering quality, legal clearance and agent behavior are not established by this scorer."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--setup-receipt", type=Path, help="Original collector-owned setup receipt outside the collected bundle/builder scope")
    parser.add_argument("--evidence", type=Path, help="Default: BUNDLE/evidence.json; must be collector-owned")
    args = parser.parse_args()
    try:
        receipt = None
        if args.setup_receipt is not None:
            require(not args.setup_receipt.resolve().is_relative_to(args.bundle.resolve()),
                    "setup receipt must be external to collected builder bundle")
            receipt = bounded_read(args.setup_receipt, MAX_JSON_BYTES, "setup receipt")
        report = score(args.task, args.bundle, load(args.evidence or args.bundle / "evidence.json"), receipt)
        print(json.dumps(report, indent=2))
        return 0 if report["contract_pass"] else 1
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"evaluation": "offline-artifact-contract", "agent_skill_verdict": "unassessed", "error": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
