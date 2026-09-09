import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_helpers import module, installer

hooks = module('harness_hooks', 'template/.codex/hooks/dry_harness.py')


class HookTests(unittest.TestCase):
    def test_dangerous_commands_denied_without_executing_them(self):
        for command in ('git reset --hard', 'git push origin main --force', 'git push -f',
                        'DROP TABLE records', 'supabase db reset', 'rm -rf /', 'rm -fr ~', 'cat .env.local'):
            with self.subTest(command=command):
                result = hooks.handle('PreToolUse', {'tool_name': 'exec_command', 'tool_input': {'cmd': command}})
                self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_ordinary_work_is_not_denied(self):
        for command in ('python3 -m unittest', 'git status', 'rm -rf build', 'cat .env.example'):
            result = hooks.handle('PreToolUse', {'tool_name': 'exec_command', 'tool_input': {'cmd': command}})
            self.assertEqual(result, {})

    def test_tdd_is_relevant_advice_not_file_naming_gate(self):
        result = hooks.handle('PreToolUse', {'tool_name': 'apply_patch', 'tool_input':
                              '*** Add File: migrations/001.sql\n+CREATE TABLE things(id int);'})
        self.assertIn('additionalContext', result['hookSpecificOutput'])
        self.assertNotIn('permissionDecision', result['hookSpecificOutput'])
        self.assertEqual(hooks.handle('PreToolUse', {'tool_name': 'Edit', 'tool_input': {'file_path': 'src/button.tsx'}}), {})

    def test_session_modes_are_isolated_and_no_global_config(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(hooks, 'runtime', return_value=Path(directory)):
            payload = {'cwd': directory, 'session_id': 'first', 'prompt': '$dry-harness mode off'}
            hooks.handle('UserPromptSubmit', payload)
            first = hooks.handle('SubagentStart', payload)
            second = hooks.handle('SubagentStart', dict(payload, session_id='second'))
            self.assertEqual(first, {})
            self.assertIn('simplest', second['hookSpecificOutput']['additionalContext'])
            self.assertEqual(hooks.handle('UserPromptSubmit', dict(payload, prompt='ordinary task')), {})

    def test_weekly_notice_is_throttled_and_first_start_is_quiet(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(hooks, 'runtime', return_value=Path(directory)), patch.dict(os.environ, {'DRY_HARNESS_WEEKLY_DAYS': '7'}):
            payload = {'cwd': directory, 'session_id': 's'}
            first = hooks.handle('SessionStart', payload, now=100)
            due = hooks.handle('SessionStart', payload, now=100 + 8 * 86400)
            again = hooks.handle('SessionStart', payload, now=100 + 8 * 86400)
            self.assertNotIn('Periodic maintenance', str(first))
            self.assertIn('Periodic maintenance', str(due))
            self.assertNotIn('Periodic maintenance', str(again))

    def test_malformed_input_is_nonblocking(self):
        script = installer.PACKAGE / 'template/.codex/hooks/dry_harness.py'
        result = subprocess.run([sys.executable, str(script), 'PreToolUse'], input='bad json', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')


class FullInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_full_install_includes_six_docs_runner_hooks_and_preserves_config(self):
        (self.root / '.codex').mkdir()
        config = self.root / '.codex/config.toml'
        config.write_text('model = "chosen-model"\n')
        installer.install(self.root, docs=['DB', 'API'])
        self.assertEqual(config.read_text(), 'model = "chosen-model"\n')
        self.assertEqual(len(list((self.root / 'docs').glob('*.md'))), 8)
        self.assertTrue((self.root / 'scripts/execute.py').exists())
        self.assertEqual(set(json.loads((self.root / '.codex/hooks.json').read_text())['hooks']),
                         {'SessionStart', 'SubagentStart', 'UserPromptSubmit', 'PreToolUse'})

    def test_existing_hooks_merge_idempotently(self):
        (self.root / '.codex').mkdir()
        path = self.root / '.codex/hooks.json'
        original = {'matcher': 'exec_command', 'hooks': [{'type': 'command', 'command': 'existing-guard'}]}
        path.write_text(json.dumps({'custom': 'preserve', 'hooks': {'PreToolUse': [original]}}))
        installer.install(self.root)
        once = path.read_text()
        installer.install(self.root, update=True)
        self.assertEqual(path.read_text(), once)
        value = json.loads(once)
        self.assertEqual(value['custom'], 'preserve')
        self.assertIn(original, value['hooks']['PreToolUse'])

    def test_existing_docs_and_executor_are_preserved(self):
        (self.root / 'docs').mkdir()
        (self.root / 'scripts').mkdir()
        (self.root / 'docs/PRD.md').write_text('confirmed policy')
        (self.root / 'scripts/execute.py').write_text('existing project runner')
        installer.install(self.root)
        installer.install(self.root, update=True)
        self.assertEqual((self.root / 'docs/PRD.md').read_text(), 'confirmed policy')
        self.assertEqual((self.root / 'scripts/execute.py').read_text(), 'existing project runner')

    def test_modified_managed_hook_is_not_silently_overwritten(self):
        installer.install(self.root)
        hook = self.root / '.codex/hooks/dry_harness.py'
        hook.write_text('project customization')
        with self.assertRaises(FileExistsError):
            installer.install(self.root, update=True)
        self.assertEqual(hook.read_text(), 'project customization')

    def test_invalid_hooks_fail_before_any_writes(self):
        (self.root / '.codex').mkdir()
        (self.root / '.codex/hooks.json').write_text('{malformed')
        with self.assertRaises(ValueError):
            installer.install(self.root)
        self.assertFalse((self.root / '.agents').exists())

    def test_skills_only_has_no_project_config_side_effects(self):
        installer.install(self.root, skills_only=True)
        self.assertFalse((self.root / '.codex').exists())
        self.assertFalse((self.root / 'docs').exists())

    def test_installed_hook_command_accepts_actual_payload(self):
        installer.install(self.root)
        result = subprocess.run([sys.executable, '.codex/hooks/dry_harness.py', 'PreToolUse'], cwd=self.root,
                                input=json.dumps({'tool_name': 'exec_command', 'tool_input': {'cmd': 'git reset --hard'}}),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')


if __name__ == '__main__':
    unittest.main()
