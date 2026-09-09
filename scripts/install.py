#!/usr/bin/env python3
"""Install the two skills into one project, preserving unrelated files/config."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "skills"
SKILLS = ("dry-harness", "dry-review")


def install(project, update=False):
    project = Path(project).resolve(strict=True)
    if not project.is_dir():
        raise ValueError("Project must be an existing directory")
    target = project / ".agents" / "skills"
    if not target.resolve().is_relative_to(project):
        raise ValueError("Project skills directory points outside project")
    files = []
    for skill in SKILLS:
        destination = target / skill
        if destination.is_symlink():
            raise ValueError(f"Refusing symlink destination: {destination}")
        if destination.exists() and not update:
            raise FileExistsError(f"Already installed: {destination}; use --update to replace package-owned files")
        for src in sorted((SOURCE / skill).rglob("*")):
            if "__pycache__" in src.parts or src.suffix == ".pyc":
                continue
            if src.is_symlink():
                raise ValueError(f"Unexpected source symlink: {src}")
            if src.is_file():
                dst = destination / src.relative_to(SOURCE / skill)
                if dst.is_symlink() or not dst.resolve().is_relative_to(destination.resolve()):
                    raise ValueError(f"Refusing redirected destination: {dst}")
                if dst.exists() and not dst.is_file():
                    raise ValueError(f"Destination is not a file: {dst}")
                # Detect file-as-directory conflicts before copying anything.
                for parent in dst.parents:
                    if parent == project:
                        break
                    if parent.exists() and not parent.is_dir():
                        raise ValueError(f"Destination parent is not a directory: {parent}")
                files.append((src, dst))
    for src, dst in files:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return [target / skill for skill in SKILLS]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--update", action="store_true", help="Overwrite known package files; retain unrelated files")
    args = parser.parse_args()
    try:
        for path in install(args.project, args.update):
            print(path)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Install failed: {exc}\n")


if __name__ == "__main__":
    main()
