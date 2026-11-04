"""Conversion failure controls; converter boundaries are mocked, not rendered."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "pdf_variants.py"
spec = importlib.util.spec_from_file_location("pdf_variants", SCRIPT)
variants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(variants)


class VariantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pdf-variants-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "base.pdf"
        self.source.write_bytes(b"%PDF-1.6\nsource")
        self.out = self.root / "outputs"

    def invoke(self, preset="web-1.6-linearized", extra=()):
        args = [str(SCRIPT), str(self.source), "--out", str(self.out), "--presets", preset, *extra]
        stdout = io.StringIO()
        with patch("sys.argv", args), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            code = variants.main()
        return code, json.loads(stdout.getvalue()) if stdout.getvalue() else None

    def rows(self):
        return [json.loads(line) for line in (self.out / "variants.jsonl").read_text().splitlines()]

    def test_existing_run_is_untouched_and_converter_not_called(self):
        self.out.mkdir()
        old = self.out / "base.web-1.6-linearized.pdf"
        old.write_bytes(b"previous artifact")
        log = self.out / "variants.jsonl"
        log.write_text("previous manifest\n")
        with patch.object(variants, "qpdf_pass", return_value=None) as converter, patch.object(variants, "summarize", return_value={"header_version": "1.6"}):
            code, _ = self.invoke()
        self.assertNotEqual(code, 0)
        converter.assert_not_called()
        self.assertEqual(old.read_bytes(), b"previous artifact")
        self.assertEqual(log.read_text(), "previous manifest\n")

    def test_failed_qpdf_partial_output_never_publishes(self):
        def fail(cmd, **kwargs):
            Path(cmd[-1]).write_bytes(b"%PDF-1.6\npartial")
            return subprocess.CompletedProcess(cmd, 2, b"", b"synthetic conversion failure")
        with patch.object(variants, "run", side_effect=fail):
            code, summary = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(summary["failed"], 1)
        self.assertIsNone(self.rows()[0]["file"])
        self.assertFalse(list(self.out.glob("*.pdf")))

    def test_warning_success_publishes_fresh_bytes(self):
        def success(cmd, **kwargs):
            Path(cmd[-1]).write_bytes(b"%PDF-1.6\nfresh")
            return subprocess.CompletedProcess(cmd, 3, b"", b"recovered warning")
        with patch.object(variants, "run", side_effect=success), patch.object(variants, "summarize", return_value={"header_version": "1.6"}):
            code, summary = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(summary["failed"], 0)
        row = self.rows()[0]
        self.assertEqual(Path(row["file"]).read_bytes(), b"%PDF-1.6\nfresh")
        self.assertTrue(row["warnings"])

    def test_missing_requested_stage_fails_instead_of_degrading(self):
        with patch.object(variants.shutil, "which", return_value=None), patch.object(variants, "qpdf_pass", return_value=None) as converter:
            code, summary = self.invoke("screen-1.4")
        self.assertEqual(code, 1)
        self.assertEqual(summary["failed"], 1)
        converter.assert_not_called()

    def test_converter_claiming_success_without_output_fails(self):
        with patch.object(variants, "qpdf_pass", return_value=None):
            code, summary = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(summary["failed"], 1)

    def test_timeout_is_a_failed_row_and_other_variants_continue(self):
        with patch.object(variants, "qpdf_pass", side_effect=subprocess.TimeoutExpired("qpdf", 600)):
            code, summary = self.invoke("web-1.6-linearized,pdf-2.0")
        self.assertEqual(code, 1)
        self.assertEqual(summary["failed"], 2)
        self.assertTrue(all(row["file"] is None and row["error"] for row in self.rows()))
        self.assertFalse(list(self.out.glob(".variant-*")))

    def test_failed_profile_does_not_publish(self):
        def fresh(source, destination, params):
            destination.write_bytes(b"%PDF-1.6\nfresh")
        with patch.object(variants, "qpdf_pass", side_effect=fresh), patch.object(variants, "summarize", return_value={"error": "profile failed"}):
            code, summary = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(summary["failed"], 1)
        self.assertFalse(list(self.out.glob("*.pdf")))

    def test_requested_metadata_failure_blocks_publication(self):
        meta = self.root / "meta.json"
        meta.write_text('{"Title": "Example"}')
        with patch.object(variants, "stamp", return_value="pikepdf missing"), patch.object(variants, "qpdf_pass") as converter:
            code, summary = self.invoke(extra=("--meta", str(meta)))
        self.assertEqual(code, 1)
        self.assertEqual(summary["failed"], 1)
        converter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
