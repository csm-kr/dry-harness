# Executor contract

Requires Python 3.10+, Git repository root with an initial commit, authenticated Codex CLI and access to `gpt-6-astra`. The dry run requires only valid phase/context files. A phase is trusted executable input: verification commands run as local subprocesses with the caller's environment, outside Codex's child sandbox. Use project-approved disposable checks, not production operations.

```json
{
  "version": 1,
  "id": "01-core",
  "goal": "Deliver the R1 behavior described in the PRD",
  "context": ["docs/PRD.md", "docs/RULES.md"],
  "steps": [
    {
      "id": "S1",
      "prompt": "Implement R1 and its important failure behavior, with meaningful tests.",
      "depends_on": [],
      "checks": [["python3", "-m", "unittest", "discover", "-s", "tests"]],
      "evidence": []
    }
  ]
}
```

All fields shown are required; additional fields are rejected. Use actual commands for the project's stack. Each `checks` entry is an argv array, not a shell string. Use an explicit shell only when intentionally needed. Exit 0 passes, 2 signals unavailable prerequisites, other nonzero results are failures. Evidence names project-relative files required in addition to checks. Contract/evidence paths must not contain symlinks. Existence/content binding does not prove an observation happened; review must inspect its substance.

Steps are ordered and dependencies must name earlier steps in the same phase. This version runs one selected phase; the coordinator checks cross-phase dependencies. Original Harness `phases/<name>/index.json` is not accepted without conversion: preserve the old runner or create this explicit JSON contract. Do not silently discard old acceptance criteria.

```bash
python3 scripts/execute.py phases/01-core.json --dry-run
python3 scripts/execute.py phases/01-core.json --max-steps 1
python3 scripts/execute.py phases/01-core.json
python3 scripts/execute.py phases/01-core.json --retry
python3 scripts/execute.py phases/01-core.json --review
# After code/evidence fixes made outside the runner:
python3 scripts/execute.py phases/01-core.json --reverify --review
```

Default execution runs remaining steps, checks the integrated phase, then starts an independent read-only review. Implementation uses workspace-write; review uses read-only. Child sessions enable the hooks feature but still require host trust for project hook definitions. Neither bypasses hook trust or silently changes the model. `--model` is an explicit override. `--attempts` defaults to 3 per invocation; `--timeout` defaults to 1800 seconds per model call/check. Blocked results stop retries immediately. `--max-steps` limits implementations and stops before automatic review when the limit is reached.

Status/receipts/logs live in `$(git rev-parse --absolute-git-dir)/dry-harness/<phase-id>/`, outside the working tree. The lock covers one Git worktree. After an interruption, inspect any remaining lock's PID before removing it. `--retry` permits retrying errored/blocked/interrupted steps. It does not retry review findings blindly: repair those in the coordinating session, then reverify/review.

The executor owns state. It rejects child state changes and detects acceptance-contract edits. Contracts include the phase JSON and its listed `context` files. If those need legitimate revision, the coordinator updates them and explicitly uses `--reset`; old runtime logs remain. Source edits are preserved on failure rather than automatically rolled back.

Completion is bound to tracked/untracked nonignored file contents/modes plus every declared evidence file, even if ignored. External/ignored inputs not declared as evidence are outside that binding; list relevant evidence and encode environmental requirements in checks. Submodules/nested repositories are unsupported. `--reverify` reruns completed checks after external changes; failed checks become errored steps. All phase checks must pass on the integrated workspace before final review. The JSON verdict also requires a consistent blocking-finding list.

Exit 0 means this command succeeded; with `--max-steps` or `--dry-run` it does not mean the phase is complete. Exit 1 is failure/findings, 2 is blocked/invalid setup, 130 is interruption. Inspect `state.json` for phase completion. Runtime logs may contain project data; do not publish them. The executor does not commit, push, deploy or start paid infrastructure.
