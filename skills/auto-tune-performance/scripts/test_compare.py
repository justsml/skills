"""Offline decisions over synthetic experiments, not evidence about a real app."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("performance_compare", Path(__file__).with_name("compare.py"))
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def metric(identity="warm.latency", role="primary", threshold=5, ratios=None, direction="lower"):
    ratios = ratios or [.79, .81, .80, .82, .78, .80, .81, .79]
    return {"id": identity, "unit": "ms", "direction": direction, "role": role,
            "threshold_pct": threshold,
            "blocks": [{"id": f"block-{i}", "order": "AB" if i % 2 == 0 else "BA",
                        "baseline": 100 + i, "candidate": (100 + i) * ratio, "valid": True}
                       for i, ratio in enumerate(ratios)]}


def experiment():
    return {"version": 1, "experiment_id": "synthetic-test", "phase": "confirm",
            "baseline": {"revision": "base", "environment_id": "env", "workload_id": "fixtures", "harness_id": "harness"},
            "candidate": {"revision": "candidate", "environment_id": "env", "workload_id": "fixtures", "harness_id": "harness"},
            "design": {"unit": "independent-paired-block", "min_blocks": 8, "confidence": .95,
                       "resamples": 2000, "seed": 42, "profiled": False},
            "hard_checks": [{"id": "output", "baseline": "pass", "candidate": "pass", "evidence": "output.json"}],
            "metrics": [metric()]}


class CompareTests(unittest.TestCase):
    def test_confirmed_effect_accepts_and_reports_correct_units(self):
        report = comparison.compare(experiment())
        self.assertEqual(report["decision"], "accept")
        row = report["metrics"][0]
        self.assertAlmostEqual(row["paired_improvement_pct"], 20, delta=.1)
        self.assertGreater(row["adjusted_interval_pct"][0], 5)
        self.assertEqual(row["independent_blocks"], 8)
        self.assertEqual(row["baseline_median"], 103.5)

    def test_screening_does_not_claim_confirmation(self):
        data = experiment(); data["phase"] = "screen"
        self.assertEqual(comparison.compare(data)["decision"], "needs_confirmation")

    def test_higher_is_better_uses_opposite_direction(self):
        data = experiment(); data["metrics"] = [metric(direction="higher", ratios=[1.25] * 8)]
        result = comparison.compare(data)
        self.assertEqual(result["decision"], "accept")
        self.assertAlmostEqual(result["metrics"][0]["paired_improvement_pct"], 25)

    def test_winning_headline_cannot_cancel_guardrail_regression(self):
        data = experiment()
        data["metrics"].append(metric("reverse-scroll.latency", "guardrail", 2, [1.3] * 8))
        self.assertEqual(comparison.compare(data)["decision"], "reject")

    def test_no_gain_keeps_baseline_and_noisy_gain_is_inconclusive(self):
        data = experiment(); data["metrics"][0] = metric(ratios=[.98] * 8)
        self.assertEqual(comparison.compare(data)["decision"], "keep_baseline")
        data["metrics"][0] = metric(ratios=[.5, 1.5] * 4)
        self.assertEqual(comparison.compare(data)["decision"], "inconclusive")

    def test_insufficient_independent_blocks_does_not_pass(self):
        data = experiment(); data["metrics"][0] = metric(ratios=[.8] * 4)
        report = comparison.compare(data)
        self.assertEqual(report["decision"], "inconclusive")
        self.assertIsNone(report["metrics"][0]["adjusted_interval_pct"])

    def test_invalid_work_drift_tracing_and_order_cannot_win(self):
        def invalid_work(d): d["metrics"][0]["blocks"][0].update(valid=False)
        def drift(d): d["candidate"].update(environment_id="different")
        def tracing(d): d["design"].update(profiled=True)
        def order(d):
            for row in d["metrics"][0]["blocks"]: row["order"] = "AB"
        for mutate in [invalid_work, drift, tracing, order]:
            with self.subTest(mutate=mutate):
                data = experiment(); mutate(data)
                self.assertEqual(comparison.compare(data)["decision"], "invalid")

    def test_correctness_failure_rejects_and_unknown_blocks_acceptance(self):
        for state, decision in [("fail", "reject"), ("unknown", "inconclusive")]:
            data = experiment(); data["hard_checks"][0]["candidate"] = state
            self.assertEqual(comparison.compare(data)["decision"], decision)
        data = experiment(); data["hard_checks"][0]["baseline"] = "fail"
        self.assertEqual(comparison.compare(data)["decision"], "invalid")

    def test_finite_positive_and_unique_observations_are_required(self):
        for value in [0, -1, float("nan"), float("inf"), True]:
            with self.subTest(value=value):
                data = experiment(); data["metrics"][0]["blocks"][0]["candidate"] = value
                with self.assertRaises(ValueError): comparison.compare(data)
        data = experiment(); data["metrics"][0]["blocks"][1]["id"] = "block-0"
        with self.assertRaises(ValueError): comparison.compare(data)

    def test_family_adjustment_widens_intervals_and_is_reproducible(self):
        data = experiment()
        first = comparison.compare(data)
        data["metrics"].append(metric("memory", "guardrail", 2))
        second = comparison.compare(data)
        low_a, high_a = first["metrics"][0]["adjusted_interval_pct"]
        low_b, high_b = second["metrics"][0]["adjusted_interval_pct"]
        self.assertLessEqual(low_b, low_a)
        self.assertGreaterEqual(high_b, high_a)
        self.assertEqual(second, comparison.compare(copy.deepcopy(data)))

    def test_cli_exit_codes_and_invalid_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "experiment.json"
            for state, expected in [("confirm", 0), ("screen", 3)]:
                data = experiment(); data["phase"] = state
                fixture.write_text(json.dumps(data))
                proc = subprocess.run([sys.executable, str(Path(__file__).with_name("compare.py")), str(fixture)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, expected)
                self.assertIn("decision", json.loads(proc.stdout))
            fixture.write_text("broken JSON")
            proc = subprocess.run([sys.executable, str(Path(__file__).with_name("compare.py")), str(fixture)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout)["decision"], "invalid")


if __name__ == "__main__":
    unittest.main()
