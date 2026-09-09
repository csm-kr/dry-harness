# dry-harness

This repository packages two Codex skills and small Python helpers. The default model is `gpt-6-astra`; do not silently fall back to another model.

- Skill behavior lives in `skills/`; packaging and usage are in `README.md`.
- Local tests use temporary fixtures with no production access. Complete requested edits, fix relevant failures, and rerun affected tests without asking at each step.
- Use `python3 -m unittest discover -s tests -v` for helper changes. A live model call is a separate smoke check, not part of this offline suite.
- Keep skill entry points concise and load references only for the requested workflow. Preserve user decisions and existing authorization.
