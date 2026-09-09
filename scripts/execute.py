#!/usr/bin/env python3
"""Repository entry point; the installed skill carries the same executor."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    installed = root / ".agents/skills/dry-harness/scripts/execute.py"
    source = installed if installed.exists() else root / "skills/dry-harness/scripts/execute.py"
    runpy.run_path(str(source), run_name="__main__")
