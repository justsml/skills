"""Consequential accounting and scaffolding behavior; entirely offline."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("remote_compute", Path(__file__).with_name("remote_compute.py"))
compute = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compute)


class ComputeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        compute.setup(self.project)
        self.base = self.project / ".remote-compute"
        self.config = json.loads((self.base / "config.json").read_text())
        self.config["providers"] = [{"alias": "gpu"}]
        self.config["budget"].update(hourly_usd=1, run_usd=10, cleanup_reserve_usd=1)
        self.now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
        self.snapshot = {
            "version": 1, "observed_at": "2026-10-07T12:00:00Z", "coverage": "complete",
            "providers": [{"alias": "gpu", "inventory_status": "verified", "billing_status": "unknown"}],
            "resources": [self.resource("live", "run-a", .5, .8), self.resource("old", "run-a", None, None, True)],
            "runs": [{"id": "run-a", "thread_id": "thread-a", "measured_usd": 2,
                      "estimated_usd": 1, "committed_usd": .5, "unknown_cost": False,
                      "eta_hours_low": 1, "eta_hours_high": 5}]
        }

    def resource(self, id, run, low, high, ended=False):
        return {"id": id, "provider": "gpu", "run_id": run, "owned": True,
                "billing_ended": ended, "rate_low_usd": low, "rate_high_usd": high,
                "active_jobs": 0, "pending_jobs": 0}

    def report(self, run=None):
        (self.base / "config.json").write_text(json.dumps(self.config))
        (self.base / "state/snapshot.json").write_text(json.dumps(self.snapshot))
        return compute.status(self.project, run, self.now)

    def test_rerun_preserves_policy_and_snapshot(self):
        self.report()
        before = (self.base / "config.json").read_bytes()
        result = compute.setup(self.project)
        self.assertEqual(result["created"], [])
        self.assertEqual((self.base / "config.json").read_bytes(), before)
        self.assertFalse(self.config["authorization"]["paid_compute"])

    def test_forecast_retains_retired_accrual_excludes_ended_rate(self):
        result = self.report()
        self.assertEqual(result["aggregate_rate_usd_per_hour"], [.5, .8])
        self.assertEqual(result["unchanged_24h_usd"], [12, 19.2])
        self.assertEqual(result["extra_1_to_5h_usd"], [.5, 4])
        self.assertEqual(result["runs"][0]["final_flat_fleet_usd"], [4, 7.5])
        self.assertEqual(result["providers"][0]["balance_usd"], None)

    def test_unknown_rate_never_becomes_zero_forecast(self):
        self.snapshot["resources"][0]["rate_high_usd"] = None
        result = self.report()
        self.assertIsNone(result["aggregate_rate_usd_per_hour"])
        self.assertIsNone(result["unchanged_24h_usd"])
        self.assertIsNone(result["runs"][0]["final_flat_fleet_usd"])

    def test_stale_missing_provider_and_unknown_cost_close_forecast(self):
        original_config = json.dumps(self.config)
        original_snapshot = json.dumps(self.snapshot)
        for mutate in [
            lambda: self.snapshot.update(observed_at="2026-10-07T10:00:00Z"),
            lambda: self.config["providers"].append({"alias": "other"}),
            lambda: self.snapshot["runs"][0].update(unknown_cost=True)
        ]:
            with self.subTest(mutate=mutate):
                self.config = json.loads(original_config)
                self.snapshot = json.loads(original_snapshot)
                mutate()
                self.assertFalse(self.report()["complete_forecast"])

    def test_scoped_run_still_checks_whole_project_ceiling(self):
        second = dict(self.snapshot["runs"][0], id="run-b", thread_id="thread-b")
        self.snapshot["runs"].append(second)
        self.snapshot["resources"].append(self.resource("peer", "run-b", 2, 3))
        borrowed = self.resource("borrowed", "run-a", 99, 99)
        borrowed["owned"] = False
        self.snapshot["resources"].append(borrowed)
        result = self.report("run-a")
        self.assertEqual(result["aggregate_rate_usd_per_hour"], [.5, .8])
        self.assertIn("aggregate project rate exceeds hourly ceiling", result["warnings"])
        self.assertEqual(len(result["runs"]), 1)

    def test_zero_budget_warns_and_invalid_values_fail(self):
        self.config["budget"]["run_usd"] = 0
        self.assertTrue(self.report()["warnings"])
        for value in [-1, float("nan"), True]:
            with self.subTest(value=value):
                self.config["budget"]["hourly_usd"] = value
                with self.assertRaises(ValueError):
                    self.report()

    def test_stopped_resource_still_bills_until_verified_end(self):
        self.snapshot["resources"][0]["state"] = "stopped"
        self.assertEqual(self.report()["aggregate_rate_usd_per_hour"], [.5, .8])

    def test_duplicate_ownership_or_missing_run_is_rejected(self):
        self.snapshot["resources"].append(self.snapshot["resources"][0].copy())
        with self.assertRaises(ValueError):
            self.report()
        self.snapshot["resources"].pop()
        self.snapshot["resources"][0]["run_id"] = "unrecorded"
        with self.assertRaises(ValueError):
            self.report()

    def test_unrounded_forecast_enforces_warning_and_unknown_project_rates_warn(self):
        self.config["budget"].update(cleanup_reserve_usd=0, run_usd=7.5)
        self.snapshot["resources"][0]["rate_high_usd"] = .80000001
        report = self.report()
        self.assertEqual(report["runs"][0]["final_flat_fleet_usd"][1], 7.5)
        self.assertIn("run run-a forecast plus cleanup reserve exceeds run ceiling", report["warnings"])
        self.snapshot["resources"][0]["rate_high_usd"] = None
        self.assertIn("hourly ceiling cannot be assessed: project rates are unknown", self.report()["warnings"])
        del self.config["budget"]["hourly_usd"]
        with self.assertRaises(ValueError): self.report()

    def test_setup_refuses_state_symlink(self):
        (self.base / "state/snapshot.json").unlink()
        (self.base / "state").rmdir()
        (self.base / "state").symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(ValueError):
            compute.setup(self.project)


if __name__ == "__main__":
    unittest.main()
