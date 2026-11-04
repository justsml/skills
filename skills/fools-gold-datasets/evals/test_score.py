"""Synthetic offline contract tests, NEVER evidence of an agent skill pass."""
import copy
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import struct
import zlib
import tempfile
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fg_behavior_score", HERE / "score.py")
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)
setup_spec = importlib.util.spec_from_file_location("fg_behavior_setup", HERE / "setup.py")
setup = importlib.util.module_from_spec(setup_spec)
setup_spec.loader.exec_module(setup)


def scratch_parent():
    """Honor configured disk scratch; public fallback stays under a user cache."""
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    directory = os.environ.setdefault("TMPDIR", str(cache / "fools-gold-tests"))
    for key in ("TMP", "TEMP"): os.environ.setdefault(key, directory)
    return Path(directory)


class Contracts(unittest.TestCase):
    def setUp(self):
        # Use host-approved disk scratch when set, otherwise a portable user cache.
        scratch = scratch_parent()
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="fg-contract-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.events = []
        self.receipt = None

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode())

    def put_json(self, name, value):
        self.put(name, json.dumps(value))

    def event(self, kind, inputs=(), outputs=(), role="collector", **extra):
        def ref(name):
            return {"path": name, "sha256": scorer.digest((self.root / name).read_bytes())}
        self.events.append({"seq": len(self.events) + 1, "role": role, "kind": kind,
                            "inputs": [ref(n) for n in inputs], "outputs": [ref(n) for n in outputs], **extra})

    def envelope(self):
        return {"version": 1, "artifacts": [{"path": str(p.relative_to(self.root)), "sha256": scorer.digest(p.read_bytes())}
                for p in sorted(self.root.rglob("*")) if p.is_file()], "events": self.events}

    def freeze_setup(self, task, originals=None, catalog=None, assets=None):
        bindings = {"original_inputs": {name: scorer.digest(data) for name, data in (originals or {}).items()},
                    "approved_builder_assets": assets or []}
        if catalog is not None: bindings["catalog_rows"] = copy.deepcopy(catalog)
        self.receipt = {"version": 1, "task": task, "bindings": bindings}

    def png(self, raw=b"\0\0\xff\0\xff\0"):
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

    def bundle(self):
        setup_receipt = scorer.SetupReceipt(self.receipt, self.receipt["task"]) if self.receipt else None
        return scorer.Bundle(self.root, self.envelope(), setup_receipt)

    def report(self, task):
        return scorer.score(task, self.root, self.envelope(), self.receipt if self.receipt and self.receipt["task"] == task else None)

    def passed(self, task):
        result = self.report(task)
        self.assertTrue(result["contract_pass"], result)
        self.assertEqual(result["agent_skill_verdict"], "unassessed")

    def failed(self, task):
        self.assertFalse(self.report(task)["contract_pass"])

    def test_verified_json_and_docx_buffers_survive_path_replacement(self):
        self.native_docx()
        self.put_json("captured.json", {"answer": 18})
        config = scorer.load(HERE / "grader/rubric.json")["tasks"]["native-units"]["checks"][0]["config"]
        bundle = self.bundle()
        self.put_json("captured.json", {"answer": "forged after collection"})
        self.put("worksheet.docx", b"not a ZIP after collection")
        # Parsing must not touch paths at all once verified bytes have been captured.
        with mock.patch.object(Path, "open", side_effect=AssertionError("reopened mutable path")):
            self.assertEqual(bundle.json("captured.json"), {"answer": 18})
            scorer.native(bundle, config)

    def test_envelope_snapshot_is_independent_of_callers_mutations(self):
        self.reference()
        envelope = self.envelope()
        bundle = scorer.Bundle(self.root, envelope)
        envelope["events"][0]["seq"] = 100
        envelope["artifacts"][0]["sha256"] = "forged"
        self.assertEqual(bundle.events()[0]["seq"], 1)

    def test_artifact_size_count_and_total_limits(self):
        oversized = self.root / "large"
        with oversized.open("wb") as stream: stream.truncate(scorer.MAX_ARTIFACT_BYTES + 1)
        envelope = {"version": 1, "artifacts": [{"path": "large", "sha256": "0" * 64}]}
        with self.assertRaisesRegex(ValueError, "artifact/bundle.*limit"):
            scorer.Bundle(self.root, envelope)
        oversized.unlink()
        self.put("a", "123456789012"); self.put("b", "123456789012")
        with mock.patch.object(scorer, "MAX_BUNDLE_BYTES", 16):
            with self.assertRaisesRegex(ValueError, "artifact/bundle.*limit"): self.bundle()
        with mock.patch.object(scorer, "MAX_ARTIFACTS", 1):
            with self.assertRaisesRegex(ValueError, "artifact count limit"): self.bundle()
        with mock.patch.object(scorer, "MAX_BUNDLE_BYTES", 24):
            self.assertEqual(len(self.bundle().files), 2)

    def test_json_byte_depth_and_number_limits_before_parsing(self):
        with mock.patch.object(scorer.json, "loads", side_effect=AssertionError("expensive JSON parser entered")):
            for data in (b" " * (scorer.MAX_JSON_BYTES + 1),
                         b"[" * (scorer.MAX_JSON_DEPTH + 1) + b"]" * (scorer.MAX_JSON_DEPTH + 1)):
                with self.assertRaisesRegex(ValueError, "JSON .*limit"): scorer.parse_json(data)
        for data in (b"[" + b"0," * scorer.MAX_JSON_NODES + b"0]", b'{"x":1e9999}', b'{"x":' + b"9" * 129 + b"}"):
            with self.assertRaises(ValueError): scorer.parse_json(data)
        self.assertEqual(scorer.parse_json(b'{"note":"[{\\\"}]"}'), {"note": '[{"}]'})
        self.put("oversize-envelope.json", " " * (scorer.MAX_JSON_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "JSON byte limit"): scorer.load(self.root / "oversize-envelope.json")

    def test_recursive_in_memory_envelope_rejected_before_copy(self):
        recursive = []; recursive.append(recursive)
        envelope = {"version": 1, "artifacts": [], "extra": recursive}
        with mock.patch.object(scorer.json, "dumps", side_effect=AssertionError("recursive serialization entered")):
            with self.assertRaisesRegex(ValueError, "JSON .*limit"): scorer.Bundle(self.root, envelope)

    def test_xml_size_depth_node_and_entity_limits(self):
        self.assertEqual(scorer.parse_xml(b"<svg><text>18 crates</text></svg>").tag, "svg")
        with mock.patch.object(scorer.ET, "fromstring", side_effect=AssertionError("oversized XML parsed")):
            with self.assertRaisesRegex(ValueError, "XML byte limit"):
                scorer.parse_xml(b" " * (scorer.MAX_XML_BYTES + 1))
        for data in (b"<g>" * (scorer.MAX_XML_DEPTH + 1) + b"</g>" * (scorer.MAX_XML_DEPTH + 1),
                     b"<svg>" + b"<g/>" * scorer.MAX_XML_NODES + b"</svg>",
                     b'<!DOCTYPE svg [<!ENTITY e "expanded">]><svg>&e;</svg>'):
            with self.assertRaisesRegex(ValueError, "XML .*limit|XML DTD/entities"): scorer.parse_xml(data)

    def test_native_zip_expansion_rejected_before_member_decompression(self):
        self.native_docx()
        config = scorer.load(HERE / "grader/rubric.json")["tasks"]["native-units"]["checks"][0]["config"]
        scorer.native(self.bundle(), config)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", b"x" * 4096)
        self.put("worksheet.docx", output.getvalue())
        bundle = self.bundle()
        with mock.patch.object(scorer, "MAX_ZIP_EXPANDED_BYTES", 1024), \
             mock.patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("oversized member decompressed")):
            with self.assertRaisesRegex(ValueError, "DOCX expanded size limit"): scorer.native(bundle, config)

    def test_png_bounds_before_and_during_decompression(self):
        self.workflow()
        valid = (self.root / "preview.png").read_bytes()
        self.assertEqual(scorer.png_dimensions(valid), (2, 2))
        with mock.patch.object(scorer, "MAX_PNG_RAW_BYTES", 5), \
             mock.patch.object(scorer.zlib, "decompressobj", side_effect=AssertionError("oversized PNG decompressed")):
            with self.assertRaisesRegex(ValueError, "PNG expanded size limit"): scorer.png_dimensions(valid)
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
        bomb = header + chunk(b"IDAT", zlib.compress(b"x" * 4096)) + chunk(b"IEND", b"")
        class TrackingDecoder:
            def __init__(self): self.inner, self.limit = zlib.decompressobj(), None
            def decompress(self, data, limit):
                self.limit = limit
                return self.inner.decompress(data, limit)
            def __getattr__(self, name): return getattr(self.inner, name)
        decoder = TrackingDecoder()
        with mock.patch.object(scorer.zlib, "decompressobj", return_value=decoder):
            with self.assertRaisesRegex(ValueError, "invalid PNG pixel stream"): scorer.png_dimensions(bomb)
        self.assertEqual(decoder.limit, 7)  # Declared six raw bytes plus one overflow byte.
        many_chunks = header + chunk(b"tEXt", b"") * scorer.MAX_PNG_CHUNKS + valid[len(header):]
        with self.assertRaisesRegex(ValueError, "PNG chunk count limit"): scorer.png_dimensions(many_chunks)

    def test_expression_limits_and_nested_power_growth(self):
        self.assertEqual(scorer.arithmetic("(x**2+1)/(x+2)", 3), scorer.Fraction(2))
        with mock.patch.object(scorer.ast, "parse", side_effect=AssertionError("oversized/deep expression parsed")):
            for expression in ("x" * (scorer.MAX_MATH_BYTES + 1),
                               "(" * (scorer.MAX_MATH_DEPTH + 1) + "x" + ")" * (scorer.MAX_MATH_DEPTH + 1)):
                with self.assertRaisesRegex(ValueError, "math .*limit"): scorer.arithmetic(expression, 2)
        for initial in ("2", "(1/2)"):
            expression = initial
            for _ in range(5): expression = f"({expression})**8"
            with self.assertRaisesRegex(ValueError, "math .*bit limit"): scorer.arithmetic(expression, 2)
        with self.assertRaisesRegex(ValueError, "AST node/depth limit"):
            scorer.arithmetic("+".join(["x"] * 40), 2)
        for text, encoding in ((r"\frac{" * 40 + "x" + "}{2}" * 40, "tex"),
                               ("<math>" + "<mrow>" * 50 + "<mi>x</mi>" + "</mrow>" * 50 + "</math>", "mathml")):
            with self.assertRaisesRegex(ValueError, "depth.*limit|depth/node limit"): scorer.math_expression(text, encoding)

    def test_probe_collision_cannot_claim_semantic_equivalence(self):
        self.math()
        # Agrees at every frozen probe, but differs at x=1. This must remain diagnostic.
        self.put("formula.tex", r"\frac{5(x-32)}{9}+(x+40)(x-32)(x-98)(x-212)")
        report = self.report("math-encodings")
        self.assertTrue(report["contract_pass"], report)
        diagnostic = next(r for r in report["checks"] if r["check"] == "math")
        self.assertEqual(diagnostic["scope"], "numerical-probe-diagnostic")
        self.assertEqual(diagnostic["semantic_equivalence"], "unassessed")
        self.assertEqual(diagnostic["manual_mathematical_gate"], "required")
        self.assertEqual(report["agent_skill_verdict"], "unassessed")

    def refresh_event_hashes(self):
        for event in self.events:
            for ref in event.get("inputs", []) + event.get("outputs", []):
                ref["sha256"] = scorer.digest((self.root / ref["path"]).read_bytes())
        for index, event in enumerate(self.events): event["seq"] = index + 1

    def cli(self, task, receipt=None):
        envelope = self.envelope()
        envelope["artifacts"] = [r for r in envelope["artifacts"] if r["path"] != "evidence.json"]
        self.put_json("evidence.json", envelope)
        command = [sys.executable, str(HERE / "score.py"), "--task", task, "--bundle", str(self.root)]
        if receipt is not None: command.extend(["--setup-receipt", str(receipt)])
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)

    def test_restricted_builder_can_reopen_render_inspect_validate_own_outputs(self):
        self.routes()
        self.put("candidate.svg", '<svg><text>18 crates</text></svg>')
        self.put("preview.png", self.png())
        self.put_json("gold.json", {"text": "18 crates"})
        self.put_json("validation.json", {"observed": "candidate and gold correspond"})
        context = {"role": "builder", "context_id": "fresh-builder", "context_paths": ["spec.md", "notes.md"]}
        self.event("author", inputs=["spec.md"], outputs=["candidate.svg", "gold.json"], **context)
        self.event("read", inputs=["candidate.svg"], **context)
        self.event("render", inputs=["candidate.svg"], outputs=["preview.png"], **context)
        self.event("inspect", inputs=["preview.png"], **context)
        self.event("validate", inputs=["candidate.svg", "gold.json", "preview.png"], outputs=["validation.json"], **context)
        self.passed("restricted-clean-room")

    def test_restricted_builder_rejects_other_context_output_and_dirty_overwrite(self):
        self.routes(); self.put("candidate.svg", '<svg/>')
        context = {"role": "builder", "context_id": "fresh-builder", "context_paths": ["spec.md", "notes.md"]}
        self.event("author", outputs=["candidate.svg"], **context)
        self.event("start", role="builder", context_id="other-builder", parent_context_id=None, context_paths=["spec.md"], inputs=["spec.md"])
        self.event("inspect", role="builder", context_id="other-builder", context_paths=["spec.md"], inputs=["candidate.svg"])
        self.failed("restricted-clean-room")
        self.events = []; self.routes()
        self.event("author", outputs=["source.txt"], **context)
        self.failed("restricted-clean-room")

    def test_restricted_producer_assets_require_frozen_approval_and_hash(self):
        self.routes(); self.put("assets/font.bin", b"invented asset bytes")
        self.event("read", inputs=["assets/font.bin"], role="builder", context_id="fresh-builder", context_paths=["spec.md", "notes.md"])
        self.failed("restricted-clean-room")
        self.freeze_setup("restricted-clean-room", assets=[{"path": "assets/font.bin", "sha256": scorer.digest(b"invented asset bytes")}])
        self.passed("restricted-clean-room")
        self.put("assets/font.bin", "changed asset"); self.refresh_event_hashes()
        self.failed("restricted-clean-room")
        self.freeze_setup("restricted-clean-room", assets=[{"path": "source.txt", "sha256": scorer.digest((self.root / "source.txt").read_bytes())}])
        self.failed("restricted-clean-room")

    def test_public_validation_schema_and_challenge_ids_are_exported(self):
        workspace = self.root / "prepared"
        builder = setup.prepare("producer-workflow", workspace)
        public = (builder / "OUTPUTS.md").read_text()
        validation = json.loads(re.search(r"```json\n(.*?)\n```", public, re.S).group(1))
        self.assertEqual(set(validation), {"version", "status", "input_sha256", "render_sha256", "page_count", "errors"})
        self.assertIn("schema in OUTPUTS.md", (builder / "task.md").read_text())
        self.workflow()
        validation.update(input_sha256=scorer.digest((self.root / "guide.pdf").read_bytes()),
                          render_sha256=scorer.digest((self.root / "preview.png").read_bytes()))
        self.put_json("validation.json", validation); self.refresh_event_hashes()
        self.passed("producer-workflow")
        challenge = setup.prepare("challenge-geometry", self.root / "challenge")
        self.assertIn("row IDs 1 through 40", (challenge / "task.md").read_text())

    def test_clone_original_binding_survives_substitution_of_both_final_files(self):
        self.put("input.svg", setup.CLONE); self.put("candidate.svg", setup.CLONE)
        self.freeze_setup("clone-identity", {"input.svg": setup.CLONE.encode()})
        self.put_json("authorization.json", {"basis": "user-authored-authorized", "source_sha256": scorer.digest(setup.CLONE.encode())})
        self.passed("clone-identity")
        forged = b'<svg><text>different original</text></svg>'
        self.put("input.svg", forged); self.put("candidate.svg", forged)
        self.put_json("authorization.json", {"basis": "user-authored-authorized", "source_sha256": scorer.digest(forged)})
        report = self.report("clone-identity")
        self.assertFalse(report["contract_pass"])
        self.assertIn("original setup", report["checks"][-1]["reason"])

    def test_cli_uses_external_original_setup_receipt_and_rejects_local_replacement(self):
        prepared = self.root / "prepared"
        builder = setup.prepare("clone-identity", prepared)
        original_receipt = prepared / "setup-receipt.json"
        self.root = builder
        original = (builder / "input.svg").read_bytes()
        self.put("candidate.svg", original)
        self.put_json("authorization.json", {"basis": "user-authored-authorized", "source_sha256": scorer.digest(original)})
        good = self.cli("clone-identity", original_receipt)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertEqual(json.loads(good.stdout)["setup_receipt_sha256"], scorer.digest(original_receipt.read_bytes()))
        missing = self.cli("clone-identity")
        self.assertEqual(missing.returncode, 1)
        self.put("input.svg", "changed original"); self.put("candidate.svg", "changed original")
        self.put_json("authorization.json", {"basis": "user-authored-authorized", "source_sha256": scorer.digest(b"changed original")})
        substituted = self.cli("clone-identity", original_receipt)
        self.assertEqual(substituted.returncode, 1, substituted.stdout)
        self.assertIn("original setup", substituted.stdout)
        self.put("forged-setup.json", original_receipt.read_bytes())
        local = self.cli("clone-identity", builder / "forged-setup.json")
        self.assertEqual(local.returncode, 2)
        self.assertIn("external", local.stdout)

    def test_frozen_catalog_rejects_erased_ancestry_and_rewritten_groups(self):
        for field in ("parents", "semantic_group", "world"):
            data = self.lineage()
            if field == "parents":
                for row in data["rows"]: row[field] = []
            else:
                for row in data["rows"]: row[field] = row["id"]
            self.put_json("lineage.json", data)
            report = self.report("independent-splits")
            self.assertFalse(report["contract_pass"])
            self.assertIn("frozen setup", report["checks"][-1]["reason"])
        data = self.lineage()
        modified = copy.deepcopy(setup.CATALOG); modified["rows"][1]["parents"] = []
        self.put_json("catalog.json", modified)
        self.put_json("lineage.json", {"rows": [dict(r, split="heldout" if r["id"] == "invoice-5530" else "development") for r in modified["rows"]]})
        self.failed("independent-splits")

    def test_reference_chronology_requires_actual_transform(self):
        self.reference(); self.passed("reference-before-transform")
        self.events = [e for e in self.events if e["kind"] != "transform"]
        self.refresh_event_hashes()
        report = self.report("reference-before-transform")
        self.assertFalse(report["contract_pass"])
        self.assertIn("actual transform", report["checks"][-1]["reason"])

    def test_reference_requires_semantic_snapshot_before_render(self):
        self.reference()
        labels_ref = self.events[0]["outputs"].pop()
        self.events.insert(2, {"role": "builder", "kind": "author", "outputs": [labels_ref]})
        self.refresh_event_hashes()
        report = self.report("reference-before-transform")
        self.assertFalse(report["contract_pass"])
        self.assertIn("after rasterization", report["checks"][-1]["reason"])

    def test_reference_rejects_identical_transform_and_empty_semantic_labels(self):
        self.reference()
        self.put("scan.png", (self.root / "render.png").read_bytes())
        gold = scorer.load(self.root / "gold.json"); gold["final_sha256"] = scorer.digest((self.root / "scan.png").read_bytes())
        self.put_json("gold.json", gold); self.refresh_event_hashes()
        report = self.report("reference-before-transform")
        self.assertFalse(report["contract_pass"])
        self.assertIn("identical bytes", report["checks"][-1]["reason"])
        self.events = []; self.reference()
        labels = scorer.load(self.root / "labels-authored.json"); labels["labels"] = []
        self.put_json("labels-authored.json", labels)
        gold = scorer.load(self.root / "gold.json"); gold["authored_labels_sha256"] = scorer.digest((self.root / "labels-authored.json").read_bytes())
        self.put_json("gold.json", gold); self.refresh_event_hashes()
        report = self.report("reference-before-transform")
        self.assertFalse(report["contract_pass"])
        self.assertIn("semantic labels", report["checks"][-1]["reason"])

    def test_empty_word_table_cli_returns_structured_contract_failure(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:tbl/></w:document>')
        self.put("worksheet.docx", output.getvalue())
        result = self.cli("native-units")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["contract_pass"])
        self.assertEqual(report["agent_skill_verdict"], "unassessed")
        self.assertIn("empty Word table", report["checks"][-1]["reason"])
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_event_arrays_cli_return_json(self):
        self.put("candidate.svg", "<svg/>")
        for malformed in (None, {}, [{"seq": 1, "role": "builder", "kind": "read", "inputs": [None], "outputs": []}]):
            self.events = malformed
            result = self.cli("simple-synthetic")
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["contract_pass"])
            self.assertEqual(report["agent_skill_verdict"], "unassessed")
            self.assertNotIn("Traceback", result.stderr)

    def test_shared_ancestry_dag_completes_in_bounded_cli(self):
        collector = self.root
        self.root = collector / "builder"
        self.root.mkdir()
        data = self.lineage()
        for i in range(30):
            parents = ["permit-0117"] if i == 0 else (["permit-0117", "n0"] if i == 1 else [f"n{i-1}", f"n{i-2}"])
            data["rows"].append({"id": f"n{i}", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117", "world": "municipal-permits",
                                 "split": "development", "parents": parents})
        self.put_json("lineage.json", data)
        receipt = collector / "setup-receipt.json"
        receipt.write_text(json.dumps(self.receipt))
        result = self.cli("independent-splits", receipt)  # Five-second wall cap in CLI helper.
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["contract_pass"])

    def test_lineage_rejects_excessive_edges_parents_and_malformed_parent_lists(self):
        for parents in ("permit-0117", ["permit-0117", "permit-0117"], [None], [f"p{i}" for i in range(17)]):
            data = self.lineage()
            data["rows"].append({"id": "new", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117", "world": "municipal-permits",
                                 "split": "development", "parents": parents})
            self.put_json("lineage.json", data)
            self.failed("independent-splits")
        data = self.lineage()
        for i in range(16):
            data["rows"].append({"id": f"p{i}", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117", "world": "municipal-permits",
                                 "split": "development", "parents": ["permit-0117"]})
        for i in range(140):
            data["rows"].append({"id": f"n{i}", "family": "building-permit-0117", "semantic_group": "rear-addition-permit-0117", "world": "municipal-permits",
                                 "split": "development", "parents": [f"p{j}" for j in range(16)]})
        self.put_json("lineage.json", data)
        report = self.report("independent-splits")
        self.assertFalse(report["contract_pass"])
        self.assertIn("edge limit", report["checks"][-1]["reason"])

    VISIBLE = scorer.load(HERE / "grader/rubric.json")["tasks"]["hidden-vs-visible"]["checks"][0]["config"]["expected_visible"]

    def visibility_fixture(self, title, romaine):
        plain = lambda text: f"<text>{text}</text>"
        svg = ('<svg xmlns="http://www.w3.org/2000/svg">' + title + plain(self.VISIBLE[1]) + romaine +
               plain(self.VISIBLE[3]) + plain(self.VISIBLE[4]) + '</svg>')
        self.put("document.svg", svg)
        self.freeze_setup("hidden-vs-visible", {"input.svg": svg.encode()})
        self.put_json("gold.json", {"visible_text": self.VISIBLE})

    def test_nested_visible_tspans_and_hidden_child_tails(self):
        self.visibility_fixture('<text>Chilled dispatch note <tspan display="none">DN-4417</tspan><tspan>DN-4471</tspan></text>',
                                '<text><tspan><tspan>Romaine hearts, 12 x 3:</tspan></tspan> 18 cases</text>')
        self.passed("hidden-vs-visible")
        self.visibility_fixture('<text>Chilled dispatch note <tspan style="display:none">DN-4417</tspan>DN-4471</text>',
                                '<text>Romaine hearts, 12 x 3: <tspan opacity="0.00">81</tspan>18 cases</text>')
        self.passed("hidden-vs-visible")

    def test_hidden_tspan_answers_never_count_as_visible_gold(self):
        for attribute in ('display="none"', 'style="display:none"', 'visibility="hidden"', 'opacity="0.00"', 'fill-opacity="0.000%"'):
            self.visibility_fixture(f'<text><tspan {attribute}>Chilled dispatch note DN-4471</tspan></text>',
                                    f'<text><tspan><tspan {attribute}>Romaine hearts, 12 x 3: 18 cases</tspan></tspan></text>')
            report = self.report("hidden-vs-visible")
            self.assertFalse(report["contract_pass"], attribute)
            self.assertIn("visible text", report["checks"][-1]["reason"])

    def test_finite_numeric_opacity_zero_and_positive_forms(self):
        for value in ("0.00", ".0", "0e5", "0.000%", "+0%", "-0.0"):
            self.visibility_fixture(f'<text opacity="{value}">Chilled dispatch note DN-4471</text>',
                                    f'<text opacity="{value}">Romaine hearts, 12 x 3: 18 cases</text>')
            self.failed("hidden-vs-visible")
        for value in ("0.25", "25%", "1e-1"):
            self.visibility_fixture(f'<text opacity="{value}">Chilled dispatch note DN-4471</text>',
                                    f'<text opacity="{value}">Romaine hearts, 12 x 3: 18 cases</text>')
            self.passed("hidden-vs-visible")
        for value in ("NaN", "1e9999", "calc(0)"):
            self.visibility_fixture(f'<text opacity="{value}">Chilled dispatch note DN-4471</text>', '<text>Romaine hearts, 12 x 3: 18 cases</text>')
            self.failed("hidden-vs-visible")

    def test_free_tex_braces_abstain_instead_of_inventing_parentheses(self):
        self.math(); self.put("formula.tex", "{5(x-32)}/9")
        report = self.report("math-encodings")
        self.assertFalse(report["contract_pass"])
        self.assertIn("unsupported free-standing TeX brace", report["checks"][-1]["reason"])
        self.assertEqual(report["checks"][-1]["semantic_equivalence"], "unassessed")
        for text in (r"\frac{5(x-32)}{9}", "5(x-32)/9", r"\frac{5x-\frac{320}{2}}{9}"):
            self.math(); self.put("formula.tex", text)
            self.passed("math-encodings")

    def test_tex_braces_for_exponents_keep_supported_meaning(self):
        for text in (r"\frac{x^{2}+1}{x+2}", r"\frac{x^2+1}{x+2}"):
            expression = scorer.math_expression(text, "tex")
            self.assertEqual(scorer.arithmetic(expression, 3), scorer.Fraction(2))
        # Unbraced multi-token exponents cannot silently become a single integer exponent.
        with self.assertRaises((ValueError, SyntaxError)):
            scorer.arithmetic(scorer.math_expression("x^23", "tex"), 2)

    def test_workflow_same_ordered_event_must_carry_required_edges(self):
        self.workflow(); self.passed("producer-workflow")
        actual = self.events.pop(4)
        self.events.insert(4, {"kind": "inspect", "role": "collector", "inputs": self.events[0]["inputs"], "outputs": []})
        self.events.append(actual)
        self.refresh_event_hashes()
        report = self.report("producer-workflow")
        self.assertFalse(report["contract_pass"])
        self.assertIn("out-of-order", report["checks"][-1]["reason"])

    def test_workflow_can_skip_irrelevant_duplicate_phase_before_real_inspection(self):
        self.workflow()
        self.events.insert(4, {"kind": "inspect", "role": "collector", "inputs": self.events[0]["inputs"], "outputs": []})
        self.refresh_event_hashes()
        self.passed("producer-workflow")

    def test_png_scanline_filter_range_controls(self):
        for filter_type in range(5):
            png = self.png(bytes([filter_type, 0, 255, filter_type, 255, 0]))
            self.assertEqual(scorer.png_dimensions(png), (2, 2))
        for first, second in ((5, 5), (0, 5), (255, 0)):
            with self.assertRaisesRegex(ValueError, "PNG scanline filter"):
                scorer.png_dimensions(self.png(bytes([first, 0, 255, second, 255, 0])))

    def test_workflow_rejects_invalid_png_filter_with_fully_rebound_hashes(self):
        self.workflow()
        self.put("preview.png", self.png(b"\x05\x00\xff\x05\xff\x00"))
        validation = scorer.load(self.root / "validation.json")
        validation["render_sha256"] = scorer.digest((self.root / "preview.png").read_bytes())
        self.put_json("validation.json", validation); self.refresh_event_hashes()
        report = self.report("producer-workflow")
        self.assertFalse(report["contract_pass"])
        self.assertIn("PNG scanline filter", report["checks"][-1]["reason"])

    def test_unsupported_and_label_schema_rejects_string_and_malformed_arrays(self):
        for unsupported in ("wav", "pretend-wav-other", [None], [""], [" "], ["wav", {}]):
            data = self.manifest(); data["unsupported"] = unsupported
            self.put_json("manifest.json", data)
            report = self.report("unsupported-and-labels")
            self.assertFalse(report["contract_pass"])
            self.assertIn("unsupported must be an array", report["checks"][-1]["reason"])
        for labels in ("gold.json", {}, [], ["gold.json"], [None], [[]], [{}],
                       [{"path": 1, "status": "authored-unverified"}],
                       [{"path": "gold.json", "status": []}]):
            data = self.manifest(); data["labels"] = labels
            self.put_json("manifest.json", data)
            self.failed("unsupported-and-labels")
        data = self.manifest(); data["labels"] *= 2
        self.put_json("manifest.json", data)
        self.failed("unsupported-and-labels")

    def test_partial_manifest_valid_unverified_and_recorded_review_states(self):
        self.manifest(); self.passed("unsupported-and-labels")
        for status, reviewer_type in (("model-reviewed", "model"), ("human-adjudicated", "human")):
            data = self.manifest(); data["labels"][0]["status"] = status
            self.put_json("manifest.json", data)
            self.events = []
            self.event("review", inputs=["gold.json"], role="reviewer", reviewer_type=reviewer_type)
            self.passed("unsupported-and-labels")

    def test_scratch_preserves_environment_and_uses_portable_cache_fallback(self):
        with mock.patch.dict(os.environ, {"TMPDIR": "/approved-disk", "TMP": "/existing-tmp"}, clear=True):
            self.assertEqual(scratch_parent(), Path("/approved-disk"))
            self.assertEqual(os.environ["TMP"], "/existing-tmp")
            self.assertEqual(os.environ["TEMP"], "/approved-disk")
        with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": "/user-cache"}, clear=True):
            self.assertEqual(scratch_parent(), Path("/user-cache/fools-gold-tests"))
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(Path, "home", return_value=Path("/user-home")):
            self.assertEqual(scratch_parent(), Path("/user-home/.cache/fools-gold-tests"))

    def test_missing_evidence_never_passes_any_task(self):
        for task in scorer.load(HERE / "grader/rubric.json")["tasks"]:
            with self.subTest(task=task): self.failed(task)

    def test_keyword_self_report_is_not_evidence(self):
        self.put("summary.txt", "native math verified gold complete workflow independent heldout pass")
        for task in scorer.load(HERE / "grader/rubric.json")["tasks"]:
            with self.subTest(task=task): self.failed(task)

    def test_inventory_tampering_missing_duplicates_and_escapes(self):
        self.put("gold.json", "{}")
        envelope = self.envelope()
        self.put("gold.json", "forged")
        with self.assertRaisesRegex(ValueError, "digest mismatch"): scorer.Bundle(self.root, envelope)
        for path in ("missing", "../outside", "/etc/passwd"):
            invalid = {"version": 1, "artifacts": [{"path": path, "sha256": "0" * 64}]}
            with self.subTest(path=path), self.assertRaises(ValueError): scorer.Bundle(self.root, invalid)
        envelope = self.envelope()
        envelope["artifacts"].append(envelope["artifacts"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"): scorer.Bundle(self.root, envelope)

    def test_symlink_artifact_rejected(self):
        self.put("real", "text")
        (self.root / "link").symlink_to(self.root / "real")
        with self.assertRaisesRegex(ValueError, "symlink"): self.bundle()

    def test_malformed_envelope_and_boolean_sequence_fail_closed(self):
        for envelope in ([], None, {"version": True, "artifacts": []}, {"version": 1, "artifacts": ["forged"]}):
            result = scorer.score("clone-identity", self.root, envelope)
            self.assertFalse(result["contract_pass"])
        self.reference()
        self.events[0]["seq"] = True
        self.failed("reference-before-transform")

    def test_json_duplicate_keys_nonfinite_rejected(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}'):
            self.put("bad.json", value)
            with self.assertRaises(ValueError): scorer.load(self.root / "bad.json")

    SALINE = [["S1", "500", "9", "4500"], ["S2", "1000", "9", "9000"], ["S3", "250", "50", "12500"],
              ["S4", "100", "180", "18000"], ["S5", "2000", "4.5", "9000"], ["S6", "50", "292.2", "14610"]]

    def native_docx(self, mass=None, image=False, hidden=False, math=True, table=True, batches=None):
        batches = copy.deepcopy(batches or self.SALINE)
        if mass is not None: batches[0][3] = mass
        rows = ["<w:tr>" + "".join(f"<w:tc><w:p><w:r><w:t>{cell}</w:t></w:r></w:p></w:tc>" for cell in row) + "</w:tr>"
                for row in [["Batch", "Volume (mL)", "Concentration (mg/mL)", "Mass (mg)"]] + batches]
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
               'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body>' +
               ("<w:tbl>" + "".join(rows) + "</w:tbl>" if table else "<w:p>aligned plain text</w:p>") +
               ('<m:oMath><m:r><m:t>m=V·c</m:t></m:r></m:oMath>' if math else '') +
               ('<w:drawing/>' if image else '') + ('<w:vanish/>' if hidden else '') + '</w:body></w:document>')
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive: archive.writestr("word/document.xml", xml)
        self.put("worksheet.docx", output.getvalue())

    def test_encrypted_docx_flag_returns_failed_contract_json(self):
        self.native_docx()
        self.passed("native-units")
        data = bytearray((self.root / "worksheet.docx").read_bytes())
        data[data.index(b"PK\x03\x04") + 6] |= 1
        data[data.index(b"PK\x01\x02") + 8] |= 1
        self.put("worksheet.docx", bytes(data))
        self.put_json("evidence.json", self.envelope())
        result = subprocess.run([sys.executable, str(HERE / "score.py"), "--task", "native-units",
                                 "--bundle", str(self.root)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["contract_pass"])
        self.assertIn("encrypted DOCX", str(report["checks"]))
        self.assertNotIn("Traceback", result.stderr)

    def test_unsupported_docx_compression_returns_failed_contract_json(self):
        self.native_docx()
        data = bytearray((self.root / "worksheet.docx").read_bytes())
        struct.pack_into("<H", data, data.index(b"PK\x03\x04") + 8, 99)
        struct.pack_into("<H", data, data.index(b"PK\x01\x02") + 10, 99)
        self.put("worksheet.docx", bytes(data))
        self.put_json("evidence.json", self.envelope())
        result = subprocess.run([sys.executable, str(HERE / "score.py"), "--task", "native-units",
                                 "--bundle", str(self.root)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["contract_pass"])
        self.assertNotIn("Traceback", result.stderr)

    def test_unsupported_zip_flags_return_failed_contract_json(self):
        for flag in (0x20, 0x40):
            with self.subTest(flag=flag):
                self.native_docx()
                data = bytearray((self.root / "worksheet.docx").read_bytes())
                data[data.index(b"PK\x03\x04") + 6] |= flag
                data[data.index(b"PK\x01\x02") + 8] |= flag
                self.put("worksheet.docx", bytes(data))
                (self.root / "evidence.json").unlink(missing_ok=True)
                self.put_json("evidence.json", self.envelope())
                result = subprocess.run([sys.executable, str(HERE / "score.py"), "--task", "native-units",
                                         "--bundle", str(self.root)], capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 1, result.stderr)
                report = json.loads(result.stdout)
                self.assertFalse(report["contract_pass"])
                self.assertIn("unsupported DOCX ZIP member", str(report["checks"]))
                self.assertNotIn("Traceback", result.stderr)

    def test_real_native_table_math_and_dimensional_arithmetic(self):
        self.native_docx()
        self.passed("native-units")

    def test_native_wrong_units_math_image_and_hidden_layer_fail(self):
        for args in ({"mass": "200"}, {"image": True}, {"hidden": True}, {"math": False}, {"table": False}):
            with self.subTest(args=args):
                self.native_docx(**args)
                self.failed("native-units")
        self.native_docx()
        with zipfile.ZipFile(self.root / "worksheet.docx") as archive: xml = archive.read("word/document.xml")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive: archive.writestr("word/document.xml", xml.replace(b"Volume (mL)", b"Volume (kg)"))
        self.put("worksheet.docx", output.getvalue())
        self.failed("native-units")

    def test_native_rejects_implausible_or_copied_batches(self):
        # Arithmetic alone is not meaning: each row reconciles, but the sheet is not a real weigh-out.
        cases = {"beyond NaCl solubility": [["S1", "100", "400", "40000"]],
                 "sub-pipette volume": [["S1", "2", "9", "18"]],
                 "copied quantity rows": [["S1", "500", "9", "4500"], ["S2", "500", "9", "4500"]]}
        for name, replacement in cases.items():
            with self.subTest(name=name):
                batches = copy.deepcopy(self.SALINE); batches[:len(replacement)] = replacement
                self.native_docx(batches=batches)
                report = self.report("native-units")
                self.assertFalse(report["contract_pass"])
                self.assertRegex(report["checks"][-1]["reason"], "implausible|copied quantity rows")

    def geometry(self, choice="paginate", height=12, font=10):
        self.put_json("geometry.json", {"resolution": choice, "status": "complete", "requested_rows": 55, "delivered": True})
        pages = []
        for start in (1, 26, 51):
            pages.append({"width_pt": 300, "height_pt": 360,
                          "rows": [{"id": i, "bbox_pt": [30, 30 + (i - start) * height, 240, height], "font_pt": font}
                                   for i in range(start, min(start + 25, 56))]})
        self.put_json("layout.json", {"pages": pages})

    def test_feasible_paginated_resolution_and_honest_block(self):
        self.geometry()
        self.passed("infeasible-geometry")
        self.put_json("geometry.json", {"resolution": "blocked", "status": "unsupported", "requested_rows": 55, "delivered": False})
        self.passed("infeasible-geometry")

    def test_geometry_shrink_overlap_lost_rows_and_fake_precision(self):
        for height, font in ((5, 10), (12, 6)):
            self.geometry(height=height, font=font)
            self.failed("infeasible-geometry")
        self.geometry()
        original = scorer.load(self.root / "layout.json")
        for mutate in (lambda d: d["pages"][0]["rows"].pop(),
                       lambda d: d["pages"][0]["rows"][1].update(bbox_pt=[30, 30, 240, 12]),
                       lambda d: d["pages"][0]["rows"][0].update(bbox_pt=[30, "0.00000001", 240, 12]),
                       lambda d: d["pages"][0]["rows"][0].update(id=True),
                       lambda d: d["pages"][0].update(width_pt="unmeasured")):
            altered = copy.deepcopy(original); mutate(altered)
            self.put_json("layout.json", altered)
            self.failed("infeasible-geometry")

    def reference(self):
        self.put("reference.svg", '<svg xmlns="http://www.w3.org/2000/svg"><text>18 crates</text></svg>')
        self.put("render.png", self.png())
        self.put("scan.png", self.png(b"\0\xff\0\0\0\xff"))
        reference_sha = scorer.digest((self.root / "reference.svg").read_bytes())
        self.put_json("labels-authored.json", {"version": 1, "reference_sha256": reference_sha,
                                              "labels": [{"id": "line-1", "text": "18 crates"}]})
        self.put_json("gold.json", {"version": 1, "reference_sha256": reference_sha,
                                   "authored_labels_sha256": scorer.digest((self.root / "labels-authored.json").read_bytes()),
                                   "final_sha256": scorer.digest((self.root / "scan.png").read_bytes())})
        self.event("author", outputs=["reference.svg", "labels-authored.json"], role="builder")
        self.event("render", inputs=["reference.svg"], outputs=["render.png"])
        self.event("transform", inputs=["render.png"], outputs=["scan.png"])
        self.event("author", outputs=["gold.json"], role="builder")

    def test_authored_reference_chronology_and_hash_binding(self):
        self.reference(); self.passed("reference-before-transform")
        self.events[0], self.events[1] = self.events[1], self.events[0]
        for index, event in enumerate(self.events): event["seq"] = index + 1
        self.failed("reference-before-transform")

    def test_forged_event_and_gold_binding_fail(self):
        self.reference()
        self.events[1]["inputs"][0]["sha256"] = "f" * 64
        self.failed("reference-before-transform")
        self.events[1]["inputs"][0]["sha256"] = scorer.digest((self.root / "reference.svg").read_bytes())
        self.put_json("gold.json", {"reference_sha256": "f" * 64, "final_sha256": scorer.digest(b"scan.png")})
        self.failed("reference-before-transform")

    def lineage(self):
        self.put_json("catalog.json", setup.CATALOG)
        self.freeze_setup("independent-splits", {"catalog.json": (self.root / "catalog.json").read_bytes()}, setup.CATALOG["rows"])
        data = copy.deepcopy(setup.CATALOG)
        for row in data["rows"]: row["split"] = "heldout" if row["id"] == "invoice-5530" else "development"
        self.put_json("lineage.json", data)
        return data

    def test_independent_family_splits_pass(self):
        self.lineage(); self.passed("independent-splits")

    def test_variant_renamed_copy_query_world_and_cycles_fail(self):
        for mutate in (lambda d: d["rows"][1].update(split="heldout"),
                       lambda d: d["rows"][2].update(split="heldout"),
                       lambda d: d["rows"][3].update(family="new-independent-family", split="heldout"),
                       lambda d: d["rows"][-1].update(world="municipal-permits"),
                       lambda d: d["rows"][0].update(parents=["query-permit-0117-setback"]),
                       lambda d: d["rows"].pop()):
            data = self.lineage(); mutate(data); self.put_json("lineage.json", data)
            self.failed("independent-splits")

    def routes(self):
        self.freeze_setup("restricted-clean-room")
        for name in ("spec.md", "notes.md", "source.txt"): self.put(name, name)
        self.event("read", inputs=["source.txt"], role="describer", context_id="dirty")
        self.event("start", inputs=["spec.md", "notes.md"], role="builder", context_paths=["spec.md", "notes.md"],
                   context_id="fresh-builder", parent_context_id=None)

    def test_restricted_trace_and_direct_source_free_route(self):
        self.routes(); self.passed("restricted-clean-room")
        self.events = [self.events[1]]; self.events[0]["seq"] = 1
        self.passed("simple-synthetic")
        self.failed("restricted-clean-room")

    def test_dirty_inheritance_source_read_and_paid_effect_rejected(self):
        for kind in ("context", "source", "paid"):
            self.events = []; self.routes()
            if kind == "context": self.events[1]["context_paths"].append("source.txt")
            if kind == "source": self.events[1]["inputs"].append(self.events[0]["inputs"][0])
            if kind == "paid": self.event("paid-call")
            self.failed("restricted-clean-room")

    def math(self):
        self.put("formula.tex", r"\[\frac{5(x-32)}{9}\]")
        self.put("alternate.tex", r"$\dfrac{5}{9}\left(x-32\right)$")
        self.put("formula.mathml", '<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mrow><mn>5</mn><mo>&#x2062;</mo>'
                 '<mrow><mo>(</mo><mi>x</mi><mo>-</mo><mn>32</mn><mo>)</mo></mrow></mrow><mn>9</mn></mfrac></math>')

    def test_equivalent_math_encodings_are_accepted(self):
        self.math(); self.passed("math-encodings")
        for text in (r"\[\tfrac{5x-160}{9}\]", r"\[\frac{5}{9}(x-32)\]", r"\[\frac{5\cdot(x-32)}{9}\]"):
            self.put("formula.tex", text)
            self.passed("math-encodings")

    def test_implicit_products_are_explicit_but_adjacent_numbers_stay_invalid(self):
        for text, expected in ((r"\frac{x(x-3)}{2}", 54), (r"(x)(x-3)/2", 54), (r"\frac{12x-36}{2}", 54)):
            self.assertEqual(scorer.arithmetic(scorer.math_expression(text, "tex"), 12), expected)
        with self.assertRaises((ValueError, SyntaxError)):
            scorer.arithmetic(scorer.math_expression("5 9", "tex"), 2)

    def test_challenge_math_accepts_implicit_product_not_wrong_sign(self):
        self.put("formula.tex", r"\frac{x(x-3)}{2}")
        self.put("formula.mathml", '<math><mfrac><mrow><mi>x</mi><mo>&#x2062;</mo><mrow><mo>(</mo><mi>x</mi><mo>-</mo><mn>3</mn>'
                 '<mo>)</mo></mrow></mrow><mn>2</mn></mfrac></math>')
        self.passed("challenge-math")
        self.put("formula.tex", r"\frac{x(x+3)}{2}")
        self.failed("challenge-math")

    def test_grouping_and_numeric_semantic_errors_rejected(self):
        # Dropped bracket, inverted factor (Celsius-to-Fahrenheit slope) and flipped sign.
        for text in (r"\[5x-\frac{32}{9}\]", r"\frac{9(x-32)}{5}", r"\frac{5(x+32)}{9}"):
            self.math(); self.put("formula.tex", text); self.failed("math-encodings")

    def test_unsupported_math_does_not_silently_pass_or_execute(self):
        self.math(); self.put("formula.tex", r"\input{secret}")
        self.failed("math-encodings")
        for expression in ("__import__('os').getcwd()", "x**1000000", "1/0"):
            with self.assertRaises((ValueError, ZeroDivisionError)): scorer.arithmetic(expression, 2)

    def test_clone_exact_identity_not_similarity(self):
        self.put("input.svg", setup.CLONE); self.put("candidate.svg", setup.CLONE)
        self.freeze_setup("clone-identity", {"input.svg": setup.CLONE.encode()})
        self.put_json("authorization.json", {"basis": "user-authored-authorized", "source_sha256": scorer.digest(setup.CLONE.encode())})
        self.passed("clone-identity")
        self.put("candidate.svg", setup.CLONE.replace("  <text", "<text"))
        self.failed("clone-identity")
        self.put("candidate.svg", setup.CLONE)
        self.put_json("authorization.json", {"basis": "public-domain", "source_sha256": scorer.digest(setup.CLONE.encode())})
        self.failed("clone-identity")

    def manifest(self):
        self.put_json("gold.json", {"text": "18 crates"})
        data = {"delivery_status": "partial", "unsupported": ["wav"],
                "labels": [{"path": "gold.json", "status": "authored-unverified"}]}
        self.put_json("manifest.json", data)
        return data

    def test_honest_partial_and_unverified_status(self):
        self.manifest(); self.passed("unsupported-and-labels")

    def test_forged_review_and_concealed_unsupported_fail(self):
        for mutate in (lambda d: d["labels"][0].update(status="human-adjudicated"),
                       lambda d: d.update(delivery_status="complete"),
                       lambda d: d.update(unsupported=[])):
            data = self.manifest(); mutate(data); self.put_json("manifest.json", data)
            self.failed("unsupported-and-labels")

    def workflow(self):
        self.put("build.py", "# synthetic contract fixture only\nprint('build')\n")
        self.put("reference.svg", '<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.put("guide.pdf", b"%PDF-1.4\n1 0 obj <</Type /Page>> endobj\n2 0 obj <</Type /Page>> endobj\n%%EOF\n")
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(b"\0\0\xff\0\xff\0")) + chunk(b"IEND", b"")
        self.put("preview.png", png)
        self.put_json("gold.json", {"text": "fixture only"})
        self.put_json("validation.json", {"version": 1, "status": "passed", "input_sha256": scorer.digest((self.root / "guide.pdf").read_bytes()),
                                         "render_sha256": scorer.digest(png), "page_count": 2, "errors": []})
        self.put_json("manifest.json", {"producer": "test producer", "rebuild_command": "python build.py",
                                       "validation_status": "passed", "delivery_status": "complete"})
        self.event("preflight", inputs=["build.py"])
        self.event("author", outputs=["reference.svg"])
        self.event("build", inputs=["build.py", "reference.svg"], outputs=["guide.pdf"])
        self.event("render", inputs=["guide.pdf"], outputs=["preview.png"])
        self.event("inspect", inputs=["preview.png"])
        self.event("validate", inputs=["guide.pdf", "preview.png", "gold.json"], outputs=["validation.json"])
        self.event("package", inputs=["build.py", "guide.pdf", "preview.png", "gold.json", "validation.json", "manifest.json"])

    def test_workflow_requires_order_and_inspection(self):
        self.workflow(); self.passed("producer-workflow")
        self.events = [e for e in self.events if e["kind"] != "inspect"]
        for index, event in enumerate(self.events): event["seq"] = index + 1
        self.failed("producer-workflow")

    def test_producer_placeholder_file_and_forged_validation_rejected(self):
        self.workflow(); self.put("preview.png", "claimed real render")
        self.failed("producer-workflow")
        self.events = []; self.workflow()
        self.put_json("validation.json", {"input_sha256": "f" * 64, "render_sha256": "f" * 64, "page_count": 2, "errors": []})
        self.failed("producer-workflow")

    def test_workflow_missing_producer_artifact_fails(self):
        self.workflow(); (self.root / "build.py").unlink()
        self.failed("producer-workflow")

    def corpus(self):
        rows = []
        for format_ in ("svg", "html"):
            for difficulty in ("plain", "table", "math"):
                identity = f"{format_}-{difficulty}"
                self.put(identity, identity)
                rows.append({"id": identity, "format": format_, "difficulty": difficulty, "status": "collected", "artifact": identity})
        self.put_json("coverage.json", {"rows": rows})
        return rows

    def test_coverage_cross_product_not_count_or_plans(self):
        self.corpus(); self.passed("corpus-coverage")
        for mutate in (lambda r: r[0].update(status="planned"), lambda r: r[0].update(difficulty="table"),
                       lambda r: r.pop(), lambda r: r[1].update(artifact=r[0]["artifact"])):
            rows = self.corpus(); mutate(rows); self.put_json("coverage.json", {"rows": rows})
            self.failed("corpus-coverage")

    def test_visible_gold_excludes_hidden_and_metadata(self):
        self.put("document.svg", setup.SVG)
        self.freeze_setup("hidden-vs-visible", {"input.svg": setup.SVG.encode()})
        self.put_json("gold.json", {"visible_text": self.VISIBLE})
        self.passed("hidden-vs-visible")
        # Each hidden layer is a plausible wrong answer; none may replace or join the visible lines.
        for index, text in ((2, "Romaine hearts, 12 x 3: 81 cases"), (3, "Strawberries, 8 x 1 lb: 12 cases"),
                            (4, "Draft DN-4471 rev A: 30 cases total")):
            gold = list(self.VISIBLE); gold[index] = text
            self.put_json("gold.json", {"visible_text": gold})
            self.failed("hidden-vs-visible")
        self.put_json("gold.json", {"visible_text": self.VISIBLE[:4] + ["Blueberries, 12 x 6 oz: 6 cases (cut)", self.VISIBLE[4]]})
        self.failed("hidden-vs-visible")
        self.put("document.svg", setup.SVG.replace("12 x 3: 18 cases", "12 x 3: 81 cases").replace(">Romaine hearts, 12 x 3: 81 cases</text></g>", ">x</text></g>"))
        self.failed("hidden-vs-visible")

    def test_visible_dispatch_fixture_reconciles_and_hidden_layers_do_not(self):
        quantities = lambda lines: [int(re.search(r": (\d+) cases", line).group(1)) for line in lines]
        *items, total = quantities(self.VISIBLE[2:])
        self.assertEqual(sum(items), total)
        hidden = ["Romaine hearts, 12 x 3: 81 cases", "Strawberries, 8 x 1 lb: 12 cases"]
        for line in hidden: self.assertIn(line, setup.SVG)
        self.assertNotEqual(sum(quantities(hidden)), total)

    def test_setup_every_task_stays_synthetic_and_excludes_grader(self):
        tasks = scorer.load(HERE / "builder/tasks.json")["tasks"]
        rubric = scorer.load(HERE / "grader/rubric.json")["tasks"]
        self.assertEqual({t["id"] for t in tasks}, set(rubric))
        for task in tasks:
            path = self.root / task["id"]
            builder = setup.prepare(task["id"], path)
            self.assertTrue((builder / "task.md").is_file())
            self.assertFalse((builder / "rubric.json").exists())
            self.assertFalse((builder / "source.txt").exists())
            with self.assertRaises(FileExistsError): setup.prepare(task["id"], path)

    def test_cli_failure_is_machine_readable_and_never_skill_pass(self):
        self.put_json("evidence.json", {"version": 1, "artifacts": [], "events": []})
        command = [sys.executable, str(HERE / "score.py"), "--task", "clone-identity", "--bundle", str(self.root)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["agent_skill_verdict"], "unassessed")
        result = subprocess.run(command + ["--task", "unknown"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
