#!/usr/bin/env python3
"""Materialize a path-bound candidate lock from reviewed public releases."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = (
    ROOT
    / "integration"
    / "candidate-releases"
    / "atmons-1.2.0-bluemap-5.23.json"
)
BUILDER_PATH = Path(__file__).with_name("build_candidate_addons.py")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+-]{0,127}$")


class ProfileError(RuntimeError):
    pass


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_builder():
    spec = importlib.util.spec_from_file_location("candidate_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise ProfileError("cannot load candidate add-on builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require_exact_keys(value: object, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ProfileError(f"{label} must be an object")
    if set(value) != expected:
        raise ProfileError(
            f"{label} keys differ from the exact contract: "
            f"expected={sorted(expected)}, actual={sorted(value)}"
        )
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise ProfileError(
            f"{' '.join(command)} failed ({result.returncode}):\n{result.stdout.strip()}"
        )
    return result.stdout.strip()


def load_profile(path: Path, manifest: dict, builder) -> dict:
    try:
        raw = path.read_bytes()
        profile = json.loads(raw, object_pairs_hook=unique_object)
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ProfileError(f"cannot read candidate release profile {path}: {exc}") from exc
    require_exact_keys(
        profile,
        {"schemaVersion", "atmons", "blueMap", "components"},
        "candidate release profile",
    )
    if profile["schemaVersion"] != 1 or type(profile["schemaVersion"]) is not int:
        raise ProfileError("candidate release profile schemaVersion must be 1")
    if profile["atmons"] != "1.2.0":
        raise ProfileError("candidate release profile must target ATMons 1.2.0")
    blue_map = require_exact_keys(
        profile["blueMap"], {"version", "commit"}, "candidate BlueMap"
    )
    if blue_map != {
        "version": builder.FEATURE_BACKPORT_VERSION,
        "commit": builder.FEATURE_BACKPORT_COMMIT,
    }:
        raise ProfileError("candidate release profile targets an unknown BlueMap identity")

    known = {
        component["id"]: component
        for component in manifest["components"]
        if component["kind"] == "addon"
    }
    entries = profile["components"]
    if not isinstance(entries, list) or not entries:
        raise ProfileError("candidate release profile components must be non-empty")
    ids: list[str] = []
    filenames: set[str] = set()
    for index, entry_value in enumerate(entries):
        label = f"candidate release component {index}"
        entry = require_exact_keys(
            entry_value,
            {
                "id",
                "repository",
                "commit",
                "releaseTag",
                "tagObject",
                "artifact",
            },
            label,
        )
        component_id = entry["id"]
        if not isinstance(component_id, str) or component_id not in known:
            raise ProfileError(f"{label} has unknown add-on ID {component_id!r}")
        ids.append(component_id)
        if entry["repository"] != known[component_id]["repository"]:
            raise ProfileError(f"{component_id}: repository differs from the manifest")
        if not isinstance(entry["commit"], str) or not HEX40.fullmatch(entry["commit"]):
            raise ProfileError(f"{component_id}: invalid release commit")
        if not isinstance(entry["tagObject"], str) or not HEX40.fullmatch(
            entry["tagObject"]
        ):
            raise ProfileError(f"{component_id}: invalid annotated tag object")
        artifact = require_exact_keys(
            entry["artifact"],
            {"filename", "url", "sizeBytes", "sha256", "version"},
            f"{component_id} artifact",
        )
        version = artifact["version"]
        filename = artifact["filename"]
        if not isinstance(version, str) or not VERSION.fullmatch(version):
            raise ProfileError(f"{component_id}: invalid release version")
        if entry["releaseTag"] != f"v{version}":
            raise ProfileError(f"{component_id}: release tag/version mismatch")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not filename.endswith(".jar")
            or filename in filenames
        ):
            raise ProfileError(f"{component_id}: invalid or duplicate artifact filename")
        filenames.add(filename)
        expected_url = (
            f"https://github.com/{entry['repository']}/releases/download/"
            f"{entry['releaseTag']}/{filename}"
        )
        if artifact["url"] != expected_url:
            raise ProfileError(f"{component_id}: artifact URL differs from release identity")
        if (
            isinstance(artifact["sizeBytes"], bool)
            or not isinstance(artifact["sizeBytes"], int)
            or artifact["sizeBytes"] < 1
        ):
            raise ProfileError(f"{component_id}: invalid artifact size")
        if not isinstance(artifact["sha256"], str) or not HEX64.fullmatch(
            artifact["sha256"]
        ):
            raise ProfileError(f"{component_id}: invalid artifact SHA-256")
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ProfileError("candidate release profile components must be unique and sorted")
    return {**profile, "profileSha256": hashlib.sha256(raw).hexdigest()}


def checkout_release(entry: dict, destination: Path) -> None:
    if destination.exists():
        raise ProfileError(f"refusing to reuse existing checkout {destination}")
    destination.mkdir(parents=True)
    repository_url = f"https://github.com/{entry['repository']}.git"
    run(["git", "init", "--quiet"], destination)
    run(["git", "remote", "add", "origin", repository_url], destination)
    tag_ref = f"refs/tags/{entry['releaseTag']}"
    run(
        [
            "git",
            "fetch",
            "--quiet",
            "--depth=1",
            "origin",
            f"{tag_ref}:{tag_ref}",
        ],
        destination,
    )
    if run(["git", "cat-file", "-t", tag_ref], destination) != "tag":
        raise ProfileError(f"{entry['id']}: release tag is not annotated")
    tag_object = run(["git", "rev-parse", tag_ref], destination)
    commit = run(["git", "rev-parse", f"{tag_ref}^{{commit}}"], destination)
    if tag_object != entry["tagObject"] or commit != entry["commit"]:
        raise ProfileError(f"{entry['id']}: fetched release tag identity mismatch")
    run(["git", "checkout", "--quiet", "--detach", entry["commit"]], destination)
    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"], destination):
        raise ProfileError(f"{entry['id']}: materialized release checkout is not clean")


def download_artifact(entry: dict, destination: Path) -> None:
    artifact = entry["artifact"]
    if destination.exists():
        raise ProfileError(f"refusing to overwrite existing artifact {destination}")
    request = urllib.request.Request(
        artifact["url"],
        headers={"User-Agent": "bluemap-atmons-candidate-materializer/1"},
    )
    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open(
            "wb"
        ) as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    if (
        destination.stat().st_size != artifact["sizeBytes"]
        or sha256(destination) != artifact["sha256"]
    ):
        raise ProfileError(f"{entry['id']}: downloaded release artifact identity mismatch")


def materialize(profile: dict, work_root: Path, output: Path, builder, manifest: dict) -> dict:
    if work_root.exists() and any(work_root.iterdir()):
        raise ProfileError(f"work root must be absent or empty: {work_root}")
    work_root.mkdir(parents=True, exist_ok=True)
    checkouts = work_root / "checkouts"
    artifacts = work_root / "artifacts"
    checkouts.mkdir()
    artifacts.mkdir()
    components = []
    for entry in profile["components"]:
        checkout = checkouts / entry["id"]
        artifact_path = artifacts / entry["artifact"]["filename"]
        checkout_release(entry, checkout)
        download_artifact(entry, artifact_path)
        components.append(
            {
                "id": entry["id"],
                "source": {
                    "checkout": str(checkout.resolve()),
                    "commit": entry["commit"],
                },
                "artifact": {
                    "path": str(artifact_path.resolve()),
                    "filename": entry["artifact"]["filename"],
                    "sizeBytes": entry["artifact"]["sizeBytes"],
                    "sha256": entry["artifact"]["sha256"],
                    "version": entry["artifact"]["version"],
                },
            }
        )
    lock = {"schemaVersion": 1, "atmons": "1.2.0", "components": components}
    raw = (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode("utf-8")
    validation_path = work_root / ".override-lock.validation.json"
    validation_path.write_bytes(raw)
    try:
        loaded = builder.load_addon_override_lock(validation_path.resolve(), manifest)
    finally:
        validation_path.unlink(missing_ok=True)
    if loaded["componentIds"] != [entry["id"] for entry in profile["components"]]:
        raise ProfileError("materialized override order differs from the release profile")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_suffix(output.suffix + ".tmp")
    temporary_output.write_bytes(raw)
    temporary_output.replace(output)
    return {
        "profileSha256": profile["profileSha256"],
        "lockSha256": hashlib.sha256(raw).hexdigest(),
        "componentIds": loaded["componentIds"],
        "output": str(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        builder = load_builder()
        manifest = builder.load_manifest(builder.DEFAULT_MANIFEST)
        profile = load_profile(args.profile.resolve(), manifest, builder)
        if args.validate_only:
            if args.work_root is not None or args.output is not None:
                raise ProfileError("--validate-only does not accept output paths")
            result = {
                "profileSha256": profile["profileSha256"],
                "componentIds": [entry["id"] for entry in profile["components"]],
                "status": "passed",
            }
        else:
            if args.work_root is None or args.output is None:
                raise ProfileError("--work-root and --output are required")
            if not args.work_root.is_absolute() or not args.output.is_absolute():
                raise ProfileError("--work-root and --output must be absolute paths")
            result = materialize(
                profile,
                args.work_root.resolve(),
                args.output.resolve(),
                builder,
                manifest,
            )
            result["status"] = "passed"
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
