#!/usr/bin/env python3
"""Focused tests for the tracked candidate release profile."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("materialize_candidate_release_overrides.py")
SPEC = importlib.util.spec_from_file_location("candidate_release_materializer", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


EXPECTED = {
    "ars-creo": (
        "v0.1.0-alpha.3",
        "cd26792d8154f54c42dfbd63ddc614ef40a191fe",
        "b4855259c2c449c4c3fe972f3a8fddf3fcf13714305524e600604908ec75ad59",
    ),
    "ars-energistique": (
        "v0.1.0-alpha.2",
        "5b2c8aeea13a80d568c3c27a058d845a66413c08",
        "e6f9d86629009880e87762c062fa109070793e91de4cf6494820b0d75b584f8c",
    ),
    "ars-nouveau": (
        "v0.1.0-alpha.4",
        "dca10c4003fe9983492a9ab2d34d4d4207cda1cd",
        "52ddc7760b5710f9af285311fe446fc525adb0f02a98549ca4aa5248a38d2966",
    ),
    "ars-technica": (
        "v0.1.0-alpha.3",
        "61d33f096d15824d27c95e584dfc18a6468413cd",
        "d05a10f02557a425616dacf7ade89b1afed86ffef7aef1f0767d334d66fe1e46",
    ),
    "theurgy": (
        "v0.1.0-alpha.2",
        "74f8e54cafd52449ad2b75c0800019483876a5a9",
        "3da20938edeb04617f3227abe8d1fd18b342c59519fbfe0ff255284f9f97beef",
    ),
}


def expect_error(value: dict, manifest: dict, builder, fragment: str) -> None:
    with tempfile.TemporaryDirectory(prefix="candidate-release-profile-test-") as root:
        path = Path(root) / "profile.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        try:
            MODULE.load_profile(path, manifest, builder)
        except MODULE.ProfileError as exc:
            assert fragment in str(exc), str(exc)
        else:
            raise AssertionError(f"invalid profile was accepted: {fragment}")


def main() -> None:
    builder = MODULE.load_builder()
    manifest = builder.load_manifest(builder.DEFAULT_MANIFEST)
    profile = MODULE.load_profile(MODULE.DEFAULT_PROFILE, manifest, builder)
    actual = {
        entry["id"]: (
            entry["releaseTag"],
            entry["commit"],
            entry["artifact"]["sha256"],
        )
        for entry in profile["components"]
    }
    assert actual == EXPECTED
    assert profile["blueMap"] == {
        "version": builder.FEATURE_BACKPORT_VERSION,
        "commit": builder.FEATURE_BACKPORT_COMMIT,
    }

    raw = json.loads(MODULE.DEFAULT_PROFILE.read_text(encoding="utf-8"))
    invalid = json.loads(json.dumps(raw))
    invalid["blueMap"]["commit"] = "0" * 40
    expect_error(invalid, manifest, builder, "unknown BlueMap identity")

    invalid = json.loads(json.dumps(raw))
    invalid["components"][0]["repository"] = "jan-guenter/wrong"
    expect_error(invalid, manifest, builder, "repository differs")

    invalid = json.loads(json.dumps(raw))
    invalid["components"][0]["releaseTag"] = "v9.9.9"
    expect_error(invalid, manifest, builder, "release tag/version mismatch")

    invalid = json.loads(json.dumps(raw))
    invalid["components"].reverse()
    expect_error(invalid, manifest, builder, "unique and sorted")

    cli = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--validate-only"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert cli.returncode == 0, cli.stdout
    result = json.loads(cli.stdout)
    assert result["status"] == "passed"
    assert result["componentIds"] == sorted(EXPECTED)
    print("PASS: candidate release profile")


if __name__ == "__main__":
    main()
