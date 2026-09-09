import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_helpers import module, installer

execute = module('execute', 'skills/dry-harness/scripts/execute.py')


class ExecuteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / '.gitignore').write_text('__pycache__/\nevidence/\n')
        (self.root / 'SPEC.md').write_text('R1: feature.txt contains good.\n')
        self.phase = {'version': 1, 'id': 'fixture', 'goal': 'Deliver R1', 'context': ['SPEC.md'], 'steps': [
            {'id': 'S1', 'prompt': 'Deliver R1', 'depends_on': [], 'checks': [[sys.executable, '-c',
              "from pathlib import Path; assert Path('feature.txt').read_text() == 'good'"]], 'evidence': []}]}
        self.write_phase()
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True).stdout

    def write_phase(self):
        (self.root / 'phase.json').write_text(json.dumps(self.phase))

    def executor(self):
        return execute.Executor(self.root, 'phase.json', timeout=5)

    def model(self, prompt, label, review=False):
        if review:
            return {'verdict': 'clear', 'summary': 'Checked fixture', 'findings': []}
        (self.root / 'feature.txt').write_text('good')
        return {'status': 'completed', 'summary': 'Implemented R1', 'reason': ''}

    def run_it(self, obj=None, model=None, **kwargs):
        obj = obj or self.executor()
        with patch.object(obj, 'invoke', side_effect=model or self.model), contextlib.redirect_stdout(io.StringIO()):
            code = obj.run(**kwargs)
        return obj, code

    def test_success_verifies_then_reviews_and_resume_is_noop(self):
        obj, code = self.run_it()
        self.assertEqual(code, 0)
        self.assertEqual(obj.state['status'], 'completed')
        with patch.object(execute.Executor, 'invoke', side_effect=AssertionError('Must not call model')):
            self.assertEqual(self.executor().run(), 0)
        self.assertEqual(self.git('rev-list', '--count', 'HEAD').strip(), b'1')

    def test_model_success_is_not_enough_to_complete(self):
        def fake(*args, **kwargs):
            return {'status': 'completed', 'summary': 'Claim', 'reason': ''}
        obj = self.executor()
        with self.assertRaises(execute.Failure):
            self.run_it(obj, fake, attempts=1)
        self.assertEqual(obj.state['steps']['S1']['status'], 'error')

    def test_retry_gets_failure_feedback_and_repairs(self):
        prompts = []
        def fake(prompt, label, review=False):
            if review:
                return self.model(prompt, label, review)
            prompts.append(prompt)
            (self.root / 'feature.txt').write_text('bad' if len(prompts) == 1 else 'good')
            return {'status': 'completed', 'summary': 'Attempt', 'reason': ''}
        obj, code = self.run_it(model=fake, attempts=2)
        self.assertEqual(code, 0)
        self.assertIn('AssertionError', prompts[1])
        self.assertEqual(obj.state['steps']['S1']['attempt'], 2)

    def test_blocked_stops_without_retries(self):
        obj = self.executor()
        with patch.object(obj, 'invoke', return_value={'status': 'blocked', 'summary': 'Need device', 'reason': 'Device absent'}) as model:
            with self.assertRaises(execute.Failure) as ctx:
                obj.run()
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(model.call_count, 1)
        self.assertEqual(obj.state['status'], 'blocked')

    def test_failed_step_needs_explicit_retry(self):
        obj = self.executor()
        with self.assertRaises(execute.Failure):
            self.run_it(obj, lambda *a, **kw: {'status': 'error', 'summary': 'Failed', 'reason': 'Bug'}, attempts=1)
        with self.assertRaisesRegex(execute.Failure, '--retry'):
            self.run_it()
        self.assertEqual(self.run_it(retry=True)[1], 0)

    def test_state_tampering_is_rejected_and_restored(self):
        obj = self.executor()
        def fake(*args, **kwargs):
            obj.state_path.write_text('{}')
            return {'status': 'completed', 'summary': 'Claim', 'reason': ''}
        with self.assertRaises(execute.Failure):
            self.run_it(obj, fake, attempts=1)
        self.assertNotEqual(json.loads(obj.state_path.read_text())['status'], 'completed')

    def test_acceptance_contract_edits_cannot_pass(self):
        def fake(*args, **kwargs):
            (self.root / 'SPEC.md').write_text('weakened')
            return {'status': 'completed', 'summary': 'Claim', 'reason': ''}
        obj = self.executor()
        with self.assertRaisesRegex(execute.Failure, 'Acceptance contract changed'):
            self.run_it(obj, fake)
        self.assertEqual((self.root / 'SPEC.md').read_text(), 'weakened')
        self.assertEqual(obj.state['status'], 'blocked')

    def test_final_integration_detects_later_step_regression(self):
        self.phase['steps'].append({'id': 'S2', 'prompt': 'Another change', 'depends_on': ['S1'],
                                    'checks': [[sys.executable, '-c', 'pass']], 'evidence': []})
        self.write_phase()
        reviews = []
        def fake(prompt, label, review=False):
            if review:
                reviews.append(label)
            result = self.model(prompt, label, review)
            if label == 'S2':
                (self.root / 'feature.txt').write_text('regressed')
            return result
        obj = self.executor()
        with self.assertRaises(execute.Failure):
            self.run_it(obj, fake)
        self.assertEqual(reviews, [])
        self.assertEqual(obj.state['steps']['S1']['status'], 'error')

    def test_ignored_evidence_change_invalidates_completion(self):
        self.phase['steps'][0]['evidence'] = ['evidence/proof.txt']
        self.write_phase()
        proof = self.root / 'evidence/proof.txt'
        proof.parent.mkdir()
        proof.write_text('observed')
        self.run_it()
        for value in ('changed', None):
            if value is None:
                proof.unlink()
            else:
                proof.write_text(value)
            with self.assertRaisesRegex(execute.Failure, 'Workspace changed'):
                self.run_it()

    def test_missing_required_evidence_blocks(self):
        self.phase['steps'][0]['evidence'] = ['proof.txt']
        self.write_phase()
        with self.assertRaisesRegex(execute.Failure, 'Required file missing') as ctx:
            self.run_it()
        self.assertEqual(ctx.exception.code, 2)

    def test_source_edit_requires_reverification(self):
        self.run_it()
        (self.root / 'feature.txt').write_text('bad')
        with self.assertRaisesRegex(execute.Failure, '--reverify'):
            self.run_it()
        with self.assertRaises(execute.Failure):
            self.run_it(reverify=True, review_only=True)

    def test_max_steps_pauses_before_review(self):
        obj, code = self.run_it(max_steps=1)
        self.assertEqual(code, 0)
        self.assertEqual(obj.state['status'], 'review')
        self.assertNotIn('review', obj.state)
        self.assertEqual(self.run_it(review_only=True)[1], 0)

    def test_review_changes_require_fix_then_reverify(self):
        def fake(prompt, label, review=False):
            if review:
                return {'verdict': 'changes_required', 'summary': 'Missing behavior', 'findings': []}
            return self.model(prompt, label, review)
        obj, code = self.run_it(model=fake)
        self.assertEqual(code, 1)
        with self.assertRaisesRegex(execute.Failure, 'Resolve review findings'):
            self.run_it()
        self.assertEqual(self.run_it(reverify=True, review_only=True)[1], 0)

    def test_review_cannot_mutate_source_and_mark_complete(self):
        def fake(prompt, label, review=False):
            result = self.model(prompt, label, review)
            if review:
                (self.root / 'feature.txt').write_text('bad')
            return result
        with self.assertRaisesRegex(execute.Failure, 'Workspace changed during'):
            self.run_it(model=fake)

    def test_dry_run_no_git_no_model_and_installed_entrypoint(self):
        installer.install(self.root)
        result = subprocess.run([sys.executable, str(self.root / 'scripts/execute.py'), 'phase.json', '--dry-run'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['model'], 'gpt-6-astra')
        self.assertFalse((self.root / '.git/dry-harness').exists())

    def test_invalid_dependency_and_empty_checks_rejected(self):
        for field, value in [('depends_on', ['S1']), ('checks', [])]:
            original = self.phase['steps'][0][field]
            self.phase['steps'][0][field] = value
            self.write_phase()
            with self.assertRaises(execute.Failure):
                self.executor()
            self.phase['steps'][0][field] = original

    def test_lock_prevents_concurrent_execution(self):
        obj = self.executor()
        with obj.locked():
            with self.assertRaisesRegex(execute.Failure, 'Executor lock exists'):
                with self.executor().locked():
                    self.fail('Second executor acquired lock')

    def test_timeout_kills_check_and_does_not_complete(self):
        self.phase['steps'][0]['checks'] = [[sys.executable, '-c', 'import time; time.sleep(10)']]
        self.write_phase()
        obj = execute.Executor(self.root, 'phase.json', timeout=0.1)
        with self.assertRaises(execute.Failure):
            self.run_it(obj, attempts=1)
        self.assertEqual(obj.state['status'], 'error')

    def test_invoke_uses_astra_hooks_and_correct_sandbox(self):
        obj = self.executor()
        calls = []
        def fake(command, **kwargs):
            calls.append(command)
            self.assertEqual(command[command.index('--model') + 1], 'gpt-6-astra')
            self.assertEqual(command[command.index('--enable') + 1], 'hooks')
            self.assertNotIn('--dangerously-bypass-hook-trust', command)
            readonly = command[command.index('--sandbox') + 1] == 'read-only'
            result = {'verdict': 'clear', 'summary': 'Checked', 'findings': []} if readonly else {
                'status': 'completed', 'summary': 'Done', 'reason': ''}
            Path(command[command.index('--output-last-message') + 1]).write_text(json.dumps(result))
            return 0, '', ''
        with obj.locked():
            obj.state = {'status': 'pending'}
            obj.save()
            with patch.object(execute, 'process', side_effect=fake):
                self.assertEqual(obj.invoke('Task', 'S1')['status'], 'completed')
                self.assertEqual(obj.invoke('Review', 'review', review=True)['verdict'], 'clear')
        self.assertEqual(calls[0][calls[0].index('--sandbox') + 1], 'workspace-write')
        self.assertEqual(len(calls), 2)

    def test_invoke_rejects_cli_failure_and_inconsistent_review(self):
        obj = self.executor()
        with obj.locked():
            obj.state = {'status': 'pending'}
            obj.save()
            with patch.object(execute, 'process', return_value=(1, '', 'failure')) as run:
                with self.assertRaises(execute.Failure):
                    obj.invoke('Task', 'S1')
                self.assertEqual(run.call_count, 1)
            def fake(command, **kwargs):
                Path(command[command.index('--output-last-message') + 1]).write_text(json.dumps({
                    'verdict': 'changes_required', 'summary': 'Defect', 'findings': []}))
                return 0, '', ''
            with patch.object(execute, 'process', side_effect=fake), self.assertRaises(ValueError):
                obj.invoke('Review', 'review', review=True)

    def test_contract_symlinks_are_rejected_before_execution(self):
        (self.root / 'actual.md').write_text('R1')
        (self.root / 'SPEC.md').unlink()
        (self.root / 'SPEC.md').symlink_to('actual.md')
        with self.assertRaisesRegex(execute.Failure, 'Symlink paths'):
            self.executor()

    def test_contract_replaced_with_symlink_cannot_complete(self):
        def fake(*args, **kwargs):
            (self.root / 'actual.md').write_text((self.root / 'SPEC.md').read_text())
            (self.root / 'SPEC.md').unlink()
            (self.root / 'SPEC.md').symlink_to('actual.md')
            return {'status': 'completed', 'summary': 'Claim', 'reason': ''}
        obj = self.executor()
        with self.assertRaisesRegex(execute.Failure, 'Symlink paths'):
            self.run_it(obj, model=fake)
        self.assertNotEqual(obj.state['status'], 'completed')


if __name__ == '__main__':
    unittest.main()
