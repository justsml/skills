"""Authored regression controls; no source corpus or third-party fixtures.

Run: python3 -I -m unittest discover -s skills/fools-gold-datasets/tests -v
"""
import importlib.util
import json
import os
import shutil
import struct
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class CliCase(unittest.TestCase):
    def setUp(self):
        cache_base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        base = Path(os.environ["TMPDIR"]) if os.environ.get("TMPDIR") else cache_base / "fools-gold-tests"
        base.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="validation.", dir=base)
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)

    def write(self, name, value):
        path = self.path / name
        path.write_text(value, encoding="utf-8")
        return str(path)

    def run_cli(self, script, *args):
        return subprocess.run([sys.executable, "-I", str(ROOT / script), *args],
                              capture_output=True, text=True, timeout=20)

    def score(self, report, flag="--judge"):
        return self.run_cli("score.py", "--stage", "judge", flag,
                            self.write("report.json", json.dumps(report)))

    def overlap(self, source, candidate, deny=None, mode="paraphrase"):
        args = ["--source", self.write("source.txt", source), "--candidate",
                self.write("candidate.txt", candidate), "--mode", mode, "--no-length"]
        if deny is not None:
            args += ["--denylist", self.write("deny.txt", deny)]
        return self.run_cli("overlap.py", *args)


