#!/usr/bin/env python3
"""Astra adaptation of Harness hook roles; stdlib only, project-local state."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

LEAN = "Use the simplest implementation that satisfies the agreed behavior. Preserve required tests and product contracts; do not add speculative abstractions."


def output(event, context="", deny=""):
    fields = {"hookEventName": event}
    if deny:
        fields.update(permissionDecision="deny", permissionDecisionReason=deny)
    elif context:
        fields["additionalContext"] = context
    else:
        return {}
    return {"hookSpecificOutput": fields}


def runtime(root):
    result = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=root,
                            capture_output=True, text=True, timeout=2)
    if result.returncode:
        return None
    path = Path(result.stdout.strip()) / "dry-harness-hooks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def danger(payload):
    tool = payload.get("tool_name", "").rsplit(".", 1)[-1]
    if tool not in {"Bash", "exec_command", "shell_command", "shell", "exec"}:
        return ""
    data = payload.get("tool_input", {})
    if isinstance(data, dict):
        command = data.get("cmd", data.get("command", data.get("code", "")))
    else:
        command = data
    if not isinstance(command, str):
        return ""
    patterns = [
        r"\bgit\s+(?:-C\s+\S+\s+)?reset\b[^;\n]*--hard\b",
        r"\bgit\s+(?:-C\s+\S+\s+)?push\b[^;\n]*(?:--force(?:-with-lease)?\b|\s-f\b)",
        r"\bDROP\s+(?:TABLE|DATABASE)\b",
        r"\b(?:supabase\s+)?db\s+reset\b",
        r"\brm\s+(?:-[A-Za-z]*[rf][A-Za-z]*\s+)+[\"']?(?:/|~|\$HOME|\$\{HOME\}|\.)(?:[\"']?(?:\s|$|[;)]))",
    ]
    if any(re.search(pattern, command, re.I) for pattern in patterns):
        return "Destructive command matched the project guard. Inspect its target and the existing authorization before changing this guard or choosing a scoped operation."
    # Protect common accidental secret dumps, without blocking .env setup or
    # claiming to parse all shell/Python/JavaScript ways to read a secret.
    if re.search(r"\b(?:cat|head|tail|less|more)\s+(?:[^;\n]*\s+)?[\"']?(?:[^\s\"';]*/)?\.env(?!\.example\b|\.sample\b)(?:\b|\.)", command):
        return "Avoid printing .env secrets; inspect variable names or a redacted example instead."
    return ""


def handle(event, payload, now=None):
    now = time.time() if now is None else now
    if event == "PreToolUse":
        denied = danger(payload)
        if denied:
            return output(event, deny=denied)
        data = payload.get("tool_input", {})
        text = data if isinstance(data, str) else json.dumps(data)
        tool = payload.get("tool_name", "").rsplit(".", 1)[-1]
        if tool in {"Write", "Edit", "apply_patch"} and re.search(r"(?:migrations/|schema\.|authorization|permissions)", text, re.I):
            return output(event, "This change may affect persisted data or authorization. Verify the changed behavior and failure cases; test-file existence alone is not evidence.")
        return {}
    if event not in {"SessionStart", "SubagentStart", "UserPromptSubmit"}:
        return {}
    root = Path(payload.get("cwd") or os.getcwd()).resolve()
    state_dir = runtime(root)
    session = hashlib.sha256(str(payload.get("session_id", "default")).encode()).hexdigest()[:24]
    state_file = state_dir / (session + ".json") if state_dir else None
    mode = "lean"
    if state_file and state_file.exists():
        mode = json.loads(state_file.read_text()).get("mode", "lean")
    if event == "UserPromptSubmit":
        match = re.fullmatch(r"\s*[$/]dry-harness(?:\s+|:)mode\s+(lean|off)\s*", str(payload.get("prompt", "")))
        if not match:
            return {}
        mode = match[1]
        if state_file:
            state_file.write_text(json.dumps({"mode": mode}))
        return output(event, f"Dry Harness guidance mode: {mode}. " + (LEAN if mode == "lean" else "No extra simplicity guidance."))
    context = LEAN if mode == "lean" else ""
    if event == "SubagentStart":
        return output(event, context)
    context = "Use relevant docs and the selected phase contract. Continue authorized implementation through verification and repair. " + context
    # Retain upstream's weekly reminder role; no automatic audits/tests and no
    # global mode/statusline changes. First session records time without nagging.
    days = float(os.environ.get("DRY_HARNESS_WEEKLY_DAYS", "7"))
    if state_dir and days > 0:
        stamp = state_dir / "weekly.json"
        last = json.loads(stamp.read_text()).get("time", now) if stamp.exists() else now
        if not stamp.exists() or now - last >= days * 86400:
            stamp.write_text(json.dumps({"time": now}))
        if now - last >= days * 86400:
            context += " Periodic maintenance is due: review stale project instructions and verification cost when useful; do not interrupt this task or launch an audit automatically."
    return output(event, context)


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        event = sys.argv[1] if len(sys.argv) > 1 else payload.get("hook_event_name", "")
        result = handle(event, payload)
        if result:
            print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        # A malformed advisory input cannot block the session. This hook is a
        # best-effort guard, not an operating-system security boundary.
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
