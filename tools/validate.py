#!/usr/bin/env python3
"""Validate BlueMap ATMons compatibility manifests and pinned submodules."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ALLOWED_TRACKED_JARS = {
    "integration/harness/gradle/wrapper/gradle-wrapper.jar":
        "55243ef57851f12b070ad14f7f5bb8302daceeebc5bce5ece5fa6edb23e1145c",
}


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: root must be an object")
    return value


def exact_keys(errors: list[str], where: str, value: Any, expected: set[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{where}: must be an object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(
            f"{where}: keys differ; missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
        return False
    return True


def integer(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def validate_manifest(path: Path) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    rel = path.relative_to(ROOT)
    try:
        data = load_json(path)
    except ValueError as exc:
        return [str(exc)], None

    if not exact_keys(
        errors,
        str(rel),
        data,
        {"schema_version", "atmons", "runtime", "release", "components"},
    ):
        return errors, data
    if not integer(data["schema_version"], 1) or data["schema_version"] != 1:
        errors.append(f"{rel}: schema_version must be 1")

    atmons = data["atmons"]
    if exact_keys(errors, f"{rel}: atmons", atmons, {"version", "tag", "pack_commit"}):
        version = atmons["version"]
        if not isinstance(version, str) or not VERSION.fullmatch(version):
            errors.append(f"{rel}: invalid atmons.version")
        elif version != path.parent.name:
            errors.append(f"{rel}: version does not match parent directory")
        if atmons["tag"] != f"atmons-{version}":
            errors.append(f"{rel}: atmons.tag must be atmons-{version}")
        if not isinstance(atmons["pack_commit"], str) or not HEX40.fullmatch(
            atmons["pack_commit"]
        ):
            errors.append(f"{rel}: invalid pack_commit")

    runtime = data["runtime"]
    if exact_keys(errors, f"{rel}: runtime", runtime, {"minecraft", "neoforge", "java"}):
        if not all(isinstance(runtime[key], str) and runtime[key] for key in ("minecraft", "neoforge")):
            errors.append(f"{rel}: runtime versions must be non-empty strings")
        if not integer(runtime["java"], 1):
            errors.append(f"{rel}: runtime.java must be a positive integer")

    release = data["release"]
    exact_keys(errors, f"{rel}: release", release, {"addon_count", "component_count"})

    components = data["components"]
    if not isinstance(components, list) or not components:
        errors.append(f"{rel}: components must be a non-empty array")
        return errors, data

    ids: list[str] = []
    repositories: set[str] = set()
    paths: set[str] = set()
    filenames: set[str] = set()
    blue_count = 0
    for index, component in enumerate(components):
        where = f"{rel}: components[{index}]"
        if not exact_keys(
            errors,
            where,
            component,
            {
                "id",
                "kind",
                "repository",
                "submodule_path",
                "commit",
                "release_tag",
                "artifact",
                "requires",
            },
        ):
            continue

        component_id = component["id"]
        if not isinstance(component_id, str) or not ID.fullmatch(component_id):
            errors.append(f"{where}: invalid id")
            continue
        ids.append(component_id)
        repository = component["repository"]
        path_value = component["submodule_path"]
        if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
            errors.append(f"{where}: invalid repository")
        elif repository in repositories:
            errors.append(f"{where}: duplicate repository {repository}")
        else:
            repositories.add(repository)
        if not isinstance(path_value, str):
            errors.append(f"{where}: submodule_path must be a string")
        elif path_value in paths:
            errors.append(f"{where}: duplicate submodule_path {path_value}")
        else:
            paths.add(path_value)
        if not isinstance(component["commit"], str) or not HEX40.fullmatch(component["commit"]):
            errors.append(f"{where}: invalid commit")
        if not isinstance(component["release_tag"], str) or not component["release_tag"]:
            errors.append(f"{where}: invalid release_tag")

        kind = component["kind"]
        if kind == "bluemap":
            blue_count += 1
            if component_id != "bluemap" or path_value != "bluemap" or component["requires"] != []:
                errors.append(f"{where}: malformed BlueMap component")
        elif kind == "addon":
            if path_value != f"addons/{component_id}":
                errors.append(f"{where}: add-on path must be addons/{component_id}")
            if component["requires"] != ["bluemap"]:
                errors.append(f"{where}: add-on requires must be ['bluemap']")
        else:
            errors.append(f"{where}: kind must be bluemap or addon")

        artifact = component["artifact"]
        if not exact_keys(
            errors,
            f"{where}: artifact",
            artifact,
            {"filename", "url", "size_bytes", "sha256"},
        ):
            continue
        filename = artifact["filename"]
        if (
            not isinstance(filename, str)
            or not filename.endswith(".jar")
            or "/" in filename
            or filename in {".jar", "..jar"}
        ):
            errors.append(f"{where}: invalid artifact filename")
        elif filename in filenames:
            errors.append(f"{where}: duplicate artifact filename {filename}")
        else:
            filenames.add(filename)
        expected_url = (
            f"https://github.com/{repository}/releases/download/"
            f"{component['release_tag']}/{filename}"
        )
        if artifact["url"] != expected_url:
            errors.append(f"{where}: artifact URL is not the exact repository/tag/filename URL")
        if not integer(artifact["size_bytes"], 1):
            errors.append(f"{where}: artifact size_bytes must be positive")
        if not isinstance(artifact["sha256"], str) or not HEX64.fullmatch(artifact["sha256"]):
            errors.append(f"{where}: invalid artifact sha256")

    if ids != sorted(ids):
        errors.append(f"{rel}: components must be sorted by id")
    if len(ids) != len(set(ids)):
        errors.append(f"{rel}: component ids must be unique")
    if blue_count != 1:
        errors.append(f"{rel}: exactly one BlueMap component is required")
    addon_count = sum(
        1
        for component in components
        if isinstance(component, dict) and component.get("kind") == "addon"
    )
    if isinstance(release, dict):
        if release.get("component_count") != len(components):
            errors.append(f"{rel}: release.component_count is incorrect")
        if release.get("addon_count") != addon_count:
            errors.append(f"{rel}: release.addon_count is incorrect")
    return errors, data


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def validate_tooling_manifest(path: Path) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    rel = path.relative_to(ROOT)
    try:
        data = load_json(path)
    except ValueError as exc:
        return [str(exc)], None
    if not exact_keys(errors, str(rel), data, {"schema_version", "components"}):
        return errors, data
    if not integer(data["schema_version"], 1) or data["schema_version"] != 1:
        errors.append(f"{rel}: schema_version must be 1")
    components = data["components"]
    if not isinstance(components, list) or not components:
        errors.append(f"{rel}: components must be a non-empty array")
        return errors, data

    ids: list[str] = []
    repositories: set[str] = set()
    paths: set[str] = set()
    filenames: set[str] = set()
    for index, component in enumerate(components):
        where = f"{rel}: components[{index}]"
        if not exact_keys(
            errors,
            where,
            component,
            {
                "id",
                "kind",
                "repository",
                "submodule_path",
                "commit",
                "release_tag",
                "artifact",
            },
        ):
            continue
        component_id = component["id"]
        repository = component["repository"]
        path_value = component["submodule_path"]
        if not isinstance(component_id, str) or not ID.fullmatch(component_id):
            errors.append(f"{where}: invalid id")
        else:
            ids.append(component_id)
        if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
            errors.append(f"{where}: invalid repository")
        elif repository in repositories:
            errors.append(f"{where}: duplicate repository {repository}")
        else:
            repositories.add(repository)
        if (
            not isinstance(path_value, str)
            or not ID.fullmatch(path_value)
            or path_value in {"addons", "bluemap"}
        ):
            errors.append(f"{where}: invalid development-tool submodule_path")
        elif path_value in paths:
            errors.append(f"{where}: duplicate submodule_path {path_value}")
        else:
            paths.add(path_value)
        if component["kind"] != "development-tool":
            errors.append(f"{where}: kind must be development-tool")
        if not isinstance(component["commit"], str) or not HEX40.fullmatch(component["commit"]):
            errors.append(f"{where}: invalid commit")
        if not isinstance(component["release_tag"], str) or not component["release_tag"]:
            errors.append(f"{where}: invalid release_tag")

        artifact = component["artifact"]
        if not exact_keys(
            errors,
            f"{where}: artifact",
            artifact,
            {"filename", "url", "size_bytes", "sha256"},
        ):
            continue
        filename = artifact["filename"]
        if (
            not isinstance(filename, str)
            or not filename.endswith(".whl")
            or "/" in filename
            or filename in {".whl", "..whl"}
            or filename in filenames
        ):
            errors.append(f"{where}: invalid or duplicate artifact filename")
        else:
            filenames.add(filename)
        expected_url = (
            f"https://github.com/{repository}/releases/download/"
            f"{component['release_tag']}/{filename}"
        )
        if artifact["url"] != expected_url:
            errors.append(f"{where}: artifact URL is not the exact repository/tag/filename URL")
        if not integer(artifact["size_bytes"], 1):
            errors.append(f"{where}: artifact size_bytes must be positive")
        if not isinstance(artifact["sha256"], str) or not HEX64.fullmatch(artifact["sha256"]):
            errors.append(f"{where}: invalid artifact sha256")

    if ids != sorted(ids):
        errors.append(f"{rel}: components must be sorted by id")
    if len(ids) != len(set(ids)):
        errors.append(f"{rel}: component ids must be unique")
    return errors, data


def validate_submodules(
    components: list[dict[str, Any]],
    tooling_components: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    modules_file = ROOT / ".gitmodules"
    if not modules_file.is_file():
        return [".gitmodules is missing"]

    expected = {
        component["submodule_path"]: {
            "url": f"https://github.com/{component['repository']}.git",
            "commit": component["commit"],
        }
        for component in components + tooling_components
    }
    try:
        path_lines = git_output(
            "config", "-f", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"
        ).splitlines()
        url_lines = git_output(
            "config", "-f", ".gitmodules", "--get-regexp", r"^submodule\..*\.url$"
        ).splitlines()
    except RuntimeError as exc:
        return [str(exc)]

    names_to_paths = {
        key.removeprefix("submodule.").removesuffix(".path"): value
        for key, value in (line.split(maxsplit=1) for line in path_lines)
    }
    names_to_urls = {
        key.removeprefix("submodule.").removesuffix(".url"): value
        for key, value in (line.split(maxsplit=1) for line in url_lines)
    }
    actual_paths = set(names_to_paths.values())
    if actual_paths != set(expected):
        errors.append(
            ".gitmodules paths differ; "
            f"missing={sorted(set(expected) - actual_paths)}, "
            f"unexpected={sorted(actual_paths - set(expected))}"
        )
    for name, path_value in names_to_paths.items():
        if name not in names_to_urls:
            errors.append(f".gitmodules: {name} has no URL")
        elif path_value in expected and names_to_urls[name] != expected[path_value]["url"]:
            errors.append(f".gitmodules: wrong URL for {path_value}")
    if set(names_to_urls) != set(names_to_paths):
        errors.append(".gitmodules: path and URL entries do not have identical names")

    try:
        stage_lines = git_output("ls-files", "--stage").splitlines()
    except RuntimeError as exc:
        return errors + [str(exc)]
    gitlinks: dict[str, str] = {}
    tracked_jars: list[str] = []
    for line in stage_lines:
        metadata, path_value = line.split("\t", 1)
        mode, object_id, _stage = metadata.split()
        if mode == "160000":
            gitlinks[path_value] = object_id
        if path_value.endswith(".jar"):
            expected_digest = ALLOWED_TRACKED_JARS.get(path_value)
            if expected_digest is None:
                tracked_jars.append(path_value)
            else:
                blob = subprocess.run(
                    ["git", "cat-file", "blob", object_id],
                    cwd=ROOT,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if blob.returncode:
                    errors.append(
                        f"cannot read tracked JAR {path_value}: "
                        f"{blob.stderr.decode(errors='replace').strip()}"
                    )
                else:
                    actual_digest = hashlib.sha256(blob.stdout).hexdigest()
                    if actual_digest != expected_digest:
                        errors.append(
                            f"tracked JAR {path_value}: expected SHA-256 "
                            f"{expected_digest}, got {actual_digest}"
                        )
    if set(gitlinks) != set(expected):
        errors.append(
            "gitlinks differ; "
            f"missing={sorted(set(expected) - set(gitlinks))}, "
            f"unexpected={sorted(set(gitlinks) - set(expected))}"
        )
    for path_value, object_id in gitlinks.items():
        if path_value in expected and object_id != expected[path_value]["commit"]:
            errors.append(f"gitlink {path_value}: expected {expected[path_value]['commit']}, got {object_id}")
    if tracked_jars:
        errors.append(f"repository tracks JARs: {tracked_jars}")
    return errors


def remote_check(component: dict[str, Any]) -> str | None:
    repository = component["repository"]
    tag = component["release_tag"]
    expected_commit = component["commit"]
    remote = f"https://github.com/{repository}.git"
    result = subprocess.run(
        ["git", "ls-remote", "--tags", remote, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if result.returncode:
        return f"{component['id']}: git ls-remote failed: {result.stderr.strip()}"
    refs = {}
    for line in result.stdout.splitlines():
        object_id, ref = line.split("\t", 1)
        refs[ref] = object_id
    peeled = refs.get(f"refs/tags/{tag}^{{}}")
    if peeled is None:
        return f"{component['id']}: release tag is missing or not annotated"
    if peeled != expected_commit:
        return f"{component['id']}: tag peels to {peeled}, expected {expected_commit}"

    artifact = component["artifact"]
    digest = hashlib.sha256()
    total = 0
    request = urllib.request.Request(
        artifact["url"], headers={"User-Agent": "bluemap-atmons-validator/1"}
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                total += len(chunk)
    except Exception as exc:  # network failures need a concise component identity
        return f"{component['id']}: artifact download failed: {exc}"
    if total != artifact["size_bytes"]:
        return f"{component['id']}: artifact size {total}, expected {artifact['size_bytes']}"
    if digest.hexdigest() != artifact["sha256"]:
        return f"{component['id']}: artifact SHA-256 mismatch"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        help="validate gitlinks and, with --remote, releases for this exact ATMons version",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="verify annotated tag targets and download/hash every release artifact",
    )
    args = parser.parse_args()

    errors: list[str] = []
    schema = ROOT / "schema/version-manifest.schema.json"
    try:
        load_json(schema)
    except ValueError as exc:
        errors.append(str(exc))

    candidate_paths = list((ROOT / "versions").glob("*/manifest.json"))
    invalid_version_paths = [
        path for path in candidate_paths if not VERSION.fullmatch(path.parent.name)
    ]
    for path in invalid_version_paths:
        errors.append(f"invalid version directory: {path.parent.name}")
    paths = sorted(
        (path for path in candidate_paths if path not in invalid_version_paths),
        key=lambda path: tuple(int(part) for part in path.parent.name.split(".")),
    )
    if not paths:
        errors.append("no version manifests found")
    manifests: list[dict[str, Any]] = []
    versions: set[str] = set()
    for path in paths:
        manifest_errors, data = validate_manifest(path)
        errors.extend(manifest_errors)
        if data is not None and not manifest_errors:
            version = data["atmons"]["version"]
            if version in versions:
                errors.append(f"duplicate version manifest: {version}")
            versions.add(version)
            manifests.append(data)

    tooling_errors, tooling = validate_tooling_manifest(ROOT / "tooling" / "manifest.json")
    errors.extend(tooling_errors)
    tooling_components: list[dict[str, Any]] = []
    if tooling is not None and not tooling_errors:
        tooling_components = tooling["components"]

    selected: dict[str, Any] | None = None
    if manifests:
        if args.version:
            selected = next(
                (
                    manifest
                    for manifest in manifests
                    if manifest["atmons"]["version"] == args.version
                ),
                None,
            )
            if selected is None:
                errors.append(f"no manifest exists for requested version {args.version}")
        else:
            selected = manifests[-1]
        if selected is not None and not tooling_errors:
            errors.extend(validate_submodules(selected["components"], tooling_components))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.remote:
        remote_manifests = [selected] if args.version and selected is not None else manifests
        components = [
            component
            for manifest in remote_manifests
            for component in manifest["components"]
        ] + tooling_components
        print(f"Remote-auditing {len(components)} component releases ...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            failures = [failure for failure in executor.map(remote_check, components) if failure]
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}", file=sys.stderr)
            return 1

    counts = [manifest["release"]["component_count"] for manifest in manifests]
    print(
        f"Validated {len(manifests)} compatibility manifest(s), "
        f"{sum(counts)} installed component record(s), "
        f"{len(tooling_components)} development tool(s), and the current pinned submodule set."
    )
    if args.remote:
        print("All annotated tag targets and release asset identities match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
