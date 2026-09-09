# Project constraints

Status: project-specific constraints still need to be recorded.

Keep only constraints whose violation has a concrete consequence. For each, record its scope, reason/source and verification. Honor explicit user decisions and existing authorization.

The framework requires honest completion evidence: do not mark a failed check as passed, invent real-world observations, or change acceptance criteria to hide a failure. Keep secrets out of public code and validation reports.

Test strategy depends on the change; file naming alone does not prove coverage. Repeated failures in [ISSUES.md](ISSUES.md) are a reason to investigate the cause, not automatically add more global instructions.