class CliTests(CliCase):
    def test_overlap_failure_details_must_match_mode_and_metrics(self):
        source = "amber birch cedar dune elm fir grove heath iris jade"
        result = self.overlap(source, source)
        report = json.loads(result.stdout)
        self.assertEqual(self.score(report, "--overlap").returncode, 1)
        gram_failure = next(f for f in report["failures"] if "-gram overlap" in f)
        for wrong in (gram_failure.replace("8-gram", "7-gram"), gram_failure.replace("1.000", "0.900"),
                      gram_failure.replace("0.02", "0.005"), "shared run of 9 words > 7",
                      "shared run of 10 words > 8", "denylisted terms present: 1",
                      "length ratio 1.00 outside 0.85-1.15"):
            with self.subTest(wrong=wrong):
                bad = {**report, "failures": [*report["failures"], wrong]}
                self.assertEqual(self.score(bad, "--overlap").returncode, 2)
        verbatim = {**report, "mode": "verbatim"}
        self.assertEqual(self.score(verbatim, "--overlap").returncode, 2)
        entity_report = json.loads(self.overlap("Reference passage.", "Prohibited name.", "Prohibited").stdout)
        self.assertEqual(self.score(entity_report, "--overlap").returncode, 1)
        entity_report["failures"] = ["denylisted terms present: 2"]
        self.assertEqual(self.score(entity_report, "--overlap").returncode, 2)

    def test_legitimate_near_threshold_overlap_failure_displays(self):
        scorer = module("score")
        for mode, denominator in (("synthetic", 200), ("public-domain-swap", 200), ("paraphrase", 50)):
            for positions in (denominator - 1, denominator, denominator + 1):
                fraction = 1 / positions
                report = {"mode": mode, "length_checked": False, "source_words": 1,
                          "candidate_words": positions, "length_ratio": positions, "ngram_n": 1,
                          "shared_ngrams": 1, "longest_shared_run": 1,
                          "ngram_overlap": round(fraction, 4), "entity_hits": [],
                          "failures": [f"1-gram overlap {fraction:.3f} > {1 / denominator}"]
                          if positions < denominator else [], "pass": positions >= denominator}
                with self.subTest(mode=mode, positions=positions):
                    self.assertEqual(bool(scorer.overlap_misses("document", report)), positions < denominator)
        # Actual ratios just outside the length band round onto its boundary in
        # both the 3-decimal metric and 2-decimal failure text. They still fail.
        for candidate_count, expected_failure in ((8499, True), (8500, False), (8501, False),
                                                  (11499, False), (11500, False), (11501, True)):
            ratio = candidate_count / 10000
            report = {"mode": "paraphrase", "length_checked": True, "source_words": 10000,
                      "candidate_words": candidate_count, "length_ratio": round(ratio, 3), "ngram_n": 8,
                      "shared_ngrams": 0, "longest_shared_run": 0, "ngram_overlap": 0, "entity_hits": [],
                      "failures": [f"length ratio {ratio:.2f} outside 0.85-1.15"] if expected_failure else [],
                      "pass": not expected_failure}
            with self.subTest(candidate_count=candidate_count):
                self.assertEqual(bool(scorer.overlap_misses("document", report)), expected_failure)
                if expected_failure:
                    for change in ({"mode": "synthetic"}, {"length_checked": False},
                                   {"failures": ["length ratio 0.50 outside 0.85-1.15"]},
                                   {"failures": [f"length ratio {ratio:.2f} outside 0.80-1.20"]}):
                        self.assertEqual(self.score({**report, **change}, "--overlap").returncode, 2)

    def test_contradictory_overlap_failures_review_reproductions(self):
        report = {"status": "complete", "length_checked": False, "mode": "synthetic",
                  "source_words": 10, "candidate_words": 10, "length_ratio": 1,
                  "ngram_n": 8, "ngram_overlap": 0, "shared_ngrams": 0,
                  "longest_shared_run": 0, "entity_hits": [], "failures": [], "pass": True}
        self.assertEqual(self.score(report, "--overlap").returncode, 0)
        for failure in ("8-gram overlap 0.000 > 0.005", "shared run of 0 words > 7",
                        "denylisted terms present: 0"):
            with self.subTest(failure=failure):
                result = self.score({**report, "failures": [failure], "pass": False}, "--overlap")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_impossible_overlap_review_reproduction(self):
        report = {"status": "complete", "length_checked": False, "mode": "synthetic",
                  "source_words": 10, "candidate_words": 10, "length_ratio": 1.0,
                  "ngram_n": 8, "ngram_overlap": 0, "shared_ngrams": 1,
                  "longest_shared_run": 0, "entity_hits": [], "failures": [], "pass": True}
        result = self.score(report, "--overlap")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_shared_ngram_count_run_and_fraction_controls(self):
        report = {"status": "complete", "length_checked": False, "mode": "synthetic",
                  "source_words": 10, "candidate_words": 10, "length_ratio": 1.0,
                  "ngram_n": 8, "ngram_overlap": 0.3333, "shared_ngrams": 1,
                  "longest_shared_run": 8, "entity_hits": [],
                  "failures": ["8-gram overlap 0.333 > 0.005", "shared run of 8 words > 7"], "pass": False}
        self.assertEqual(self.score(report, "--overlap").returncode, 1)
        for change in ({"longest_shared_run": 7}, {"shared_ngrams": 4},
                       {"source_words": 7, "length_ratio": 1.429, "longest_shared_run": 7},
                       {"candidate_words": 7, "length_ratio": 0.7, "longest_shared_run": 7},
                       {"ngram_overlap": 0}, {"ngram_overlap": 0.2}, {"ngram_overlap": 0.8},
                       {"shared_ngrams": 0, "ngram_overlap": 0}, {"ngram_overlap": 0.333333}):
            with self.subTest(change=change):
                result = self.score({**report, **change}, "--overlap")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        # Distinct grams, not positions, form the fraction's denominator.
        result = self.overlap("cedar " * 20, "cedar " * 20)
        self.assertEqual(result.returncode, 1)
        repeated = json.loads(result.stdout)
        self.assertEqual((repeated["shared_ngrams"], repeated["ngram_overlap"]), (1, 1.0))
        self.assertEqual(self.score(repeated, "--overlap").returncode, 1)

    def test_rounded_overlap_zero_and_threshold_bounds(self):
        report = {"status": "complete", "length_checked": False, "mode": "synthetic",
                  "source_words": 1, "candidate_words": 50000, "length_ratio": 50000,
                  "ngram_n": 1, "ngram_overlap": 0, "shared_ngrams": 1,
                  "longest_shared_run": 1, "entity_hits": [], "failures": [], "pass": True}
        # A positive fraction can honestly round to zero at four decimal places.
        self.assertEqual(self.score(report, "--overlap").returncode, 0)
        impossible = {**report, "candidate_words": 19999, "length_ratio": 19999}
        self.assertEqual(self.score(impossible, "--overlap").returncode, 2)
        # Rounding must not hide a necessary threshold failure: 2/397 > .005.
        threshold = {**report, "source_words": 2, "candidate_words": 397, "length_ratio": 198.5,
                     "shared_ngrams": 2, "ngram_overlap": 0.005}
        self.assertEqual(self.score(threshold, "--overlap").returncode, 2)
        threshold.update({"failures": ["1-gram overlap 0.005 > 0.005"], "pass": False})
        self.assertEqual(self.score(threshold, "--overlap").returncode, 1)

    def test_full_overlap_reports_match_rounding_across_denominators(self):
        scorer = module("score")
        # n=1 permits isolated shared tokens without triggering the shared-run
        # gate. Each denominator is realizable with distinct authored tokens.
        for total in (1, 3, 7, 198, 200, 201, 397, 19999, 20001, 50000):
            fraction = 1 / total
            report = {"mode": "synthetic", "source_words": 1, "candidate_words": total,
                      "length_ratio": total, "ngram_n": 1, "shared_ngrams": 1,
                      "longest_shared_run": 1, "ngram_overlap": round(fraction, 4), "entity_hits": [],
                      "failures": [f"1-gram overlap {fraction:.3f} > 0.005"] if fraction > 0.005 else [],
                      "pass": fraction <= 0.005}
            with self.subTest(total=total):
                self.assertEqual(bool(scorer.overlap_misses("document", report)), fraction > 0.005)

    def office_tells(self, xml, part="docProps/core.xml", *args):
        path = self.path / "metadata.docx"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr(part, xml)
        return self.run_cli("check_tells.py", "--text", self.write("candidate.txt", "Annual river observations."),
                            "--file", str(path), *args)

    @staticmethod
    def core_xml(creator):
        return ('<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:d="http://purl.org/dc/elements/1.1/">'
                + creator + '</cp:coreProperties>')

    def test_encrypted_metadata_flag_returns_indeterminate_json(self):
        clean = self.office_tells(self.core_xml('<dc:creator>River Institute</dc:creator>'))
        self.assertEqual(clean.returncode, 0, clean.stderr)
        path = self.path / "metadata.docx"
        data = bytearray(path.read_bytes())
        data[data.index(b"PK\x03\x04") + 6] |= 1
        data[data.index(b"PK\x01\x02") + 8] |= 1
        path.write_bytes(data)
        result = self.run_cli("check_tells.py", "--text", str(self.path / "candidate.txt"), "--file", str(path))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "indeterminate")
        self.assertNotIn("Traceback", result.stderr)

    def test_unsupported_metadata_compression99_returns_indeterminate_json(self):
        clean = self.office_tells(self.core_xml('<dc:creator>River Institute</dc:creator>'))
        self.assertEqual(clean.returncode, 0, clean.stderr)
        path = self.path / "metadata.docx"
        data = bytearray(path.read_bytes())
        struct.pack_into("<H", data, data.index(b"PK\x03\x04") + 8, 99)
        struct.pack_into("<H", data, data.index(b"PK\x01\x02") + 10, 99)
        path.write_bytes(data)
        result = self.run_cli("check_tells.py", "--text", str(self.path / "candidate.txt"), "--file", str(path))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "indeterminate")
        self.assertNotIn("Traceback", result.stderr)

    def test_stored_and_deflated_metadata_controls(self):
        for compression in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            with self.subTest(compression=compression):
                path = self.path / "metadata.docx"
                with zipfile.ZipFile(path, "w", compression=compression) as z:
                    z.writestr("docProps/core.xml", self.core_xml('<dc:creator>River Institute</dc:creator>'))
                result = self.run_cli("check_tells.py", "--text", self.write("candidate.txt", "Annual observations."),
                                      "--file", str(path))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["misses"], [])

    def test_unsupported_zip_flags_return_indeterminate(self):
        for flag in (0x20, 0x40):
            with self.subTest(flag=flag):
                self.office_tells(self.core_xml('<dc:creator>River Institute</dc:creator>'))
                path = self.path / "metadata.docx"
                data = bytearray(path.read_bytes())
                data[data.index(b"PK\x03\x04") + 6] |= flag
                data[data.index(b"PK\x01\x02") + 8] |= flag
                path.write_bytes(data)
                result = self.run_cli("check_tells.py", "--text", str(self.path / "candidate.txt"), "--file", str(path))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "indeterminate")
                self.assertNotIn("Traceback", result.stderr)

    def test_office_metadata_review_reproductions(self):
        for creator in ('<dc:creator>python-docx</dc:creator>', '<dc:creator>python&#45;docx</dc:creator>',
                        '<dc:creator><![CDATA[python-docx]]></dc:creator>', '<d:creator>python-docx</d:creator>'):
            with self.subTest(creator=creator):
                result = self.office_tells(self.core_xml(creator))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(len(report["misses"]), 1)
                self.assertIn("python-docx", report["misses"][0]["summary"])
                self.assertEqual(report["misses"][0]["severity"], "medium")
                scored = self.score(report, "--misses")
                self.assertEqual(scored.returncode, 0, scored.stdout + scored.stderr)
        malformed = self.office_tells(self.core_xml('<dc:creator>python-docx'))
        self.assertEqual(malformed.returncode, 2, malformed.stdout + malformed.stderr)
        self.assertEqual(json.loads(malformed.stdout)["status"], "indeterminate")

    def test_decoded_office_metadata_supported_clean_and_producer_controls(self):
        clean = self.office_tells(self.core_xml('<d:creator>River Institute</d:creator><dc:title>Annual observations</dc:title>'))
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        self.assertEqual(json.loads(clean.stdout)["misses"], [])
        empty = self.office_tells(self.core_xml(""))
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        for xml, part in (
            ('<p:Properties xmlns:p="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
             '<p:Application>python&#x2d;docx</p:Application></p:Properties>', "docProps/app.xml"),
            ('<o:document-meta xmlns:o="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
             'xmlns:m="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"><o:meta>'
             '<m:generator><![CDATA[python-docx]]></m:generator></o:meta></o:document-meta>', "meta.xml"),
            (self.core_xml('<dc:creator>python<!--no text-->-docx</dc:creator>'), "docProps/core.xml"),
            (('<?xml version="1.0" encoding="UTF-16"?>' + self.core_xml('<dc:creator>python-docx</dc:creator>')).encode("utf-16"),
             "docProps/core.xml")):
            with self.subTest(part=part, xml=xml):
                result = self.office_tells(xml, part)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["misses"][0]["severity"], "medium")
                self.assertIn("python-docx", report["misses"][0]["summary"])
                self.assertEqual(self.score(report, "--misses").returncode, 0)

    def test_office_xml_unsupported_or_excessive_is_indeterminate(self):
        dtd = '<!DOCTYPE cp:coreProperties [<!ENTITY producer "python-docx">]>'
        inputs = [dtd + self.core_xml('<dc:creator>&producer;</dc:creator>'),
                  '<!DOCTYPE cp:coreProperties SYSTEM "file:///nonexistent-authored-test">' + self.core_xml(""),
                  ('<?xml version="1.0" encoding="UTF-16"?>' + dtd + self.core_xml("")).encode("utf-16"),
                  self.core_xml('<dc:creator><child>python-docx</child></dc:creator>'),
                  self.core_xml('<dc:creator>&unbound;</dc:creator>'),
                  '<coreProperties><creator>python-docx</creator></coreProperties>',
                  self.core_xml('<wrong:creator xmlns:wrong="urn:unsupported">python-docx</wrong:creator>'),
                  self.core_xml('<dc:creator>' + 'a' * 200000 + '</dc:creator>'),
                  self.core_xml('<branch>' * 70 + '</branch>' * 70),
                  self.core_xml('<branch/>' * 4100)]
        for index, xml in enumerate(inputs):
            with self.subTest(index=index):
                result = self.office_tells(xml)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["status"], "indeterminate")
                self.assertEqual(self.score(report, "--misses").returncode, 2)

    def test_duplicate_metadata_fields_are_all_inspected(self):
        result = self.office_tells(self.core_xml('<dc:creator>River Institute</dc:creator>'
                                               '<dc:creator>python&#45;docx</dc:creator>'))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["misses"]), 1)

    def test_review_malformed_reports_fail_closed(self):
        reports = [{}, {"error": "review unavailable"}, [], None, {"misses": None},
                   {"misses": ["not a miss"]},
                   {"misses": [{"category": "leekk", "severity": "FATAL", "summary": "copied source"}]}]
        for report in reports:
            with self.subTest(report=report):
                result = self.score(report)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn('"decision": "pass"', result.stdout)

    def test_review_valid_controls(self):
        clean = self.score({"misses": []})
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertEqual(json.loads(clean.stdout)["score"], 100)
        leak = self.score({"misses": [{"category": "leak", "severity": "low", "cause": "build",
                                        "where": "document", "summary": "protected content"}]})
        self.assertEqual(leak.returncode, 1, leak.stderr)
        self.assertEqual(json.loads(leak.stdout)["decision"], "rewrite-spec")
        self.assertEqual(json.loads(leak.stdout)["score"], 0)

    def test_review_enum_and_field_validation(self):
        valid = {"category": "layout", "severity": "low", "cause": "build",
                 "where": "page1", "summary": "minor spacing"}
        for field, value in (("category", "leekk"), ("severity", "FATAL"), ("cause", "builder"),
                             ("where", []), ("summary", " "), ("category", {})):
            with self.subTest(field=field, value=value):
                self.assertEqual(self.score({"misses": [{**valid, field: value}]}).returncode, 2)
        for field in valid:
            self.assertEqual(self.score({"misses": [{k: v for k, v in valid.items() if k != field}]}).returncode, 2)
        self.assertEqual(self.score({"misses": [valid]}).returncode, 0)
        self.assertEqual(self.score({"misses": [], "error": "unavailable"}).returncode, 2)
        self.assertEqual(self.score({"misses": [], "status": "indeterminate"}).returncode, 2)

    def test_invalid_report_does_not_append_history(self):
        history = self.write("attempts.jsonl", "")
        result = self.run_cli("score.py", "--judge", self.write("bad.json", "{}"), "--history", history)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(Path(history).read_text(), "")

    def test_duplicate_json_fields_rejected(self):
        result = self.run_cli("score.py", "--judge", self.write("duplicate.json", '{"misses":[{}],"misses":[]}'))
        self.assertEqual(result.returncode, 2)

    def test_overlap_report_schema_and_valid_controls(self):
        result = self.overlap("Quiet water flows through a narrow canyon.", "Clear skies above the remote mountains.")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(self.score(report, "--overlap").returncode, 0)
        legacy = {k: v for k, v in report.items() if k not in ("status", "tokenization", "length_checked")}
        self.assertEqual(self.score(legacy, "--overlap").returncode, 0)
        for bad in ({}, {"failures": []}, {"pass": True, "failures": []},
                    {**report, "pass": "true"}, {**report, "failures": ""},
                    {**report, "length_ratio": float("nan")},
                    {**report, "source_words": True}, {**report, "entity_hits": ["prohibited"]},
                    {**report, "status": "indeterminate"},
                    {**report, "longest_shared_run": 8},
                    {**report, "failures": ["review unavailable"], "pass": False}):
            with self.subTest(bad=bad):
                self.assertEqual(self.score(bad, "--overlap").returncode, 2)
        leak = self.overlap("The private Cedar-Bridge index.", "New Cedar-Bridge chart.", "Cedar-Bridge")
        scored = self.score(json.loads(leak.stdout), "--overlap")
        self.assertEqual(scored.returncode, 1, scored.stdout + scored.stderr)
        self.assertEqual(json.loads(scored.stdout)["counts"]["fatal"], 1)
        self.assertNotIn("Cedar-Bridge", scored.stdout)

    def test_denylist_review_reproductions(self):
        controls = [
            ("The secret Zephyr-Labs ledger contains protected text.", "Zephyr-Labs makes unrelated tools.",
             "Zephyr-Labs", "paraphrase"),
            ("项目报告 商业秘密 不可分享 alpha", "项目报告 商业秘密 不可分享 beta", "商业秘密", "synthetic"),
        ]
        for source, candidate, deny, mode in controls:
            with self.subTest(deny=deny):
                result = self.overlap(source, candidate, deny, mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertTrue(json.loads(result.stdout)["entity_hits"])

    def test_contextual_tell_exception(self):
        result = self.run_cli("check_tells.py", "--text",
                              self.write("text.txt", "Advances in synthetic biology."),
                              "--allow", "synthetic biology")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["misses"], [])

    def test_unicode_punctuation_denylist_and_boundaries(self):
        controls = [("ZEPHYR—LABS ships crates.", "Zephyr-Labs"),
                    ("The CAFE\u0301 team arrives.", "Café"),
                    ("Проект СЕВЕР starts.", "север"),
                    ("这里包含商业秘密文本。", "商业秘密"),
                    ("ＡＬＰＨＡ arrives.", "alpha"),
                    ("An O’Neill memo.", "O'Neill")]
        for candidate, deny in controls:
            with self.subTest(deny=deny):
                result = self.overlap("Distinct authored reference sentence.", candidate, deny)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["entity_hits"], [deny])
        for candidate, deny in (("Cafeteria chairs.", "café"), ("AlphaBeta chairs.", "alpha"),
                                ("Zephyr laboratories.", "Zephyr-Labs"), ("A concatenate call.", "cat")):
            result = self.overlap("Distinct authored reference sentence.", candidate, deny)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unsupported_overlap_is_not_a_pass(self):
        for candidate, deny in (("ภาษาไทย alpha", None), ("Hello\ufffd world", None),
                                ("Hello\u200b world", None), ("Valid text", "***"), ("!!!", None)):
            result = self.overlap("Another reference passage.", candidate, deny)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "indeterminate")
            self.assertFalse(json.loads(result.stdout)["pass"])
            self.assertEqual(self.score(json.loads(result.stdout), "--overlap").returncode, 2)

    def test_tell_exception_is_local_and_has_locations(self):
        text = "Advances in synthetic biology.\nThis is synthetic data."
        result = self.run_cli("check_tells.py", "--text", self.write("text.txt", text),
                              "--allow", "synthetic biology")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        misses = json.loads(result.stdout)["misses"]
        self.assertEqual(len(misses), 1)
        self.assertEqual(misses[0]["start"], text.rindex("synthetic"))
        self.assertEqual(misses[0]["line"], 2)
        self.assertEqual(text[misses[0]["start"]:misses[0]["end"]], "synthetic")
        self.assertEqual(self.score({"misses": misses}, "--misses").returncode, 1)

    def test_invalid_allow_or_unavailable_metadata_is_indeterminate(self):
        path = self.write("clean.txt", "Annual report on river flows.")
        for args in (("--allow", "["), ("--file", str(self.path / "missing.pdf")),
                     ("--file", self.write("unsupported.bin", "not an office file"))):
            result = self.run_cli("check_tells.py", "--text", path, *args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "indeterminate")
            self.assertEqual(self.score(json.loads(result.stdout), "--misses").returncode, 2)

    def test_metadata_allow_uses_its_own_context(self):
        office = self.path / "authored.docx"
        with zipfile.ZipFile(office, "w") as z:
            z.writestr("docProps/core.xml", self.core_xml('<dc:title>Advances in synthetic biology.</dc:title>'
                                                        '<dc:subject>This is synthetic data.</dc:subject>'))
        result = self.run_cli("check_tells.py", "--text", self.write("text.txt", "Annual report."),
                              "--file", str(office), "--allow", "synthetic biology")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        misses = json.loads(result.stdout)["misses"]
        self.assertEqual(len(misses), 1)
        self.assertIn("dc:subject", misses[0]["where"])

    def test_length_failure_keeps_existing_scoring_behavior(self):
        result = self.run_cli("overlap.py", "--source", self.write("source.txt", "one two three four five six"),
                              "--candidate", self.write("candidate.txt", "different text"), "--mode", "paraphrase")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        scored = self.score(json.loads(result.stdout), "--overlap")
        self.assertEqual(scored.returncode, 1, scored.stdout + scored.stderr)
        self.assertEqual(json.loads(scored.stdout)["counts"]["high"], 1)
        self.assertIn("content-length", json.loads(scored.stdout)["by_category"])


