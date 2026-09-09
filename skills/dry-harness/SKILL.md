---
name: dry-harness
description: Plan or execute a development phase using existing project contracts and independent review.
---

Use Harness for the working plan and Dryforge-inspired independent checks for intent and delivery. Respond in the user's language. The Astra edition assumes `gpt-6-astra`; a skill cannot change its host model. Use the user's selected model, and never silently substitute another.

- **Ready / planning:** follow [planning](references/planning.md) to turn the requested outcome into an implementable contract and phase.
- **Run / resume:** follow [execution](references/execution.md) to deliver the selected phase through verification and repair.
- **Setup / hooks:** the repository's `scripts/install.py` installs the executor, six base docs and Codex hooks. See [hooks](references/hooks.md) for behavior and trust setup; preserve existing project files.
- **Review only:** use the sibling `dry-review` skill. Its [review contract](../dry-review/SKILL.md) also describes independent planning checks.

Existing project contracts and explicit user decisions govern the work. Keep one canonical set of requirements and phases; adapt to the repository's paths. Do not maintain a second `.dryforge` spec beside an active Harness spec. Apply ordinary small edits directly without introducing a phase ceremony.

Read only the relevant contract, code, and evidence. Continue authorized work until the requested completion conditions hold. Resolve implementation choices yourself; ask only for missing product intent or authorization that materially affects the next action. Existing authorization remains valid.
