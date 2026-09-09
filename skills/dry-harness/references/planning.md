# Prepare a phase

Start with the user's outcome, current decisions, and the relevant existing documents. A source plan is useful input; distinguish confirmed decisions, proposals, and unresolved questions. Preserve explicit decisions. Surface a material conflict rather than silently inventing product policy. Record independent work that can proceed while a decision is pending.

For a new project, use `docs/SPEC.md` for behavior and `phases/<name>.md` for the plan. Reuse an existing repository's equivalents instead. Add architecture, user-flow, or decision documents only when the task needs them; avoid empty document scaffolds.

Make each requirement observable: trigger, expected outcome, important failure behavior, and required evidence. For stateful or external actions, address the relevant ownership, lifecycle, retry, and cancellation behavior. Scope this work to the requested feature, not every hypothetical future feature.

For a substantial new plan or material policy change, use two fresh, read-only reviewers via `dry-review`:

1. **Intent:** give the reviewer the relevant raw user statements and decision record alongside the proposed requirements. Check unsupported assumptions and missing product decisions. Do not replace raw statements with an author-approved summary or expose unrelated conversation.
2. **Plan:** after writing the contract and phase, give a different reviewer the finished artifacts and access to relevant code, without the planning conversation or desired verdict. Check whether an implementer could deliver the right outcome from those artifacts alone.

These independent checks are part of this workflow; delegate them when tools support fresh agents. Use Astra for new reviewers unless the user selects another model. If independent execution is unavailable, label the review unperformed; a second self-review is not independent. Continue preparation that does not depend on it.

Resolve findings at their source. Recheck the affected area when a fix changes the contract; do not repeat clean reviews without cause. A reviewer suggestion is evidence to assess, not an authority to invent user intent or expand scope.

The phase should name its goal, requirement IDs, dependencies, deliverable steps, meaningful checks, and any real-world evidence required. Each step has a useful outcome and links to its requirements. Cover every in-scope requirement; remove tasks with no requirement. Use the repository's executable format if it has a runner; otherwise this small Markdown form suffices:

```markdown
# Phase: <name>
Goal: <observable outcome>
Requirements: <IDs / links>
Dependencies: <completed work or unresolved decisions>

## <step>
Outcome: <user-visible behavior or enabling result>
Requirements: <IDs>
Verification: <specific command or observation and what success proves>
Status: pending

## Phase completion
<integration behavior and evidence required>
Independent review: pending
```

A planning-only request ends with the usable documents and material unresolved questions. When implementation is already authorized, proceed to execution after required checks; do not add another approval checkpoint just because planning ended.