class RecurrenceTests(CliCase):
    def test_agreeing_reviewers_incur_one_penalty(self):
        for cause, decision in (("build", "revise-build"), ("spec", "rewrite-spec"), ("unknown", "revise-build")):
            with self.subTest(cause=cause):
                miss = {"category": "table", "severity": "high", "cause": cause,
                        "where": "page 1 header", "summary": "Merged units header missing"}
                result = self.run_cli("score.py", "--judge", self.write("judge.json", json.dumps({"misses": [miss]})),
                                      "--audit", self.write("audit.json", json.dumps({"misses": [miss]})))
                report = json.loads(result.stdout)
                self.assertEqual((report["decision"], report["score"]), (decision, 85))
                merged = report["by_category"]["table"][0]
                self.assertFalse(merged["cause_disagreement"])
                self.assertFalse(merged["severity_disagreement"])
                self.assertEqual(len(merged["reports"]), 2)
                self.assertEqual({r["source"] for r in merged["reports"]}, {"judge", "audit"})

    def test_reviewer_severity_disagreement_in_both_orders(self):
        for first, second in (("low", "high"), ("high", "low")):
            with self.subTest(first=first, second=second):
                base = {"category": "table", "cause": "build", "where": "header", "summary": "Missing span"}
                judge = self.write("judge.json", json.dumps({"misses": [{**base, "severity": first}]}))
                audit = self.write("audit.json", json.dumps({"misses": [{**base, "severity": second}]}))
                result = self.run_cli("score.py", "--judge", judge, "--audit", audit)
                report = json.loads(result.stdout)
                self.assertEqual((report["decision"], report["score"]), ("diagnose", 85))
                merged = report["by_category"]["table"][0]
                self.assertTrue(merged["severity_disagreement"])
                self.assertFalse(merged["cause_disagreement"])
                self.assertEqual({(r["source"], r["reported_severity"], r["report"]) for r in merged["reports"]},
                                 {("judge", first, judge), ("audit", second, audit)})
                exhausted = self.run_cli("score.py", "--judge", judge, "--audit", audit, "--round", "4")
                self.assertEqual(json.loads(exhausted.stdout)["decision"], "stop")

    def test_cosmetic_disagreement_retains_records_without_critical_gate(self):
        base = {"category": "typography", "severity": "low", "where": "title", "summary": "Minor spacing"}
        result = self.run_cli("score.py", "--judge", self.write("judge.json", json.dumps({
            "misses": [{**base, "cause": "build"}]})), "--audit", self.write("audit.json", json.dumps({
            "misses": [{**base, "cause": "spec"}]})))
        report = json.loads(result.stdout)
        self.assertEqual((result.returncode, report["decision"], report["score"]), (0, "pass", 99))
        self.assertTrue(report["by_category"]["typography"][0]["cause_disagreement"])
        self.assertEqual(len(report["by_category"]["typography"][0]["reports"]), 2)

    def test_reviewer_cause_disagreement_in_both_orders(self):
        miss = {"category": "table", "severity": "high", "where": "page 1 header",
                "summary": "Merged units header missing"}
        for judge_cause, audit_cause in (("build", "spec"), ("spec", "build")):
            with self.subTest(judge=judge_cause, audit=audit_cause):
                result = self.run_cli("score.py", "--judge", self.write("judge.json", json.dumps({
                    "misses": [{**miss, "cause": judge_cause}]})), "--audit", self.write("audit.json", json.dumps({
                    "misses": [{**miss, "cause": audit_cause}]})))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual((report["decision"], report["score"]), ("diagnose", 85))
                self.assertEqual(report["counts"]["high"], 1)
                merged = report["by_category"]["table"]
                self.assertEqual(len(merged), 1)
                self.assertTrue(merged[0]["cause_disagreement"])
                self.assertEqual(merged[0]["cause"], "unknown")
                self.assertEqual({(r["source"], r["cause"], r["reported_severity"]) for r in merged[0]["reports"]},
                                 {("judge", judge_cause, "high"), ("audit", audit_cause, "high")})
                self.assertEqual(report["spec_learnings"], [])

    HEADER = {"category": "table", "severity": "high", "cause": "build", "where": "p2.header",
              "summary": "Builder dropped the merged header explicitly required by the correct spec"}
    COSMETIC = {"category": "typography", "severity": "low", "cause": "build", "where": "p1.title",
                "summary": "minor title spacing"}

    def attempt(self, misses, attempt=1, round_=1, history=None, **limits):
        args = ["--judge", self.write("review.json", json.dumps({"misses": misses})),
                "--attempt", str(attempt), "--round", str(round_)]
        if history is not None:
            args += ["--history", history]
        for flag, value in limits.items():
            args += ["--" + flag.replace("_", "-"), str(value)]
        result = self.run_cli("score.py", *args)
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_twice_dropped_header_diagnoses_without_inventing_spec_cause(self):
        for cause in ("build", "unknown"):
            with self.subTest(cause=cause):
                history = self.write("history.jsonl", "")
                miss = {**self.HEADER, "cause": cause}
                _, first = self.attempt([miss], history=history)
                self.assertEqual(first["decision"], "revise-build")
                code, second = self.attempt([miss], round_=2, history=history)
                self.assertEqual(code, 1)
                self.assertEqual(second["decision"], "diagnose")
                actual = second["by_category"]["table"][0]
                self.assertEqual(actual["cause"], cause)
                self.assertEqual(actual["severity"], "high")
                self.assertTrue(actual["recurring_within_attempt"])
                self.assertFalse(actual["recurring_across_attempts"])
                self.assertTrue(second["diagnosis_notes"])
                self.assertEqual(second["spec_learnings"], [])
                self.assertEqual(second["builder_notes"], [])

    def test_cross_attempt_build_defect_still_diagnoses(self):
        history = self.write("history.jsonl", "")
        self.attempt([self.HEADER], history=history)
        code, result = self.attempt([self.HEADER], attempt=2, history=history)
        self.assertEqual((code, result["decision"]), (1, "diagnose"))
        miss = result["by_category"]["table"][0]
        self.assertTrue(miss["recurring_across_attempts"])
        self.assertFalse(miss["recurring_within_attempt"])
        self.assertEqual((miss["severity"], miss["cause"]), ("high", "build"))

    def test_repeated_cosmetic_remains_eligible(self):
        history = self.write("history.jsonl", "")
        self.attempt([self.COSMETIC], history=history)
        self.attempt([self.COSMETIC], round_=2, history=history)
        self.attempt([self.COSMETIC], attempt=2, history=history)
        code, result = self.attempt([self.COSMETIC], attempt=2, round_=2, history=history)
        self.assertEqual((code, result["decision"], result["score"]), (0, "pass", 99))
        miss = result["by_category"]["typography"][0]
        self.assertTrue(miss["recurring_within_attempt"])
        self.assertTrue(miss["recurring_across_attempts"])
        self.assertEqual((miss["severity"], miss["cause"]), ("low", "build"))
        self.assertEqual(result["counts"]["high"], 0)
        self.assertEqual(result["diagnosis_notes"], [])

    def test_repeated_medium_preserves_severity_and_critical_gate(self):
        history = self.write("history.jsonl", "")
        medium = {**self.COSMETIC, "severity": "medium"}
        self.attempt([medium], history=history)
        code, result = self.attempt([medium], attempt=2, history=history)
        self.assertEqual((code, result["decision"], result["score"]), (0, "pass", 95))
        self.assertEqual(result["by_category"]["typography"][0]["severity"], "medium")
        code, result = self.attempt([medium, self.HEADER], attempt=2, round_=2, history=history)
        self.assertEqual((code, result["decision"]), (1, "revise-build"))
        self.assertFalse(result["pass"])
        self.assertEqual(result["counts"]["high"], 1)

    def test_genuine_spec_failure_and_leak_retain_rewrite_behavior(self):
        for miss in ({**self.HEADER, "cause": "spec", "summary": "spec omitted the merged header"},
                     {"category": "leak", "severity": "low", "cause": "build", "where": "document",
                      "summary": "protected expression"}):
            with self.subTest(miss=miss):
                code, result = self.attempt([miss], round_=4)
                self.assertEqual((code, result["decision"]), (1, "rewrite-spec"))
                self.assertTrue(result["spec_learnings"])
                _, exhausted = self.attempt([miss], attempt=3, round_=4)
                self.assertEqual(exhausted["decision"], "stop")

    def test_exhausted_build_lane_stops_without_spec_rewrite(self):
        history = self.write("history.jsonl", "")
        self.attempt([self.HEADER], round_=1, history=history)
        code, result = self.attempt([self.HEADER], round_=2, max_rounds=2, history=history)
        self.assertEqual((code, result["decision"]), (1, "stop"))
        self.assertEqual(result["by_category"]["table"][0]["cause"], "build")
        self.assertTrue(any("build rounds exhausted" in x for x in result["reasons"]))

    def test_last_spec_attempt_can_diagnose_with_build_budget(self):
        history = self.write("history.jsonl", "")
        self.attempt([self.HEADER], attempt=3, history=history)
        _, result = self.attempt([self.HEADER], attempt=3, round_=2, history=history)
        self.assertEqual(result["decision"], "diagnose")

    def test_plateau_stops_failed_diagnosis_but_not_eligible_cosmetic(self):
        history = self.write("history.jsonl", "")
        self.attempt([self.HEADER], history=history)
        self.attempt([self.HEADER], attempt=2, history=history)
        code, result = self.attempt([self.HEADER], attempt=3, history=history)
        self.assertEqual((code, result["decision"]), (1, "stop"))
        self.assertTrue(any("plateau" in reason for reason in result["reasons"]))
        cosmetic_history = self.write("cosmetic-history.jsonl", "")
        for attempt in (1, 2, 3):
            code, result = self.attempt([self.COSMETIC], attempt=attempt, history=cosmetic_history)
        self.assertEqual((code, result["decision"]), (0, "pass"))

    def test_patience_also_bounds_evidenced_spec_rewrites(self):
        history = self.write("history.jsonl", "")
        miss = {**self.HEADER, "cause": "spec", "summary": "spec omitted header span"}
        self.attempt([miss], history=history)
        _, result = self.attempt([miss], attempt=2, history=history, patience=1)
        self.assertEqual(result["decision"], "stop")
        self.assertTrue(any("plateau" in reason for reason in result["reasons"]))

    def test_legacy_history_still_flags_serious_recurrence(self):
        history = self.write("history.jsonl", json.dumps({"attempt": 1, "round": 1, "score": 85,
                                                        "serious_keys": [["table", "p2.header"]]}) + "\n")
        _, result = self.attempt([self.HEADER], round_=2, history=history)
        self.assertEqual(result["decision"], "diagnose")
        self.assertTrue(result["by_category"]["table"][0]["recurring_within_attempt"])

    def test_low_score_alone_is_not_evidence_of_spec_failure(self):
        misses = [{**self.COSMETIC, "severity": "medium", "where": f"p{i}.title"} for i in range(11)]
        code, result = self.attempt(misses)
        self.assertEqual((code, result["decision"], result["score"]), (1, "diagnose", 45))
        _, exhausted = self.attempt(misses, round_=4)
        self.assertEqual(exhausted["decision"], "stop")

    def test_out_of_budget_arguments_are_usage_errors(self):
        path = self.write("clean.json", '{"misses": []}')
        for args in (("--attempt", "4", "--max-attempts", "3"), ("--round", "5", "--max-rounds", "4")):
            result = self.run_cli("score.py", "--judge", path, *args)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('"decision": "pass"', result.stdout)


