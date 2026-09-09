# Project hooks

The full installer adds `.codex/hooks.json` and `.codex/hooks/dry_harness.py`, merging existing hook events without duplicate commands. Start Codex from the project root. New config enables `features.hooks`; existing config is preserved, so enable hooks explicitly if that config disables them.

Use `/hooks` to inspect and trust the new or changed definitions. The installer never edits host trust records or uses a trust-bypass flag. Hook installation and active host enforcement are distinct. See the [official Codex hooks guide](https://learn.chatgpt.com/docs/hooks).

| Event | Astra behavior |
| --- | --- |
| SessionStart | Short relevant-context/completion reminder and restrained simplicity guidance; weekly maintenance reminder only when due. |
| SubagentStart | Short simplicity guidance in the assigned task's scope. |
| UserPromptSubmit | `$dry-harness mode lean` / `$dry-harness mode off` changes only the session guidance mode. Ordinary prompts inject nothing. |
| PreToolUse | Best-effort destructive-command/secret-output guard; targeted advice for persistence/authorization edits, without a test-filename gate. |

The six upstream roles (danger, TDD, activation, subagent, mode tracking, weekly check) share one stdlib Python handler. No Node runtime or global Ponytail statusline/config writes are required. `DRY_HARNESS_WEEKLY_DAYS=0` disables weekly reminders; the default is 7 days and first use records time without interrupting setup. Hook state lives under the Git metadata directory, not public docs.

Danger matches include hard resets, force pushes, DROP operations, DB resets, root/home/current-directory removal and common `.env` dumps. Ordinary relative cleanup and `.env.example` reads remain available. These are pattern checks, not a complete shell parser, secret scanner or security boundary. A justified command that matches requires deliberate adjustment of the project guard consistent with existing authorization; do not repeatedly request approval already given.

No Stop hook runs the whole test suite: the executor owns acceptance verification. No hook weakens sandbox/permissions. Invalid advisory payloads fail open so a broken reminder does not freeze work. `.env` setup is not blocked wholesale; keep secret handling scoped and avoid dumping values into model-visible output.
