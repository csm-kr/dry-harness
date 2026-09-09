import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


review = module("review", "skills/dry-review/scripts/review.py")
installer = module("installer", "scripts/install.py")


def clear():
    return {"verdict": "clear", "summary": "No blocking finding in inspected scope", "findings": []}


def finding(severity="blocking"):
    return dict(severity=severity, location="spec.md:3", evidence="Missing cancellation case",
                impact="Output survives cancellation", recommendation="Implement and test cancellation")


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_install_preserves_project_and_contains_runnable_helper(self):
        doc = self.root / "AGENTS.md"
        doc.write_text("existing policy")
        installer.install(self.root)
        script = self.root / ".agents/skills/dry-review/scripts/review.py"
        result = subprocess.run(["python3", str(script), "plan", "--root", str(self.root),
                                 "--input", "AGENTS.md", "--dry-run"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["model"], "gpt-6-astra")
        self.assertEqual(doc.read_text(), "existing policy")
        self.assertFalse((self.root / ".codex").exists())

    def test_collision_is_preflighted_before_any_copy(self):
        blocked = self.root / ".agents/skills/dry-review"
        blocked.mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            installer.install(self.root)
        self.assertFalse((blocked.parent / "dry-harness").exists())

    def test_update_replaces_package_file_but_keeps_custom_file(self):
        installer.install(self.root)
        skill = self.root / ".agents/skills/dry-harness"
        (skill / "SKILL.md").write_text("old")
        (skill / "custom.md").write_text("keep")
        installer.install(self.root, update=True)
        self.assertEqual((skill / "SKILL.md").read_bytes(), (installer.SOURCE / "dry-harness/SKILL.md").read_bytes())
        self.assertEqual((skill / "custom.md").read_text(), "keep")

    def test_rejects_external_skills_symlink(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root / ".agents").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(self.root)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_rejects_nested_update_symlink(self):
        installer.install(self.root)
        target = self.root / ".agents/skills/dry-review/scripts/review.py"
        outside = self.root / "keep.py"
        outside.write_text("keep")
        target.unlink()
        target.symlink_to(outside)
        with self.assertRaises(ValueError):
            installer.install(self.root, update=True)
        self.assertEqual(outside.read_text(), "keep")

    def test_file_parent_conflict_does_not_partially_install(self):
        target = self.root / ".agents/skills/dry-review"
        target.mkdir(parents=True)
        (target / "scripts").write_text("not a directory")
        with self.assertRaises(ValueError):
            installer.install(self.root, update=True)
        self.assertFalse((target.parent / "dry-harness").exists())


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.input = self.root / "spec.md"
        self.input.write_text("Cancellation must leave no output.")

    def test_clear_and_advisory_are_valid(self):
        self.assertEqual(review.validate_result(clear()), clear())
        result = clear()
        result["findings"] = [finding("advisory")]
        self.assertEqual(review.validate_result(result), result)

    def test_rejects_contradictory_clear(self):
        result = clear()
        result["findings"] = [finding()]
        with self.assertRaises(ValueError):
            review.validate_result(result)

    def test_changes_and_blocked_require_concrete_blocker(self):
        for verdict in ("changes_required", "blocked"):
            with self.subTest(verdict=verdict):
                result = dict(clear(), verdict=verdict)
                with self.assertRaises(ValueError):
                    review.validate_result(result)
                result["findings"] = [finding()]
                self.assertEqual(review.validate_result(result), result)

    def test_malformed_or_empty_result_is_rejected(self):
        for value in ([], {}, dict(clear(), summary=""), dict(clear(), findings={}),
                      dict(clear(), extra=True), dict(clear(), findings=[{"severity": "blocking"}])):
            with self.subTest(value=value), self.assertRaises(ValueError):
                review.validate_result(value)

    def test_rejects_external_missing_and_absolute_paths(self):
        for value in ("../escape.md", "missing.md", str(self.input)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                review.scoped_file(self.root, value)

    def test_rejects_symlink_outside_root(self):
        with tempfile.TemporaryDirectory() as outside:
            source = Path(outside) / "private.md"
            source.write_text("private")
            (self.root / "link.md").symlink_to(source)
            with self.assertRaises(ValueError):
                review.scoped_file(self.root, "link.md")

    def test_cli_passes_model_readonly_and_raw_input_without_fallback(self):
        calls = []

        def fake(command, **kwargs):
            calls.append(command)
            self.assertEqual(command[command.index("--model") + 1], "gpt-6-astra")
            self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
            self.assertIn("--ephemeral", command)
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
            self.assertIn(self.input.read_text(), kwargs["input"])
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text(json.dumps(clear()))
            return subprocess.CompletedProcess(command, 0)

        before = set(self.root.rglob("*"))
        self.assertEqual(review.run_review(self.root, "plan", [self.input], runner=fake), clear())
        self.assertEqual(len(calls), 1)
        self.assertEqual(before, set(self.root.rglob("*")))

    def test_explicit_model_override_is_forwarded(self):
        def fake(command, **kwargs):
            self.assertEqual(command[command.index("--model") + 1], "explicit-model")
            Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(clear()))
            return subprocess.CompletedProcess(command, 0)
        review.run_review(self.root, "plan", [self.input], model="explicit-model", runner=fake)

    def test_nonzero_cli_exit_does_not_accept_written_clear_result(self):
        def fake(command, **kwargs):
            Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(clear()))
            return subprocess.CompletedProcess(command, 1)
        with self.assertRaises(RuntimeError):
            review.run_review(self.root, "plan", [self.input], runner=fake)

    def test_missing_and_invalid_cli_output_fail_closed(self):
        for content in (None, "not json", json.dumps(dict(clear(), findings=[finding()]))):
            def fake(command, **kwargs):
                if content is not None:
                    Path(command[command.index("--output-last-message") + 1]).write_text(content)
                return subprocess.CompletedProcess(command, 0)
            with self.subTest(content=content), self.assertRaises(ValueError):
                review.run_review(self.root, "plan", [self.input], runner=fake)

    def test_dry_run_never_calls_model_or_writes(self):
        before = list(self.root.rglob("*"))
        with patch.object(review, "run_review") as mock, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(review.main(["plan", "--root", str(self.root), "--input", "spec.md", "--dry-run"]), 0)
            mock.assert_not_called()
        self.assertEqual(before, list(self.root.rglob("*")))

    def test_exit_codes_and_timeouts(self):
        args = ["plan", "--root", str(self.root), "--input", "spec.md"]
        for verdict, code in (("clear", 0), ("changes_required", 1), ("blocked", 2)):
            with patch.object(review, "run_review", return_value=dict(clear(), verdict=verdict)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(review.main(args), code)
        with patch.object(review, "run_review", side_effect=subprocess.TimeoutExpired("codex", 1)), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(review.main(args), 2)


if __name__ == "__main__":
    unittest.main()
