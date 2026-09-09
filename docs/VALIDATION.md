# Validation · 0.1.0

Validated on 2026-09-09. These checks establish the scope below, not model quality or performance benchmarks.

## Offline helper suite

`python3 -m unittest discover -s tests -v`: **18 tests passed**.

The suite covers installing into an isolated project; preserving existing configuration; preflighting collisions and invalid paths; explicit updates; symlink escapes; using the installed review helper; validating review verdicts; model/sandbox argument forwarding; CLI failure and malformed output; exit codes; and a dry run with no model call or writes.

Codex calls in this suite are simulated. The tests exercise orchestration behavior, not model reasoning. Temporary fixtures have no production access.

## Package checks

The Codex skill creator's `quick_validate.py` passed for both shipped skills. The plugin creator's `validate_plugin.py` passed for `.codex-plugin/plugin.json` and its package. These external development tools are not runtime dependencies.

## Independent Astra review

A fresh `gpt-6-astra` reviewer inspected the actual skills, references, installer, review helper, README, manifest and model configuration without editing them. It returned `clear` with no blocking findings. It also checked the review helper flags against the locally installed `codex exec --help`. That review did not itself exercise a live CLI model call or the subsequently completed offline tests.

## Live CLI forward check

The shipped review helper was run with its default `gpt-6-astra` model in a temporary, disposable project. Input requirements specified CSV export and cancellation that stops an active export without leaving a partial file. The example plan implemented and tested only successful export.

```bash
python3 /path/to/dry-harness/skills/dry-review/scripts/review.py plan \
  --root /path/to/disposable-fixture \
  --input SPEC.md --input phase.md --timeout 180
```

Observed result: **exit 1, `changes_required`**, with a blocking finding identifying the omitted cancellation implementation and verification. The finding called for testing interruption after writing begins and checking that no partial output remains. No fallback model was used.

This verifies a real independent Astra invocation and detection of one deliberately missing requirement. It does not establish general review recall, end-to-end application delivery, or an advantage over other frameworks/models. Codex authentication and Astra access remain environment prerequisites.
