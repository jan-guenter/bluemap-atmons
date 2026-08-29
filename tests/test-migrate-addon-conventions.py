#!/usr/bin/env python3
"""Focused tests for the deterministic addon-v1 migration renderer."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "migrate_addon_conventions", ROOT / "tools" / "migrate_addon_conventions.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load tools/migrate_addon_conventions.py")
MIGRATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MIGRATOR
SPEC.loader.exec_module(MIGRATOR)


class MigrationRendererTest(unittest.TestCase):
    def fixture(self, root: Path) -> None:
        (root / "gradle.properties").write_text(
            "\n".join(
                (
                    "addon_id=bluemap-fixture",
                    "addon_name=BlueMap Fixture Add-on",
                    "addon_version=0.1.0-alpha.1",
                    "bluemap_version=5.22-test",
                    "",
                )
            ),
            encoding="utf-8",
        )
        (root / "build.gradle").write_text(
            "plugins {\n    id 'java-library'\n    id 'maven-publish'\n}\n\n"
            "tasks.named('jar', Jar).configure {\n}\n",
            encoding="utf-8",
        )

    def test_renderer_is_deterministic_and_adds_checkstyle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self.fixture(repository)
            first = MIGRATOR.planned_changes(repository)
            second = MIGRATOR.planned_changes(repository)
            self.assertEqual(first, second)
            by_path = {item.path: item.content for item in first}
            build = by_path["build.gradle"].decode()
            self.assertIn("id 'checkstyle'", build)
            self.assertIn("toolVersion = '10.18.2'", build)
            self.assertIn("BlueMap Fixture Add-on", by_path["AGENTS.md"].decode())

    def test_write_refuses_dirty_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self.fixture(repository)
            subprocess.run(["git", "-C", str(repository), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
            (repository / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            self.assertEqual(2, MIGRATOR.main([str(repository), "--write"]))


if __name__ == "__main__":
    unittest.main()
