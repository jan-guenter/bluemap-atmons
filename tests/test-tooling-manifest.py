#!/usr/bin/env python3
"""Focused tests for the development-tool manifest contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_bluemap_atmons",
    REPOSITORY_ROOT / "tools" / "validate.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load tools/validate.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def valid_component() -> dict[str, object]:
    return {
        "id": "addon-toolkit",
        "kind": "development-tool",
        "repository": "jan-guenter/bluemap-addon-toolkit",
        "submodule_path": "toolkit",
        "commit": "a" * 40,
        "release_tag": "v0.1.0-alpha.1",
        "artifact": {
            "filename": "bluemap_addon_toolkit-0.1.0a1-py3-none-any.whl",
            "url": (
                "https://github.com/jan-guenter/bluemap-addon-toolkit/releases/"
                "download/v0.1.0-alpha.1/"
                "bluemap_addon_toolkit-0.1.0a1-py3-none-any.whl"
            ),
            "size_bytes": 1,
            "sha256": "b" * 64,
        },
    }


class ToolingManifestTest(unittest.TestCase):
    def validate(self, value: object) -> tuple[list[str], dict[str, object] | None]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "tooling" / "manifest.json"
            path.parent.mkdir()
            path.write_text(json.dumps(value), encoding="utf-8")
            original = VALIDATOR.ROOT
            try:
                VALIDATOR.ROOT = root
                return VALIDATOR.validate_tooling_manifest(path)
            finally:
                VALIDATOR.ROOT = original

    def test_accepts_exact_development_tool_record(self) -> None:
        errors, data = self.validate(
            {"schema_version": 1, "components": [valid_component()]}
        )
        self.assertEqual([], errors)
        self.assertIsNotNone(data)

    def test_rejects_wrong_kind_and_artifact_identity(self) -> None:
        component = valid_component()
        component["kind"] = "addon"
        component["artifact"] = {
            "filename": "tool.jar",
            "url": "https://example.invalid/tool.jar",
            "size_bytes": 0,
            "sha256": "BAD",
        }
        errors, _data = self.validate(
            {"schema_version": 1, "components": [component]}
        )
        self.assertTrue(any("kind must be development-tool" in error for error in errors))
        self.assertTrue(any("artifact filename" in error for error in errors))
        self.assertTrue(any("artifact size_bytes" in error for error in errors))
        self.assertTrue(any("artifact sha256" in error for error in errors))

    def test_rejects_boolean_schema_version(self) -> None:
        errors, _data = self.validate(
            {"schema_version": True, "components": [valid_component()]}
        )
        self.assertTrue(any("schema_version must be 1" in error for error in errors))

    def test_rejects_degenerate_wheel_filename(self) -> None:
        component = valid_component()
        artifact = component["artifact"]
        assert isinstance(artifact, dict)
        artifact["filename"] = ".whl"
        artifact["url"] = (
            "https://github.com/jan-guenter/bluemap-addon-toolkit/releases/"
            "download/v0.1.0-alpha.1/.whl"
        )
        errors, _data = self.validate(
            {"schema_version": 1, "components": [component]}
        )
        self.assertTrue(any("artifact filename" in error for error in errors))

    def test_malformed_field_types_report_errors_without_crashing(self) -> None:
        component = valid_component()
        component["repository"] = []
        component["submodule_path"] = []
        component["artifact"] = {
            "filename": [],
            "url": [],
            "size_bytes": False,
            "sha256": [],
        }
        errors, _data = self.validate(
            {"schema_version": 1, "components": [component]}
        )
        self.assertGreaterEqual(len(errors), 5)

    def test_compatibility_manifest_non_object_component_reports_error(self) -> None:
        manifest = json.loads(
            (REPOSITORY_ROOT / "versions" / "1.2.0" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["components"].append(None)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "versions" / "1.2.0" / "manifest.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(manifest), encoding="utf-8")
            original = VALIDATOR.ROOT
            try:
                VALIDATOR.ROOT = root
                errors, _data = VALIDATOR.validate_manifest(path)
            finally:
                VALIDATOR.ROOT = original
        self.assertTrue(any("components[52]: must be an object" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
