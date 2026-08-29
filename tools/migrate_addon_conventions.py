#!/usr/bin/env python3
"""Render the managed addon-v1 convention files into clean add-on worktrees."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "standards" / "addon-v1"
PROPERTY = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9_.-]*)\s*=\s*(.*?)\s*$")


@dataclass(frozen=True)
class Change:
    path: str
    content: bytes
    only_if_missing: bool = False


def git_status(repository: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), "status", "--porcelain"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"cannot inspect {repository}")
    return result.stdout


def properties(repository: Path) -> dict[str, str]:
    path = repository / "gradle.properties"
    if not path.is_file():
        raise ValueError(f"{repository}: gradle.properties is missing")
    return dict(PROPERTY.findall(path.read_text(encoding="utf-8")))


def render(template: str, values: dict[str, str]) -> bytes:
    text = template
    for key, value in values.items():
        text = text.replace(f"@@{key}@@", value)
    unresolved = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", text)))
    if unresolved:
        raise ValueError(f"unresolved template tokens: {unresolved}")
    return text.encode("utf-8")


def insert_checkstyle(build: str) -> str:
    if re.search(r"id\s+['\"]checkstyle['\"]", build):
        return build
    updated, count = re.subn(
        r"(plugins\s*\{\s*\n\s*id\s+['\"]java-library['\"]\s*\n)",
        r"\1    id 'checkstyle'\n",
        build,
        count=1,
    )
    if count != 1:
        raise ValueError("could not insert checkstyle plugin")
    block = """

checkstyle {
    toolVersion = '10.18.2'
    configFile = file('config/checkstyle/checkstyle.xml')
}

tasks.withType(Checkstyle).configureEach {
    reports {
        xml.required = true
        html.required = true
    }
}
"""
    anchor = "tasks.named('jar', Jar).configure {"
    if anchor in updated:
        return updated.replace(anchor, block + "\n" + anchor, 1)
    return updated.rstrip() + block + "\n"


def planned_changes(repository: Path) -> list[Change]:
    values = properties(repository)
    required = {
        "ADDON_ID": values.get("addon_id", ""),
        "ADDON_NAME": values.get("addon_name", ""),
        "ADDON_VERSION": values.get("addon_version", ""),
        "BLUEMAP_VERSION": values.get("bluemap_version", ""),
    }
    if not all(required.values()):
        raise ValueError(f"{repository}: required add-on properties are incomplete")
    changes = [
        Change(".editorconfig", (STANDARD / ".editorconfig").read_bytes()),
        Change(".gitattributes", (STANDARD / ".gitattributes").read_bytes()),
        Change(
            "config/checkstyle/checkstyle.xml",
            (STANDARD / "checkstyle.xml").read_bytes(),
        ),
        Change(
            "AGENTS.md",
            render((STANDARD / "AGENTS.md.template").read_text(encoding="utf-8"), required),
            only_if_missing=True,
        ),
        Change(
            "docs/RELEASING.md",
            (STANDARD / "RELEASING.md.template").read_bytes(),
            only_if_missing=True,
        ),
    ]
    build_path = repository / "build.gradle"
    build = build_path.read_text(encoding="utf-8")
    updated = insert_checkstyle(build)
    if updated != build:
        changes.append(Change("build.gradle", updated.encode("utf-8")))
    return changes


def differences(repository: Path, changes: list[Change]) -> list[Change]:
    result: list[Change] = []
    for change in changes:
        path = repository / change.path
        if change.only_if_missing and path.exists():
            continue
        if not path.is_file() or path.read_bytes() != change.content:
            result.append(change)
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repositories", nargs="+", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    stale = False
    for raw in args.repositories:
        repository = raw.resolve()
        if args.write and git_status(repository):
            print(f"refusing dirty repository: {repository}", file=sys.stderr)
            return 2
        try:
            pending = differences(repository, planned_changes(repository))
        except (OSError, ValueError, RuntimeError) as exc:
            print(exc, file=sys.stderr)
            return 2
        if pending:
            stale = True
        state = "current" if not pending else "would update"
        print(f"{state} {repository}")
        for change in pending:
            print(f"  {change.path}")
            if args.write:
                target = repository / change.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(change.content)
    if args.check and stale:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