class ProfileTests(CliCase):
    def authored_pdf(self):
        """A real one-page PDF authored here, including hostile metadata strings."""
        xmp = (b'<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Hidden Toolkit Phrase">'
               b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
               b'<rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" '
               b'xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmlns:HiddenNamespace="urn:invented">'
               b'<xmp:CreatorTool>Hidden Creator Phrase</xmp:CreatorTool>'
               b'<pdf:Producer>Hidden Producer Phrase</pdf:Producer>'
               b'</rdf:Description></rdf:RDF></x:xmpmeta>')
        content = b'BT /F1 12 Tf 20 100 Td (Annual river observations.) Tj ET\n'
        objects = [b'<< /Type /Catalog /Pages 2 0 R /Metadata 7 0 R >>',
                   b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
                   b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] '
                   b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
                   b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
                   b'<< /Length %d >>\nstream\n' % len(content) + content + b'endstream',
                   b'<< /Creator (Private Project Zephyr-Labs) /Producer (Confidential Contract Text) '
                   b'/Author (Hidden Author Phrase) /Title (Hidden Title Phrase) >>',
                   b'<< /Type /Metadata /Subtype /XML /Length %d >>\nstream\n' % len(xmp) + xmp + b'\nendstream']
        data = bytearray(b'%PDF-1.4\n')
        offsets = [0]
        for i, obj in enumerate(objects, 1):
            offsets.append(len(data))
            data.extend(f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n')
        xref = len(data)
        data.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
        for offset in offsets[1:]:
            data.extend(f'{offset:010d} 00000 n \n'.encode())
        data.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R /Info 6 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
        path = self.path / "authored.pdf"
        path.write_bytes(data)
        return str(path)

    @unittest.skipUnless(all(shutil.which(x) for x in ("pdfinfo", "pdffonts", "pdfimages", "qpdf")),
                         "actual PDF integration requires installed Poppler and qpdf; not a validation pass")
    def test_real_pdf_dirty_and_handoff_profiles(self):
        pdf = self.authored_pdf()
        raw = self.run_cli("file_profile.py", "profile", pdf)
        self.assertEqual(raw.returncode, 0, raw.stdout + raw.stderr)
        report = json.loads(raw.stdout)
        self.assertEqual(report["profile_kind"], "raw-dirty")
        self.assertEqual(report["docinfo"]["Creator"], "Private Project Zephyr-Labs")
        self.assertEqual(report["docinfo"]["Producer"], "Confidential Contract Text")
        self.assertIsInstance(report["docinfo"]["Author"], dict)
        self.assertIn("Hidden Toolkit Phrase", raw.stdout)
        clean = self.run_cli("file_profile.py", "profile", "--handoff", pdf)
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        handoff = json.loads(clean.stdout)
        self.assertEqual(handoff["profile_kind"], "sanitized-handoff")
        for phrase in ("Private Project", "Zephyr-Labs", "Confidential Contract Text", "Hidden", "Helvetica"):
            self.assertNotIn(phrase, clean.stdout)
        self.assertEqual(handoff["structure"]["header_version"], [1, 4])
        self.assertEqual(handoff["pages"]["size_points"], [200.0, 200.0])
        self.assertEqual(handoff["pages"]["count"], 1)
        compared = self.run_cli("file_profile.py", "compare", self.write("raw.json", raw.stdout), pdf)
        self.assertEqual(compared.returncode, 0, compared.stdout + compared.stderr)
        self.assertEqual(json.loads(compared.stdout)["misses"], [])
        legacy = {k: v for k, v in report.items() if k not in ("profile_kind", "sharing")}
        legacy["profile_version"] = 1
        compared = self.run_cli("file_profile.py", "compare", self.write("v1.json", json.dumps(legacy)), pdf)
        self.assertEqual(compared.returncode, 0, compared.stdout + compared.stderr)
        compared = self.run_cli("file_profile.py", "compare", self.write("clean.json", clean.stdout), pdf)
        self.assertEqual(compared.returncode, 2)
        self.assertIn("handoff profiles are not comparison targets", compared.stderr)

    def test_handoff_omits_all_source_string_channels(self):
        p = module("file_profile")
        secret = "PrivateMetadataPayload"
        raw = {"structure": {"encryption": [secret], "header_version": secret, "eol": secret},
               "docinfo": {"Creator": "Adobe Acrobat " + secret, "Producer": secret,
                           "Title": {"pattern": secret, "extension": secret, "length": 10},
                           "CreationDate": {"raw_form": secret, "timezone": secret, "precision_digits": 14}},
               "xmp": {"toolkit": secret, "producer": secret, "pdfa": secret, "pdfua": secret,
                       "dc_format": secret, "namespaces": [secret]},
               "fonts": {"families": [secret], "types": {secret: 1}, "encodings": {secret: 2}},
               "images": {"colors": {secret: 1}, "encodings": {secret: 1}},
               "jpeg": {"exif_tools": {secret: 1}, "jfif_versions": {secret: 1}, "subsampling": {secret: 1}},
               "pages": {"size": secret, "rotation": secret}, secret: secret}
        result = p.handoff_profile(raw)
        serialized = json.dumps(result)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("Adobe Acrobat", serialized)
        self.assertEqual(result["fonts"]["types"], {"distinct_count": 1, "total_count": 1})
        self.assertEqual(result["docinfo"]["Creator"]["length"], len("Adobe Acrobat " + secret))
        with self.assertRaisesRegex(ValueError, "handoff profiles"):
            p.compare(result, result)

    def test_failed_jpeg_inspection_is_not_no_images(self):
        p = module("file_profile")
        with patch.object(p, "run", side_effect=subprocess.CalledProcessError(1, ["pdfimages"])):
            with self.assertRaises(subprocess.CalledProcessError):
                p.jpegs("invented.pdf")


if __name__ == "__main__":
    unittest.main()
