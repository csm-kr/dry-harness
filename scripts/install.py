#!/usr/bin/env python3
"""Install Astra skills, executor, document templates and project-local hooks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
SOURCE = PACKAGE / "skills"
SKILLS = ("dry-harness", "dry-review")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def install(project, update=False, skills_only=False, docs=()):
    project = Path(project).resolve(strict=True)
    if not project.is_dir():
        raise ValueError("Project must be an existing directory")
    pending, kept = {}, []

    def checked(relative):
        path = project / relative
        if path.is_symlink() or not path.resolve().is_relative_to(project):
            raise ValueError(f"Refusing redirected destination: {path}")
        for parent in path.parents:
            if parent == project:
                break
            if parent.is_symlink():
                raise ValueError(f"Refusing symlink parent: {parent}")
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"Destination parent is not a directory: {parent}")
        if path.exists() and not path.is_file():
            raise ValueError(f"Destination is not a file: {path}")
        return path

    def add(relative, data, preserve=False):
        path = checked(relative)
        if preserve and path.exists():
            kept.append(relative)
        else:
            pending[path] = data

    for skill in SKILLS:
        destination = project / ".agents/skills" / skill
        if destination.is_symlink():
            raise ValueError(f"Refusing symlink destination: {destination}")
        if destination.exists() and not update:
            raise FileExistsError(f"Already installed: {destination}; use --update for package files")
        for src in sorted((SOURCE / skill).rglob("*")):
            if "__pycache__" in src.parts or src.suffix == ".pyc":
                continue
            if src.is_symlink():
                raise ValueError(f"Unexpected source symlink: {src}")
            if src.is_file():
                add(str(Path('.agents/skills') / skill / src.relative_to(SOURCE / skill)), src.read_bytes())

    if not skills_only:
        manifest_path = checked('.codex/dry-harness-install.json')
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"files": {}}
        owned = manifest["files"]
        if not isinstance(owned, dict):
            raise ValueError("Invalid installation manifest")
        managed = {}
        for src in sorted((PACKAGE / "template").rglob("*")):
            if not src.is_file() or "__pycache__" in src.parts or src.suffix == ".pyc":
                continue
            rel = str(src.relative_to(PACKAGE / "template"))
            if rel == '.codex/hooks.json':
                continue
            if rel == '.codex/hooks/dry_harness.py':
                managed[rel] = src.read_bytes()
            else:
                add(rel, src.read_bytes(), preserve=True)
        managed['scripts/execute.py'] = (PACKAGE / 'scripts/execute.py').read_bytes()
        for rel, data in managed.items():
            target = checked(rel)
            if target.exists() and target.read_bytes() != data:
                if not update or owned.get(rel) != digest(target.read_bytes()):
                    if rel.endswith('dry_harness.py'):
                        raise FileExistsError(f"Existing hook differs: {rel}; merge it explicitly or use --skills-only")
                    kept.append(rel)
                    continue
            add(rel, data)
            owned[rel] = digest(data)
        for name in docs:
            if name not in {p.stem for p in (PACKAGE / 'docs-catalog').glob('*.md') if p.stem != 'README'}:
                raise ValueError(f"Unknown optional document: {name}")
            add(f'docs/{name}.md', (PACKAGE / 'docs-catalog' / (name + '.md')).read_bytes(), preserve=True)
        hooks_path = checked('.codex/hooks.json')
        hooks = json.loads(hooks_path.read_text()) if hooks_path.exists() else {"hooks": {}}
        if not isinstance(hooks, dict) or not isinstance(hooks.get('hooks'), dict):
            raise ValueError("Existing hooks.json must contain a hooks object")
        wanted = json.loads((PACKAGE / 'template/.codex/hooks.json').read_text())
        for event, groups in wanted['hooks'].items():
            existing = hooks['hooks'].setdefault(event, [])
            if not isinstance(existing, list):
                raise ValueError(f"Existing hook event is not an array: {event}")
            commands = set()
            for group in existing:
                if not isinstance(group, dict) or not isinstance(group.get('hooks'), list):
                    raise ValueError(f"Invalid existing hook group: {event}")
                for handler in group['hooks']:
                    if not isinstance(handler, dict):
                        raise ValueError(f"Invalid existing hook handler: {event}")
                    commands.add(handler.get('command'))
            for group in groups:
                if group['hooks'][0]['command'] not in commands:
                    existing.append(group)
        add('.codex/hooks.json', (json.dumps(hooks, ensure_ascii=False, indent=2) + '\n').encode())
        add('.codex/dry-harness-install.json', (json.dumps(manifest, indent=2) + '\n').encode())

    # Preflight all inputs/paths/merges before writing. Disk/permission failures
    # can still interrupt a copy; rerun --update after resolving them.
    for path, data in pending.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for relative in kept:
        print(f"Kept existing project file: {relative}")
    return list(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--update", action="store_true", help="Update skill files and unmodified managed code; preserve project docs/config")
    parser.add_argument("--skills-only", action="store_true", help="Install only skills and their bundled helpers")
    parser.add_argument("--doc", action="append", default=[], help="Optional document name, e.g. DB; repeat as needed")
    args = parser.parse_args()
    try:
        if args.skills_only and args.doc:
            raise ValueError('--doc cannot be combined with --skills-only')
        for path in install(args.project, args.update, args.skills_only, args.doc):
            print(path)
        if not args.skills_only:
            print('Start Codex from the project root; use /hooks to review and trust new or changed hooks. Existing config/model values were preserved.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Install failed: {exc}\n")


if __name__ == "__main__":
    main()
