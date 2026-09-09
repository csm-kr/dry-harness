# Project workspace

`docs/` holds the current product decisions and contracts. Read the documents relevant to the requested change; do not load all documents for every edit. Fill in project-specific decisions during planning, without treating template headings as settled requirements.

- Product intent: `docs/PRD.md`; user journeys: `docs/USER_FLOW.md`.
- Implementation shape: `docs/ARCHITECTURE.md`; decisions: `docs/ADR.md`.
- Agreed constraints: `docs/RULES.md`; unresolved decisions/failures: `docs/ISSUES.md`.
- Use `dry-harness` for planning/execution and `dry-review` for independent review. The default model is `gpt-6-astra`; do not silently substitute another.
- Continue authorized local work through appropriate verification and repair. An initial implementation is not the completion condition.
- Update the document whose behavior/decision changed; do not rewrite unrelated docs. Repeated issues prompt diagnosis, not automatic promotion to universal rules.
- `scripts/execute.py` owns runtime status and runs declared checks independently. The child must not edit acceptance contracts or runtime state. If a contract needs correction, return the precise issue for the coordinator.

Run Codex from this project root so project hook commands resolve. Review new/changed hooks with `/hooks`; installation does not grant hook trust. The optional guards are best-effort checks; they do not replace sandboxing, meaningful tests, or required real-world observations.
