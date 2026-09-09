# Validation · 0.2.0

Validated on 2026-09-09. These checks establish the scope below, not a model-quality or performance benchmark.

## Offline suite

`python3 -m unittest discover -s tests -q`: **53 tests passed**.

The suite uses temporary Git repositories and simulated model responses. It checks:

- Step implementation claims versus real verification commands; retry feedback; blocked results; explicit resume; max-step pause; locks and timeouts.
- Integrated acceptance verification after all steps, including a later step regressing an earlier one.
- Source changes and missing/modified gitignored evidence invalidating completion.
- Executor-owned status, frozen contracts, rejected contract symlinks and runtime symlink replacement.
- Astra model, hooks feature and sandbox flags; no silent fallback/trust bypass; malformed/inconsistent review rejection.
- Full installation, existing docs/config/runner preservation, hook merging without duplication, modified-hook conflicts and skills-only installation.
- Hook JSON for destructive-command/secret-output denial, nonblocking targeted test advice, per-session modes, weekly throttling and malformed-input handling.

These tests do not invoke live models or operate production systems. Verification subprocesses are real local fixture commands. Hook tests inspect outputs; they do not execute the dangerous command strings under test.

## Independent Astra review

A separate `gpt-6-astra` reviewer inspected the executor, installer and hook integration read-only. It found three concrete problems during development: missing integrated revalidation, ignored evidence not binding completion, and a symlink allowing a contract to change after resolution. All three were fixed and given regression tests.

The final focused review returned `clear`. It reran five targeted tests for symlink protection, model/hooks/sandbox flags, integrated regression detection and ignored-evidence invalidation. It did not repeat the full suite or perform live model calls.

## Live end-to-end executor check

The complete current installer was run in a disposable Git project. The bundled `examples/hello.json` and `hello-spec.md` were supplied as the actual contract. The executor used its default `gpt-6-astra` model and started an implementation session followed by a fresh read-only review session.

Observed result: **exit 0, phase `completed`, review `clear`**. The generated `hello.py` implements whitespace-normalized greetings and rejects empty names; `test_hello.py` verifies both behaviors. The executor ran declared checks and the integrated verification; the independent reviewer inspected actual untracked code/test files and reran the two tests successfully.

The [sanitized actual receipt](validation/execute-smoke.json) preserves the step check output, final review and artifact hashes. Temporary project paths, raw model logs and host configuration are not published. No fallback model was used.

This is one small end-to-end fixture, not proof of production readiness or general task completion quality.

## Package and hook validation

The Codex skill creator's `quick_validate.py` passed for both skills, and the plugin creator's `validate_plugin.py` passed for the package. The repository wrapper's example dry run succeeded without model calls or state writes.

The hook event/output shapes were checked against the [official Codex hooks guide](https://learn.chatgpt.com/docs/hooks), and installed handlers were exercised with synthetic event payloads. The installation test verifies all four configured events and preservation of existing hook groups.

**Host hook trust was not changed or automatically approved.** This record does not claim that every hook was enabled in the user's app. Users must inspect new/changed definitions in `/hooks`; project trust and the hooks feature also apply. The hook patterns are supplementary guards, not an OS security boundary.
