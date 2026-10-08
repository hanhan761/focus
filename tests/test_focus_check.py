import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/focus/scripts/focus_check.py"
spec = importlib.util.spec_from_file_location("focus_check", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
TEMPLATE = json.loads((ROOT / "skills/focus/assets/focus.template.json").read_text(encoding="utf-8"))
RECEIPT = {"source": "results/check.txt", "revision": "input-v1@artifact-sha256",
           "observation": "Required check passed with exit code 0"}


class FocusChecks(unittest.TestCase):
    def setUp(self):
        self.state = copy.deepcopy(TEMPLATE)

    def cycle(self, new_evidence=False, observation="No distinguishing result"):
        return {"step_id": "S1", "action": "Check one hypothesis", "result": observation,
                "new_evidence": new_evidence,
                "evidence": [copy.deepcopy(RECEIPT)] if new_evidence else []}

    def make_complete(self):
        self.state["metrics"][0].update(status="pass", current="target reached",
                                        evidence=[copy.deepcopy(RECEIPT)])
        self.state["workflow"][0]["status"] = "done"

    def test_initial_state_is_healthy_but_not_complete(self):
        code, report = checker.evaluate(self.state)
        self.assertEqual(code, 0)
        self.assertEqual(report["verification"]["recorded"], 0)
        self.assertFalse(report["recorded_completion_eligible"])
        self.assertEqual(checker.evaluate(self.state, complete=True)[0], 3)

    def test_recorded_evidence_and_finished_actions_allow_acceptance(self):
        self.make_complete()
        self.assertEqual(checker.evaluate(self.state, complete=True)[0], 0)

    def test_pass_without_evidence_does_not_count_as_verified(self):
        self.state["metrics"][0].update(status="pass", current="target reached")
        code, report = checker.evaluate(self.state)
        self.assertEqual(code, 1)
        self.assertEqual(report["verification"]["recorded"], 0)
        self.assertEqual(report["unverified_pass_claims"], ["M1"])

    def test_unknown_current_cannot_support_pass(self):
        self.state["metrics"][0].update(status="pass", evidence=[RECEIPT])
        self.assertEqual(checker.evaluate(self.state)[1]["unverified_pass_claims"], ["M1"])

    def test_unfinished_required_metric_blocks_acceptance(self):
        self.make_complete()
        self.state["metrics"].append(dict(self.state["metrics"][0], id="M2", status="pending"))
        self.assertEqual(checker.evaluate(self.state, complete=True)[0], 3)

    def test_multiple_current_steps_trigger_refocus(self):
        self.state["workflow"].append(dict(self.state["workflow"][0], id="S2"))
        self.assertEqual(checker.evaluate(self.state)[0], 1)

    def test_action_without_metric_triggers_refocus(self):
        self.state["workflow"][0]["metric_ids"] = []
        self.assertEqual(checker.evaluate(self.state)[0], 1)

    def test_unknown_metric_reference_is_invalid(self):
        self.state["workflow"][0]["metric_ids"] = ["M99"]
        with self.assertRaises(checker.FocusError):
            checker.evaluate(self.state)

    def test_conflict_resolution_changes_record_health(self):
        self.state["conflicts"] = [{"sources": ["user", "old plan"], "resolution": ""}]
        self.assertEqual(checker.evaluate(self.state)[0], 1)
        self.state["conflicts"][0]["resolution"] = "Current user correction supersedes old method"
        self.assertEqual(checker.evaluate(self.state)[0], 0)

    def test_two_stalled_cycles_trigger_refocus(self):
        self.state["cycles"] = [self.cycle(), self.cycle()]
        code, report = checker.evaluate(self.state)
        self.assertEqual(code, 1)
        self.assertEqual(report["stall_streak"], 2)
        self.assertEqual(checker.evaluate(self.state, stall_limit=3)[0], 0)

    def test_failed_experiment_can_reset_stall_when_it_has_new_evidence(self):
        self.state["cycles"] = [self.cycle(), self.cycle(),
                                self.cycle(True, "Hypothesis ruled out by a controlled test")]
        self.assertEqual(checker.evaluate(self.state)[0], 0)
        self.assertEqual(checker.evaluate(self.state)[1]["stall_streak"], 0)

    def test_completed_outcomes_are_not_blocked_by_irrelevant_stall_history(self):
        self.make_complete()
        self.state["cycles"] = [self.cycle(), self.cycle()]
        self.assertEqual(checker.evaluate(self.state, complete=True)[0], 0)

    def test_new_evidence_without_receipt_is_invalid(self):
        self.state["cycles"] = [self.cycle()]
        self.state["cycles"][0]["new_evidence"] = True
        with self.assertRaises(checker.FocusError):
            checker.evaluate(self.state)

    def test_evidence_needs_input_or_artifact_version(self):
        self.make_complete()
        self.state["metrics"][0]["evidence"][0]["revision"] = ""
        with self.assertRaises(checker.FocusError):
            checker.evaluate(self.state)

    def test_claiming_complete_cannot_bypass_required_work(self):
        self.state["status"] = "complete"
        self.assertEqual(checker.evaluate(self.state)[0], 1)

    def test_blocked_state_cannot_pass_acceptance(self):
        self.make_complete()
        self.state["status"] = "blocked"
        self.assertEqual(checker.evaluate(self.state, complete=True)[0], 3)

    def test_cli_is_read_only_and_has_distinct_completion_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / "focus.json"
            before = json.dumps(self.state, ensure_ascii=False).encode("utf-8")
            checkpoint.write_bytes(before)
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
            result = subprocess.run([sys.executable, str(SCRIPT), str(checkpoint),
                                     "--json", "--complete"], capture_output=True,
                                    encoding="utf-8", **options)
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertEqual(json.loads(result.stdout)["remaining_metrics"], ["M1"])
            self.assertEqual(checkpoint.read_bytes(), before)
            self.assertEqual(list(Path(tmp).iterdir()), [checkpoint])

    def test_duplicate_json_keys_cannot_silently_change_state(self):
        with self.assertRaises(checker.FocusError):
            json.loads('{"status":"active","status":"complete"}',
                       object_pairs_hook=checker.no_duplicate_keys)

    def test_missing_next_action_is_not_recoverable(self):
        self.state["checkpoint"]["next_action"] = ""
        with self.assertRaises(checker.FocusError):
            checker.evaluate(self.state)


if __name__ == "__main__":
    unittest.main()
