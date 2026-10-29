"""Tests review arithmetic and binding, not model linguistic judgment."""
import copy
import unittest
from humanness import DIMENSIONS, digest, evaluate


def receipt():
    text = "Which orders are awaiting dispatch?"
    context = "Short logistics query, UK English."
    return {"version": 1, "text": text, "context": context, "review": {
        "text_sha256": digest(text), "context_sha256": digest(context),
        "reviewer": "independent-test-fixture", "rubric_version": "humanness-v1",
        "calibration": "passed", "fidelity": "pass", "dimensions": {
            name: {"score": 4, "reason": "Plausible for context", "spans": []}
            for name in DIMENSIONS}}}


class HumannessTests(unittest.TestCase):
    def test_clean_writing_needs_no_typos_or_slang(self):
        self.assertEqual(evaluate(receipt())["verdict"], "pass")

    def test_one_weak_dimension_cannot_be_averaged_away(self):
        for dimension in DIMENSIONS:
            data = receipt()
            data["review"]["dimensions"][dimension] = {
                "score": 2, "reason": "Synthetic mismatch control",
                "spans": [{"start": 0, "end": 5, "quote": "Which"}]}
            self.assertEqual(evaluate(data)["verdict"], "fail")

    def test_missing_calibration_fidelity_or_judgment_cannot_pass(self):
        for key, value in (("calibration", "pending"), ("calibration", "failed"), ("fidelity", "unassessed")):
            data = receipt()
            data["review"][key] = value
            self.assertEqual(evaluate(data)["verdict"], "unassessed")
        data = receipt()
        data["review"]["dimensions"]["regional_fit"]["score"] = None
        self.assertEqual(evaluate(data)["verdict"], "unassessed")

    def test_factual_failure_blocks_natural_style(self):
        data = receipt()
        data["review"]["fidelity"] = "fail"
        self.assertEqual(evaluate(data)["verdict"], "fail")

    def test_stale_text_and_context_rejected(self):
        for field in ("text", "context"):
            data = receipt()
            data[field] += " changed"
            with self.assertRaises(ValueError):
                evaluate(data)

    def test_invalid_scores_and_ungrounded_evidence_rejected(self):
        for score in (True, -1, 5, 3.5, "4"):
            data = receipt()
            data["review"]["dimensions"]["register"]["score"] = score
            with self.assertRaises(ValueError):
                evaluate(data)
        base = receipt()
        base["review"]["dimensions"]["register"]["score"] = 2
        for spans in ([], [{"start": 0, "end": 5, "quote": "wrong"}], [{"start": -1, "end": 5, "quote": "Which"}]):
            data = copy.deepcopy(base)
            data["review"]["dimensions"]["register"]["spans"] = spans
            with self.assertRaises(ValueError):
                evaluate(data)

    def test_incomplete_and_malformed_reviews_rejected(self):
        for data in ([], None, {"version": True}):
            with self.assertRaises(ValueError):
                evaluate(data)
        data = receipt()
        del data["review"]["dimensions"]["restraint"]
        with self.assertRaises(ValueError):
            evaluate(data)


if __name__ == "__main__":
    unittest.main()
