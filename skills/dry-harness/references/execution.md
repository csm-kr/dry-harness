# Deliver or resume a phase

Read the selected phase, its required contract sections, and relevant code. Preserve its dependencies and acceptance criteria. On resume, inspect the last verified outcome and current changes; do not trust a stale completion label after its code or evidence has changed.

The full installer provides `scripts/execute.py`; its [executor contract](executor.md) defines JSON phases, independent checks, resume/retry and cumulative review. Run it from the project root. If an existing project runner was preserved during installation, use its actual interface or invoke `.agents/skills/dry-harness/scripts/execute.py` explicitly with a compatible phase; do not mistake the two formats for interchangeable ones.

Finish implementation, run checks that demonstrate the changed behavior, inspect the result where necessary, and repair failures within the authorized scope. Choose implementation details and test techniques to fit the task. Broaden verification for integration changes, failures, or unresolved concerns; avoid repeating unrelated suites after unchanged passing evidence.

The bundled runner executes all phase checks on the integrated result before review. It stops with concrete findings when review requires changes. The coordinating agent then repairs the authorized issues and runs `--reverify --review`; a runner exit is not an instruction to abandon an otherwise authorized task.

Treat an agent's completion message as a claim. The coordinator or existing runner must inspect concrete test output and artifacts before recording verified progress. Do not weaken acceptance criteria to make a failed step pass. Missing credentials, devices, observations, or user-only decisions remain explicit blockers for dependent work. Mock results cannot stand in for real API or device evidence.

At the phase boundary, use `dry-review` with a fresh read-only reviewer to compare the cumulative change, user journey, contracts, and evidence. Give the reviewer the actual revision/diff and artifact paths, not only the implementer's summary. A clear review does not replace deterministic checks; passing tests do not replace required observations.

Fix blocking findings within scope and rerun affected checks. Re-review the changed area and its integration effects. Bound repeated failures by the observed cause: stop for an unresolved external dependency or a decision only the user can make, and report the exact condition. Do not stop merely because a first implementation exists.

Report the delivered behavior, checks actually run, independent review result, and remaining limitations. Completion applies only to the inspected revision and evidence. Publication, messages, or paid actions follow the user's existing authorization; local implementation authorization does not imply these actions.
