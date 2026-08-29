#!/usr/bin/env python3
"""Focused tests for the add-on repository contract checker."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_addon_conventions", ROOT / "tools" / "check_addon_conventions.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load tools/check_addon_conventions.py")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class AddonConventionTest(unittest.TestCase):
    def test_standard_files_are_self_consistent(self) -> None:
        standard = ROOT / "standards" / "addon-v1"
        self.assertTrue((standard / ".editorconfig").read_bytes().endswith(b"\n"))
        self.assertTrue((standard / ".gitattributes").read_bytes().endswith(b"\n"))
        checkstyle = (standard / "checkstyle.xml").read_text(encoding="utf-8")
        self.assertNotIn('module name="UnusedImports"', checkstyle)
        self.assertIn('module name="NeedBraces"', checkstyle)
        self.assertIn('module name="LineLength"', checkstyle)
        self.assertIn('module name="ModifierOrder"', checkstyle)
        self.assertIn('module name="WhitespaceAround"', checkstyle)

    def test_reports_missing_contract_and_unpinned_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            subprocess.run(["git", "-C", str(repository), "init", "-q"], check=True)
            workflow = repository / ".github" / "workflows" / "ci.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("steps:\n  - uses: actions/checkout@v4\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(repository), "add", ".github/workflows/ci.yml"],
                check=True,
            )
            result = CHECKER.check_repository(repository)
            messages = [item["message"] for item in result["findings"]]
            self.assertFalse(result["ok"])
            self.assertIn("required file is missing", messages)
            self.assertIn("action is not pinned to a full commit: actions/checkout@v4", messages)

    def test_standard_comparison_accepts_exact_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            source = ROOT / "standards" / "addon-v1" / ".editorconfig"
            shutil.copyfile(source, repository / ".editorconfig")
            self.assertEqual(
                [], CHECKER.compare_standard(repository, ".editorconfig", ".editorconfig")
            )


if __name__ == "__main__":
    unittest.main()
