# Deliver or resume a phase

Read the selected phase, its required contract sections, and relevant code. Preserve its dependencies and acceptance criteria. On resume, inspect the last verified outcome and current changes; do not trust a stale completion label after its code or evidence has changed.

Use the project's runner if one exists. Follow its ownership of state, checks, commits, and review. The runner's actual interface governs; this package does not install a universal step executor. Otherwise the coordinating agent implements the ordered steps and records concise progress in the phase document.

Finish implementation, run checks that demonstrate the changed behavior, inspect the result where necessary, and repair failures within the authorized scope. Choose implementation details and test techniques to fit the task. Broaden verification for integration changes, failures, or unresolved concerns; avoid repeating unrelated suites after unchanged passing evidence.

Treat an agent's completion message as a claim. The coordinator or existing runner must inspect concrete test output and artifacts before recording verified progress. Do not weaken acceptance criteria to make a failed step pass. Missing credentials, devices, observations, or user-only decisions remain explicit blockers for dependent work. Mock results cannot stand in for real API or device evidence.

At the phase boundary, use `dry-review` with a fresh read-only reviewer to compare the cumulative change, user journey, contracts, and evidence. Give the reviewer the actual revision/diff and artifact paths, not only the implementer's summary. A clear review does not replace deterministic checks; passing tests do not replace required observations.

Fix blocking findings within scope and rerun affected checks. Re-review the changed area and its integration effects. Bound repeated failures by the observed cause: stop for an unresolved external dependency or a decision only the user can make, and report the exact condition. Do not stop merely because a first implementation exists.

Report the delivered behavior, checks actually run, independent review result, and remaining limitations. Completion applies only to the inspected revision and evidence. Publication, messages, or paid actions follow the user's existing authorization; local implementation authorization does not imply these actions.
