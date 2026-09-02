#!/usr/bin/env python3
"""Run every manifest-pinned BlueMap add-on's safe child-project gates.

The suite is deliberately sequential.  It performs a global clean/pin
preflight before executing anything and rechecks each child repository after
every command.  Build output may be generated in ignored directories, but a
tracked or untracked Git status change, child HEAD movement, or meta-repository
gitlink movement fails the suite and stops that child's remaining commands.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator, Mapping, Sequence


SCHEMA_VERSION = 1
RUNNER_VERSION = "1.3.0"
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
GALLERY_TEST_RE = re.compile(r"^gallery/(?:.*/)?test_[^/]+\.py$")
ADDON_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
GRADLE_ARTIFACT_PROPERTY_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*Jar")
ATMONS_1_2_0_MANIFEST_SHA256 = "f118552f76a334d7f00ac85fcb2e30a0394f438c20492fe5c5a149e2f3093df3"
ATMONS_1_2_0_VALIDATOR_SHA256 = "10ac46a5f99bfa440dae6b15ab2cad3432e0a3acadf4c2b204597b30ae8a46b7"


class GateError(RuntimeError):
    """Raised for invalid suite input or an unsafe invocation."""


@dataclasses.dataclass(frozen=True)
class Component:
    identifier: str
    submodule_path: str
    commit: str


@dataclasses.dataclass(frozen=True)
class CommandSpec:
    identifier: str
    description: str
    argv: tuple[str, ...]
    display_argv: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class GradleArtifact:
    property_name: str
    path: Path
    size_bytes: int
    sha256: str


@dataclasses.dataclass(frozen=True)
class GalleryArtifactDirectory:
    path: Path
    file_count: int
    size_bytes: int
    sha256: str
    files: tuple[tuple[str, int, str], ...]


@dataclasses.dataclass(frozen=True)
class ComponentPlan:
    component: Component
    repository: Path
    tracked_paths: tuple[str, ...]
    commands: tuple[CommandSpec, ...]
    discovery_warnings: tuple[str, ...]
    gradle_artifacts: tuple[GradleArtifact, ...] = ()
    gallery_artifact: GalleryArtifactDirectory | None = None


def run_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
    timeout: float | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env=environment,
        check=False,
    )


def git(repo: Path, *args: str) -> str:
    result = run_process(("git", "-C", str(repo), *args), cwd=repo)
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace").strip()
        raise GateError(f"git {' '.join(args)} failed in {repo}: {output}")
    return result.stdout.decode("utf-8", errors="strict").strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise GateError(f"cannot read {path}: {exc}") from exc


def git_index_file_bytes(root: Path, relative_path: str) -> bytes:
    result = run_process(
        ("git", "-C", str(root), "show", f":{relative_path}"),
        cwd=root,
    )
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace").strip()
        raise GateError(f"cannot read tracked index blob {relative_path}: {output}")
    return result.stdout


def validate_manifest_selection(
    root: Path,
    requested_path: Path,
    requested_version: str,
) -> dict[str, object]:
    """Bind a run to the validated, byte-exact tracked version manifest."""

    canonical_path = (root / "versions" / requested_version / "manifest.json").resolve()
    requested_path = requested_path.resolve()
    if not requested_path.is_relative_to(root):
        raise GateError("manifest must remain inside the BlueMap ATMons repository")
    if not canonical_path.is_relative_to(root):
        raise GateError("requested version resolves outside the BlueMap ATMons repository")

    canonical_relative = canonical_path.relative_to(root).as_posix()
    requested_relative = requested_path.relative_to(root).as_posix()
    try:
        requested_bytes = requested_path.read_bytes()
        canonical_bytes = canonical_path.read_bytes()
    except OSError as exc:
        raise GateError(f"cannot read selected manifest: {exc}") from exc
    index_bytes = git_index_file_bytes(root, canonical_relative)
    if canonical_bytes != index_bytes:
        raise GateError(
            f"canonical manifest {canonical_relative} differs byte-for-byte from its tracked index blob"
        )
    if requested_bytes != canonical_bytes:
        raise GateError(
            "manifest override differs byte-for-byte from the tracked canonical manifest "
            f"{canonical_relative}"
        )

    try:
        manifest = json.loads(requested_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot decode selected manifest: {exc}") from exc
    manifest_version = (
        manifest.get("atmons", {}).get("version")
        if isinstance(manifest, dict) and isinstance(manifest.get("atmons"), dict)
        else None
    )
    if manifest_version != requested_version:
        raise GateError(
            f"selected manifest declares ATMons {manifest_version!r}, requested {requested_version!r}"
        )

    validator_relative = "tools/validate.py"
    validator_path = root / validator_relative
    try:
        validator_bytes = validator_path.read_bytes()
    except OSError as exc:
        raise GateError(f"cannot read shared manifest validator: {exc}") from exc
    validator_index_bytes = git_index_file_bytes(root, validator_relative)
    if validator_bytes != validator_index_bytes:
        raise GateError("shared manifest validator differs byte-for-byte from its tracked index blob")
    if requested_version == "1.2.0":
        if sha256_bytes(canonical_bytes) != ATMONS_1_2_0_MANIFEST_SHA256:
            raise GateError(
                "canonical ATMons 1.2.0 manifest differs from its immutable released-profile digest"
            )
        if sha256_bytes(validator_bytes) != ATMONS_1_2_0_VALIDATOR_SHA256:
            raise GateError(
                "shared manifest validator differs from its reviewed immutable digest"
            )
    validation = run_process(
        (sys.executable, validator_relative, "--version", requested_version),
        cwd=root,
        environment=suite_environment(),
    )
    validator_output = sanitized_output(validation.stdout, root, 40)
    if validation.returncode != 0:
        raise GateError(
            "shared manifest validator rejected the selected version"
            + (f": {validator_output}" if validator_output else "")
        )

    manifest_sha256 = sha256_bytes(canonical_bytes)
    return {
        "ok": True,
        "requested_version": requested_version,
        "declared_atmons_version": manifest_version,
        "requested_path": requested_relative,
        "canonical_path": canonical_relative,
        "sha256": manifest_sha256,
        "requested_matches_canonical": True,
        "canonical_matches_tracked_index": True,
        "shared_validator": {
            "path": validator_relative,
            "sha256": sha256_bytes(validator_bytes),
            "matches_tracked_index": True,
            "exit_code": validation.returncode,
            "output_tail": validator_output,
        },
    }


def attest_gallery_artifact_directory(path: Path) -> GalleryArtifactDirectory:
    """Hash every regular input file in a gallery artifact directory."""

    path = path.resolve()
    if not path.is_dir():
        raise GateError(f"gallery artifact directory is missing: {path}")
    files: list[tuple[str, int, str]] = []
    try:
        entries = sorted(path.rglob("*"), key=lambda entry: entry.relative_to(path).as_posix())
        for entry in entries:
            relative = entry.relative_to(path).as_posix()
            if entry.is_symlink():
                raise GateError(f"gallery artifact directory contains a symlink: {relative}")
            if entry.is_dir():
                continue
            if not entry.is_file():
                raise GateError(f"gallery artifact directory contains a non-regular entry: {relative}")
            size_bytes = entry.stat().st_size
            files.append((relative, size_bytes, sha256_file(entry)))
    except OSError as exc:
        raise GateError(f"cannot attest gallery artifact directory {path}: {exc}") from exc
    if not files:
        raise GateError(f"gallery artifact directory is empty: {path}")
    tree_payload = json.dumps(files, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return GalleryArtifactDirectory(
        path=path,
        file_count=len(files),
        size_bytes=sum(size for _relative, size, _digest in files),
        sha256=sha256_bytes(tree_payload),
        files=tuple(files),
    )


def external_input_state(plan: ComponentPlan) -> dict[str, object]:
    """Rehash every external input without exposing its local path."""

    gradle_records: list[dict[str, object]] = []
    for artifact in plan.gradle_artifacts:
        record: dict[str, object] = {
            "property": artifact.property_name,
            "filename": artifact.path.name,
            "expected_size_bytes": artifact.size_bytes,
            "expected_sha256": artifact.sha256,
            "observed_size_bytes": None,
            "observed_sha256": None,
            "ok": False,
            "error": None,
        }
        try:
            if artifact.path.is_symlink() or not artifact.path.is_file():
                raise GateError("input is not a regular non-symlink file")
            observed_size = artifact.path.stat().st_size
            observed_sha256 = sha256_file(artifact.path)
            record.update(
                {
                    "observed_size_bytes": observed_size,
                    "observed_sha256": observed_sha256,
                    "ok": (
                        observed_size == artifact.size_bytes
                        and observed_sha256 == artifact.sha256
                    ),
                }
            )
            if not record["ok"]:
                record["error"] = "external Gradle artifact identity changed"
        except (GateError, OSError) as exc:
            record["error"] = str(exc)
        gradle_records.append(record)

    gallery_record: dict[str, object] | None = None
    gallery = plan.gallery_artifact
    if gallery is not None:
        gallery_record = {
            "expected_file_count": gallery.file_count,
            "expected_size_bytes": gallery.size_bytes,
            "expected_sha256": gallery.sha256,
            "observed_file_count": None,
            "observed_size_bytes": None,
            "observed_sha256": None,
            "ok": False,
            "error": None,
        }
        try:
            observed = attest_gallery_artifact_directory(gallery.path)
            gallery_record.update(
                {
                    "observed_file_count": observed.file_count,
                    "observed_size_bytes": observed.size_bytes,
                    "observed_sha256": observed.sha256,
                    "ok": observed == gallery,
                }
            )
            if not gallery_record["ok"]:
                gallery_record["error"] = "gallery artifact directory identity changed"
        except GateError as exc:
            gallery_record["error"] = str(exc).replace(str(gallery.path), "<gallery-artifacts>")

    return {
        "mode": "byte-exact-before-and-after-each-command",
        "gradle_artifacts": gradle_records,
        "gallery_artifact_directory": gallery_record,
        "ok": all(record["ok"] for record in gradle_records)
        and (gallery_record is None or bool(gallery_record["ok"])),
    }


def load_manifest(path: Path, expected_addons: int) -> tuple[dict[str, object], tuple[Component, ...]]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise GateError("manifest must be a schema-1 object")
    components_value = manifest.get("components")
    if not isinstance(components_value, list):
        raise GateError("manifest components must be an array")

    components: list[Component] = []
    for value in components_value:
        if not isinstance(value, dict) or value.get("kind") != "addon":
            continue
        identifier = value.get("id")
        submodule_path = value.get("submodule_path")
        commit = value.get("commit")
        if not all(isinstance(item, str) for item in (identifier, submodule_path, commit)):
            raise GateError("each add-on component needs string id, submodule_path, and commit fields")
        path = PurePosixPath(submodule_path)
        if path.is_absolute() or ".." in path.parts or len(path.parts) != 2 or path.parts[0] != "addons":
            raise GateError(f"unsafe add-on submodule path: {submodule_path}")
        if not COMMIT_RE.fullmatch(commit):
            raise GateError(f"add-on {identifier} has a non-full commit: {commit}")
        components.append(Component(identifier, submodule_path, commit))

    components.sort(key=lambda component: component.identifier)
    identifiers = [component.identifier for component in components]
    paths = [component.submodule_path for component in components]
    if len(identifiers) != len(set(identifiers)) or len(paths) != len(set(paths)):
        raise GateError("manifest add-on ids and submodule paths must be unique")
    if len(components) != expected_addons:
        raise GateError(f"expected {expected_addons} manifest add-ons, found {len(components)}")
    release_count = manifest.get("release", {}).get("addon_count") if isinstance(manifest.get("release"), dict) else None
    if release_count != len(components):
        raise GateError(f"manifest release.addon_count is {release_count!r}, expected {len(components)}")
    return manifest, tuple(components)


def root_gitlink_commit(root: Path, submodule_path: str) -> str | None:
    output = git(root, "ls-files", "--stage", "--", submodule_path)
    records = [line for line in output.splitlines() if line]
    if len(records) != 1:
        return None
    match = re.fullmatch(r"160000 ([0-9a-f]{40}) 0\t(.+)", records[0])
    if match is None or match.group(2) != submodule_path:
        return None
    return match.group(1)


def tracked_paths_at(repository: Path, commit: str) -> tuple[str, ...]:
    output = git(repository, "ls-tree", "-r", "--name-only", commit)
    return tuple(sorted(line for line in output.splitlines() if line))


def pinned_file_text(repository: Path, commit: str, path: str) -> str:
    result = run_process(("git", "-C", str(repository), "show", f"{commit}:{path}"), cwd=repository)
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace").strip()
        raise GateError(f"cannot read pinned {path} in {repository}@{commit}: {output}")
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"pinned script is not UTF-8: {repository}/{path}") from exc


def ignored_status_paths(repository: Path) -> tuple[str, ...]:
    result = run_process(
        (
            "git",
            "-C",
            str(repository),
            "status",
            "--porcelain=v1",
            "-z",
            "--ignored=matching",
            "--untracked-files=normal",
        ),
        cwd=repository,
    )
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace").strip()
        raise GateError(f"cannot inspect ignored inputs in {repository}: {output}")
    try:
        records = result.stdout.decode("utf-8").split("\0")
    except UnicodeDecodeError as exc:
        raise GateError(f"repository has a non-UTF-8 ignored path: {repository}") from exc
    return tuple(sorted(record[3:] for record in records if record.startswith("!! ")))


def is_allowed_ignored_output(path: str, *, bluemap: bool) -> bool:
    normalized = path.rstrip("/")
    parts = PurePosixPath(normalized).parts
    if not parts or ".." in parts:
        return False
    if bluemap:
        if any(part in {".gradle", "build"} for part in parts):
            return True
        return normalized == (
            "core/src/main/resources/de/bluecolored/bluemap/resourceExtensions.zip"
        )
    return parts[0] in {".gradle", "build"}


def source_input_attestation(repository: Path, *, bluemap: bool) -> dict[str, object]:
    """Attest all Git-visible inputs, allowing only bounded generated outputs."""

    status = git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    ignored = ignored_status_paths(repository)
    allowed = tuple(path for path in ignored if is_allowed_ignored_output(path, bluemap=bluemap))
    unexpected = tuple(path for path in ignored if path not in allowed)
    return {
        "mode": "tracked-head-plus-bounded-ignored-output-roots",
        "non_ignored_status_porcelain": status,
        "non_ignored_status_clean": not status,
        "ignored_entry_count": len(ignored),
        "allowed_ignored_output_entries": list(allowed),
        "unexpected_ignored_entries": list(unexpected),
        "ok": not status and not unexpected,
    }


def nested_gitlink_commit(repository: Path, commit: str, path: str) -> str | None:
    output = git(repository, "ls-tree", commit, "--", path)
    records = [line for line in output.splitlines() if line]
    if len(records) != 1:
        return None
    match = re.fullmatch(r"160000 commit ([0-9a-f]{40})\t(.+)", records[0])
    if match is None or match.group(2) != path:
        return None
    return match.group(1)


def repository_state(root: Path, component: Component) -> dict[str, object]:
    repository = root / component.submodule_path
    state: dict[str, object] = {
        "expected_commit": component.commit,
        "gitlink_commit": None,
        "head_commit": None,
        "status_porcelain": None,
        "source_input_attestation": None,
        "pin_ok": False,
        "clean": False,
        "ok": False,
        "errors": [],
    }
    errors: list[str] = state["errors"]  # type: ignore[assignment]
    if not repository.is_dir():
        errors.append("submodule worktree is missing")
        return state
    try:
        gitlink = root_gitlink_commit(root, component.submodule_path)
        state["gitlink_commit"] = gitlink
        if gitlink != component.commit:
            errors.append(f"root gitlink is {gitlink or 'missing'}, expected {component.commit}")
        head = git(repository, "rev-parse", "HEAD")
        state["head_commit"] = head
        if head != component.commit:
            errors.append(f"child HEAD is {head}, expected {component.commit}")
        attestation = source_input_attestation(repository, bluemap=False)
        status = str(attestation["non_ignored_status_porcelain"])
        state["status_porcelain"] = status
        state["source_input_attestation"] = attestation
        if not attestation["ok"]:
            errors.append("child source inputs are not clean and bounded")
        state["pin_ok"] = gitlink == component.commit and head == component.commit
        state["clean"] = attestation["ok"]
        state["ok"] = bool(state["pin_ok"] and state["clean"])
    except GateError as exc:
        errors.append(str(exc))
    return state


def bluemap_source_state(
    root: Path,
    repository: Path,
    *,
    expected_commit: str,
    require_gitlink_match: bool,
) -> dict[str, object]:
    repository = repository.resolve()
    is_meta_submodule = repository == (root / "bluemap").resolve()
    state: dict[str, object] = {
        "source": "<repo>/bluemap" if is_meta_submodule else "<external-bluemap-source>",
        "is_meta_submodule": is_meta_submodule,
        "gitlink_commit": None,
        "expected_commit": expected_commit,
        "head_commit": None,
        "branch": None,
        "status_porcelain": None,
        "source_input_attestation": None,
        "api": None,
        "head_matches_expected": False,
        "gitlink_matches_head": False,
        "pin_ok": False,
        "clean": False,
        "ok": False,
        "errors": [],
    }
    errors: list[str] = state["errors"]  # type: ignore[assignment]
    if not repository.is_dir():
        errors.append("BlueMap source submodule worktree is missing")
        return state
    try:
        gitlink = root_gitlink_commit(root, "bluemap") if is_meta_submodule else None
        head = git(repository, "rev-parse", "HEAD")
        branch = git(repository, "branch", "--show-current")
        attestation = source_input_attestation(repository, bluemap=True)
        status = str(attestation["non_ignored_status_porcelain"])
        expected_api_commit = nested_gitlink_commit(repository, head, "api")
        api_repository = repository / "api"
        api_state: dict[str, object] = {
            "expected_commit": expected_api_commit,
            "head_commit": None,
            "source_input_attestation": None,
            "ok": False,
        }
        if expected_api_commit is None:
            errors.append("BlueMap source commit has no pinned api gitlink")
        elif not api_repository.is_dir():
            errors.append("BlueMap api submodule worktree is missing")
        else:
            api_head = git(api_repository, "rev-parse", "HEAD")
            api_attestation = source_input_attestation(api_repository, bluemap=True)
            api_state.update(
                {
                    "head_commit": api_head,
                    "source_input_attestation": api_attestation,
                    "ok": api_head == expected_api_commit and api_attestation["ok"],
                }
            )
            if api_head != expected_api_commit:
                errors.append(
                    f"BlueMap api HEAD is {api_head}, expected nested gitlink {expected_api_commit}"
                )
            if not api_attestation["ok"]:
                errors.append("BlueMap api source inputs are not clean and bounded")
        state.update(
            {
                "gitlink_commit": gitlink,
                "head_commit": head,
                "branch": branch or None,
                "status_porcelain": status,
                "source_input_attestation": attestation,
                "api": api_state,
                "head_matches_expected": head == expected_commit,
                "gitlink_matches_head": gitlink == head if is_meta_submodule else False,
                "pin_ok": head == expected_commit,
                "clean": bool(attestation["ok"] and api_state["ok"]),
            }
        )
        if head != expected_commit:
            errors.append(f"BlueMap child HEAD is {head}, expected integration commit {expected_commit}")
        if is_meta_submodule and require_gitlink_match and gitlink != head:
            errors.append(f"BlueMap child HEAD is {head}, root gitlink is {gitlink or 'missing'}")
        if not attestation["ok"]:
            errors.append("BlueMap source inputs are not clean and bounded")
        gitlink_ok = not (is_meta_submodule and require_gitlink_match) or gitlink == head
        state["ok"] = bool(state["pin_ok"] and state["clean"] and gitlink_ok and COMMIT_RE.fullmatch(head))
    except GateError as exc:
        errors.append(str(exc))
    return state


def discover_commands(
    root: Path,
    component: Component,
    *,
    bluemap_source: Path,
    gallery_artifact_dirs: dict[str, Path],
    gradle_artifacts: Mapping[str, GradleArtifact],
    python_command: str,
    gradle_command: str,
) -> ComponentPlan:
    repository = root / component.submodule_path
    tracked = tracked_paths_at(repository, component.commit)
    tracked_set = set(tracked)
    commands: list[CommandSpec] = []
    warnings: list[str] = []

    generator = "gallery/generate.py"
    if generator in tracked_set:
        generator_source = pinned_file_text(repository, component.commit, generator)
        if "--check" not in generator_source:
            raise GateError(f"{component.identifier}: tracked gallery generator has no explicit --check mode")
        generator_arguments: tuple[str, ...] = ()
        generator_display: tuple[str, ...] = ()
        if "--artifact-dir" in generator_source:
            artifact_dir = gallery_artifact_dirs.get(component.identifier)
            if artifact_dir is None:
                raise GateError(
                    f"{component.identifier}: gallery generator requires --artifact-dir; "
                    f"supply --gallery-artifact-dir {component.identifier}=PATH"
                )
            if not artifact_dir.is_dir():
                raise GateError(f"{component.identifier}: gallery artifact directory is missing: {artifact_dir}")
            generator_arguments = ("--artifact-dir", str(artifact_dir))
            generator_display = ("--artifact-dir", f"<gallery-artifacts:{component.identifier}>")
        commands.append(
            CommandSpec(
                "gallery-generate-check",
                "verify checked-in gallery output is byte-current",
                (python_command, generator, *generator_arguments, "--check"),
                ("<python>", generator, *generator_display, "--check"),
            )
        )

    lint = "gallery/lint.py"
    if lint in tracked_set:
        lint_source = pinned_file_text(repository, component.commit, lint)
        lint_arguments: tuple[str, ...] = ()
        lint_display: tuple[str, ...] = ()
        if "--artifact-dir" in lint_source:
            artifact_dir = gallery_artifact_dirs.get(component.identifier)
            if artifact_dir is None:
                raise GateError(
                    f"{component.identifier}: gallery lint requires --artifact-dir; "
                    f"supply --gallery-artifact-dir {component.identifier}=PATH"
                )
            lint_arguments = ("--artifact-dir", str(artifact_dir))
            lint_display = ("--artifact-dir", f"<gallery-artifacts:{component.identifier}>")
        commands.append(
            CommandSpec(
                "gallery-lint",
                "run the gallery's non-mutating lint contract",
                (python_command, lint, *lint_arguments),
                ("<python>", lint, *lint_display),
            )
        )

    gallery_tests = sorted(path for path in tracked if GALLERY_TEST_RE.fullmatch(path))
    for index, test_path in enumerate(gallery_tests, start=1):
        commands.append(
            CommandSpec(
                f"gallery-test-{index:02d}",
                f"run tracked gallery test {test_path}",
                (python_command, test_path),
                ("<python>", test_path),
            )
        )

    if "build.gradle" not in tracked_set and "build.gradle.kts" not in tracked_set:
        raise GateError(f"{component.identifier}: no tracked Gradle build file")
    build_path = "build.gradle" if "build.gradle" in tracked_set else "build.gradle.kts"
    build_source = pinned_file_text(repository, component.commit, build_path)
    ordered_gradle_artifacts = tuple(
        gradle_artifacts[name] for name in sorted(gradle_artifacts)
    )
    for artifact in ordered_gradle_artifacts:
        property_literals = (
            f"gradleProperty('{artifact.property_name}')",
            f'gradleProperty("{artifact.property_name}")',
        )
        dynamic_property_literals = (
            f"'{artifact.property_name}'",
            f'"{artifact.property_name}"',
        )
        declared = any(literal in build_source for literal in property_literals) or (
            "providers.gradleProperty" in build_source
            and any(literal in build_source for literal in dynamic_property_literals)
        )
        if not declared:
            raise GateError(
                f"{component.identifier}: --gradle-artifact property "
                f"{artifact.property_name!r} is not declared in pinned {build_path}"
            )
    if "gradlew" in tracked_set:
        gradle_argv = ("./gradlew",)
        gradle_display = ("./gradlew",)
    else:
        gradle_argv = (gradle_command,)
        gradle_display = ("<gradle>",)
    source_argument = f"-PbluemapSourcePath={bluemap_source}"
    source_display = "-PbluemapSourcePath=<bluemap-source>"
    artifact_arguments = tuple(
        f"-P{artifact.property_name}={artifact.path}"
        for artifact in ordered_gradle_artifacts
    )
    artifact_display = tuple(
        f"-P{artifact.property_name}=<artifact:{component.identifier}:{artifact.property_name}>"
        for artifact in ordered_gradle_artifacts
    )
    commands.extend(
        (
            CommandSpec(
                "gradle-clean-check-build",
                "run the common clean/check/build gate",
                (
                    *gradle_argv,
                    "--no-daemon",
                    source_argument,
                    *artifact_arguments,
                    "clean",
                    "check",
                    "build",
                ),
                (
                    *gradle_display,
                    "--no-daemon",
                    source_display,
                    *artifact_display,
                    "clean",
                    "check",
                    "build",
                ),
            ),
            CommandSpec(
                "gradle-generate-pom",
                "generate the add-on Maven publication POM",
                (
                    *gradle_argv,
                    "--no-daemon",
                    source_argument,
                    *artifact_arguments,
                    "generatePomFileForAddonPublication",
                ),
                (
                    *gradle_display,
                    "--no-daemon",
                    source_display,
                    *artifact_display,
                    "generatePomFileForAddonPublication",
                ),
            ),
        )
    )
    if not gallery_tests:
        warnings.append("no tracked gallery test_*.py files discovered")
    if generator not in tracked_set and lint not in tracked_set:
        warnings.append("no tracked gallery generator/lint scripts discovered")
    return ComponentPlan(
        component,
        repository,
        tracked,
        tuple(commands),
        tuple(warnings),
        ordered_gradle_artifacts,
    )


def plan_record(plan: ComponentPlan, preflight: dict[str, object]) -> dict[str, object]:
    return {
        "id": plan.component.identifier,
        "submodule_path": plan.component.submodule_path,
        "expected_commit": plan.component.commit,
        "preflight": preflight,
        "discovery_warnings": list(plan.discovery_warnings),
        "commands": [
            {
                "id": command.identifier,
                "description": command.description,
                "argv": list(command.display_argv),
                "status": "planned",
            }
            for command in plan.commands
        ],
    }


def build_plan(
    root: Path,
    manifest_path: Path,
    *,
    expected_addons: int,
    bluemap_source: Path,
    expected_bluemap_commit: str | None = None,
    manifest_validation: dict[str, object] | None = None,
    gallery_artifact_dirs: dict[str, Path] | None = None,
    gradle_artifacts: dict[str, dict[str, GradleArtifact]] | None = None,
    python_command: str,
    gradle_command: str,
) -> tuple[dict[str, object], tuple[ComponentPlan, ...]]:
    manifest, components = load_manifest(manifest_path, expected_addons)
    artifact_dirs = gallery_artifact_dirs or {}
    gradle_inputs = gradle_artifacts or {}
    component_ids = {component.identifier for component in components}
    unknown_gallery_input_ids = sorted(set(artifact_dirs) - component_ids)
    if unknown_gallery_input_ids:
        raise GateError(
            "--gallery-artifact-dir names add-ons outside the manifest: "
            + ", ".join(unknown_gallery_input_ids)
        )
    gallery_inputs = {
        identifier: attest_gallery_artifact_directory(path)
        for identifier, path in artifact_dirs.items()
    }
    unknown_gradle_input_ids = sorted(set(gradle_inputs) - component_ids)
    if unknown_gradle_input_ids:
        raise GateError(
            "--gradle-artifact names add-ons outside the manifest: "
            + ", ".join(unknown_gradle_input_ids)
        )
    plans: list[ComponentPlan] = []
    addon_records: list[dict[str, object]] = []
    discovery_errors: list[str] = []
    for component in components:
        preflight = repository_state(root, component)
        try:
            plan = discover_commands(
                root,
                component,
                bluemap_source=bluemap_source,
                gallery_artifact_dirs=artifact_dirs,
                gradle_artifacts=gradle_inputs.get(component.identifier, {}),
                python_command=python_command,
                gradle_command=gradle_command,
            )
            gallery_input = gallery_inputs.get(component.identifier)
            if gallery_input is not None:
                used = any(
                    str(gallery_input.path) in command.argv
                    for command in plan.commands
                )
                if not used:
                    raise GateError(
                        f"{component.identifier}: supplied gallery artifact directory is unused"
                    )
                plan = dataclasses.replace(plan, gallery_artifact=gallery_input)
        except GateError as exc:
            discovery_errors.append(str(exc))
            plan = ComponentPlan(component, root / component.submodule_path, (), (), (str(exc),))
        plans.append(plan)
        addon_records.append(plan_record(plan, preflight))

    bad_preflights = [record["id"] for record in addon_records if not record["preflight"]["ok"]]
    manifest_bluemap = next(
        (
            value
            for value in manifest.get("components", [])
            if isinstance(value, dict) and value.get("kind") == "bluemap"
        ),
        None,
    )
    manifest_bluemap_commit = manifest_bluemap.get("commit") if manifest_bluemap else None
    if expected_bluemap_commit is None:
        if not isinstance(manifest_bluemap_commit, str) or not COMMIT_RE.fullmatch(manifest_bluemap_commit):
            raise GateError("manifest has no full BlueMap commit and no explicit integration override was supplied")
        active_bluemap_commit = manifest_bluemap_commit
        integration_override = False
    else:
        if not COMMIT_RE.fullmatch(expected_bluemap_commit):
            raise GateError(f"explicit BlueMap integration commit is not a full SHA-1: {expected_bluemap_commit}")
        active_bluemap_commit = expected_bluemap_commit
        integration_override = True
    bluemap_state = bluemap_source_state(
        root,
        bluemap_source,
        expected_commit=active_bluemap_commit,
        require_gitlink_match=not integration_override,
    )
    atmons = manifest.get("atmons") if isinstance(manifest.get("atmons"), dict) else {}
    report: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "runner": {
            "name": "integration/run_child_gates.py",
            "version": RUNNER_VERSION,
            "sha256": sha256_file(Path(__file__)),
            "sequential": True,
            "fail_on_git_state_change": True,
            "external_inputs_rehashed_before_after_each_command": True,
        },
        "mode": "plan",
        "target": {
            "atmons_version": atmons.get("version"),
            "pack_commit": atmons.get("pack_commit"),
            "manifest_path": str(manifest_path.relative_to(root)),
            "manifest_sha256": sha256_file(manifest_path),
            "manifest_validation": manifest_validation,
            "manifest_bluemap_commit": manifest_bluemap_commit,
            "active_bluemap_expected_commit": active_bluemap_commit,
            "bluemap_integration_override": integration_override,
            "active_bluemap_source": bluemap_state,
        },
        "settings": {
            "addon_order": [component.identifier for component in components],
            "expected_addons": expected_addons,
            "gallery_python_scope": "tracked gallery/generate.py --check, gallery/lint.py, and gallery/**/test_*.py",
            "gradle_gates": ["clean check build", "generatePomFileForAddonPublication"],
            "bluemap_source_path": bluemap_state["source"],
            "gallery_artifact_inputs": [
                {
                    "addon": identifier,
                    "file_count": artifact.file_count,
                    "size_bytes": artifact.size_bytes,
                    "sha256": artifact.sha256,
                    "files": [
                        {
                            "path": relative,
                            "size_bytes": size_bytes,
                            "sha256": digest,
                        }
                        for relative, size_bytes, digest in artifact.files
                    ],
                }
                for identifier, artifact in sorted(gallery_inputs.items())
            ],
            "gradle_artifact_inputs": [
                {
                    "addon": component_id,
                    "property": property_name,
                    "filename": artifact.path.name,
                    "size_bytes": artifact.size_bytes,
                    "sha256": artifact.sha256,
                }
                for component_id in sorted(gradle_inputs)
                for property_name, artifact in sorted(gradle_inputs[component_id].items())
            ],
        },
        "addons": addon_records,
        "summary": {
            "status": "ready" if not bad_preflights and not discovery_errors and bluemap_state["ok"] else "blocked",
            "addon_count": len(addon_records),
            "command_count": sum(len(plan.commands) for plan in plans),
            "preflight_failure_count": len(bad_preflights),
            "preflight_failed_addons": bad_preflights,
            "discovery_error_count": len(discovery_errors),
            "discovery_errors": discovery_errors,
            "bluemap_source_preflight_ok": bluemap_state["ok"],
        },
    }
    return report, tuple(plans)


def suite_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "CI": "true",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
    )
    return environment


def resolve_gradle_command(root: Path, requested: str | None) -> str:
    if requested:
        return requested
    shared_wrapper = root / "addons" / "ae2" / "gradlew"
    if shared_wrapper.is_file() and os.access(shared_wrapper, os.X_OK):
        return str(shared_wrapper)
    raise GateError(
        "no --gradle-command was supplied and the pinned AE2 Gradle wrapper is unavailable"
    )


def parse_gallery_artifact_dirs(root: Path, values: Sequence[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        identifier, separator, path_text = value.partition("=")
        if not separator or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier) or not path_text:
            raise GateError(f"invalid --gallery-artifact-dir value: {value!r}; expected addon-id=PATH")
        if identifier in result:
            raise GateError(f"duplicate --gallery-artifact-dir for {identifier}")
        path = Path(path_text)
        if not path.is_absolute():
            path = root / path
        result[identifier] = path.resolve()
    return result


def parse_gradle_artifacts(
    root: Path,
    values: Sequence[str],
) -> dict[str, dict[str, GradleArtifact]]:
    result: dict[str, dict[str, GradleArtifact]] = {}
    for value in values:
        owner, separator, path_text = value.partition("=")
        identifier, property_separator, property_name = owner.partition(":")
        if (
            not separator
            or not property_separator
            or not ADDON_ID_RE.fullmatch(identifier)
            or not GRADLE_ARTIFACT_PROPERTY_RE.fullmatch(property_name)
            or not path_text
        ):
            raise GateError(
                f"invalid --gradle-artifact value: {value!r}; "
                "expected addon-id:propertyJar=PATH"
            )
        per_addon = result.setdefault(identifier, {})
        if property_name in per_addon:
            raise GateError(
                f"duplicate --gradle-artifact for {identifier}:{property_name}"
            )
        path = Path(path_text)
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".jar":
            raise GateError(
                f"--gradle-artifact is not a regular non-symlink JAR: {identifier}:{property_name}"
            )
        size_bytes = path.stat().st_size
        if size_bytes <= 0:
            raise GateError(
                f"--gradle-artifact is empty: {identifier}:{property_name}"
            )
        per_addon[property_name] = GradleArtifact(
            property_name,
            path,
            size_bytes,
            sha256_file(path),
        )
    return result


def sanitized_output(
    output: bytes | str | None,
    root: Path,
    tail_lines: int,
    *,
    redactions: Mapping[str, str] | None = None,
) -> str:
    if output is None:
        return ""
    text = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else output
    text = text.replace(str(root), "<repo>")
    home = str(Path.home())
    if home and home != str(root):
        text = text.replace(home, "<home>")
    for source, replacement in (redactions or {}).items():
        text = text.replace(source, replacement)
    lines = text.rstrip().splitlines()
    return "\n".join(lines[-tail_lines:])


@contextmanager
def temporary_bluemap_source_alias(
    root: Path,
    source: Path,
    *,
    enabled: bool,
) -> Iterator[dict[str, object]]:
    alias = root / "addons" / "bluemap-backport"
    record: dict[str, object] = {
        "enabled": enabled,
        "path": "<repo>/addons/bluemap-backport",
        "created": False,
    }
    if not enabled:
        yield record
        return
    if alias.exists() or alias.is_symlink():
        if not alias.is_symlink() or alias.resolve() != source.resolve():
            raise GateError(
                "AE2's legacy BlueMap source alias exists but does not point to the active source"
            )
        record["preexisting"] = True
        yield record
        return
    alias.symlink_to(source.resolve(), target_is_directory=True)
    record["created"] = True
    try:
        yield record
    finally:
        try:
            alias.unlink()
        except FileNotFoundError:
            pass


def execute_command(
    root: Path,
    plan: ComponentPlan,
    command: CommandSpec,
    *,
    bluemap_source: Path,
    expected_bluemap_commit: str,
    require_bluemap_gitlink_match: bool,
    timeout_seconds: float,
    tail_lines: int,
) -> dict[str, object]:
    print(f"[{plan.component.identifier}] {command.identifier}: {shlex.join(command.display_argv)}", file=sys.stderr, flush=True)
    started = time.monotonic()
    record: dict[str, object] = {
        "id": command.identifier,
        "description": command.description,
        "argv": list(command.display_argv),
        "status": "error",
        "exit_code": None,
        "duration_seconds": None,
        "output_tail": "",
        "integrity_after": None,
        "bluemap_source_integrity_after": None,
        "external_input_integrity_before": None,
        "external_input_integrity_after": None,
        "temporary_bluemap_source_alias": None,
    }
    redactions = {
        str(artifact.path): f"<artifact:{plan.component.identifier}:{artifact.property_name}>"
        for artifact in plan.gradle_artifacts
    }
    needs_legacy_alias = (
        plan.component.identifier == "ae2"
        and command.identifier == "gradle-clean-check-build"
    )
    input_before = external_input_state(plan)
    record["external_input_integrity_before"] = input_before
    if not input_before["ok"]:
        record["status"] = "integrity_failed"
        record["output_tail"] = "external execution input changed before command"
    else:
        try:
            with temporary_bluemap_source_alias(
                root,
                bluemap_source,
                enabled=needs_legacy_alias,
            ) as alias_record:
                record["temporary_bluemap_source_alias"] = alias_record
                result = run_process(
                    command.argv,
                    cwd=plan.repository,
                    timeout=timeout_seconds,
                    environment=suite_environment(),
                )
            record["exit_code"] = result.returncode
            record["output_tail"] = sanitized_output(
                result.stdout,
                root,
                tail_lines,
                redactions=redactions,
            )
            record["status"] = "passed" if result.returncode == 0 else "failed"
        except subprocess.TimeoutExpired as exc:
            record["status"] = "timeout"
            record["output_tail"] = sanitized_output(
                exc.stdout,
                root,
                tail_lines,
                redactions=redactions,
            )
        except GateError as exc:
            record["status"] = "error"
            record["output_tail"] = str(exc)
        except OSError as exc:
            record["status"] = "error"
            record["output_tail"] = str(exc)
    record["duration_seconds"] = round(time.monotonic() - started, 3)

    integrity = repository_state(root, plan.component)
    bluemap_integrity = bluemap_source_state(
        root,
        bluemap_source,
        expected_commit=expected_bluemap_commit,
        require_gitlink_match=require_bluemap_gitlink_match,
    )
    record["integrity_after"] = integrity
    record["bluemap_source_integrity_after"] = bluemap_integrity
    input_after = external_input_state(plan)
    record["external_input_integrity_after"] = input_after
    if not integrity["ok"] or not bluemap_integrity["ok"] or not input_after["ok"]:
        record["status"] = "integrity_failed"
    return record


def execute_suite(
    root: Path,
    plan_report: dict[str, object],
    plans: Sequence[ComponentPlan],
    *,
    bluemap_source: Path,
    timeout_seconds: float,
    tail_lines: int,
    fail_fast: bool,
) -> dict[str, object]:
    report = json.loads(json.dumps(plan_report))
    expected_bluemap_commit = str(report["target"]["active_bluemap_expected_commit"])
    require_bluemap_gitlink_match = not bool(report["target"]["bluemap_integration_override"])
    report["mode"] = "run"
    report["settings"]["command_timeout_seconds"] = timeout_seconds
    report["settings"]["output_tail_lines"] = tail_lines
    report["settings"]["fail_fast"] = fail_fast
    if report["summary"]["status"] != "ready":
        report["summary"]["status"] = "failed_preflight"
        report["summary"]["duration_seconds"] = 0.0
        return report

    started = time.monotonic()
    stopped = False
    for addon_record, plan in zip(report["addons"], plans, strict=True):
        if stopped:
            for command in addon_record["commands"]:
                command["status"] = "not_run_fail_fast"
            addon_record["status"] = "not_run_fail_fast"
            continue

        current = repository_state(root, plan.component)
        current_bluemap = bluemap_source_state(
            root,
            bluemap_source,
            expected_commit=expected_bluemap_commit,
            require_gitlink_match=require_bluemap_gitlink_match,
        )
        current_external_inputs = external_input_state(plan)
        addon_record["pre_run_integrity"] = current
        addon_record["pre_run_bluemap_source_integrity"] = current_bluemap
        addon_record["pre_run_external_input_integrity"] = current_external_inputs
        if not current["ok"] or not current_bluemap["ok"] or not current_external_inputs["ok"]:
            addon_record["status"] = "integrity_failed"
            for command in addon_record["commands"]:
                command["status"] = "not_run_integrity"
            if fail_fast:
                stopped = True
            continue

        executed: list[dict[str, object]] = []
        child_failed = False
        for index, command in enumerate(plan.commands):
            result = execute_command(
                root,
                plan,
                command,
                bluemap_source=bluemap_source,
                expected_bluemap_commit=expected_bluemap_commit,
                require_bluemap_gitlink_match=require_bluemap_gitlink_match,
                timeout_seconds=timeout_seconds,
                tail_lines=tail_lines,
            )
            executed.append(result)
            if result["status"] != "passed":
                child_failed = True
                for pending in plan.commands[index + 1 :]:
                    executed.append(
                        {
                            "id": pending.identifier,
                            "description": pending.description,
                            "argv": list(pending.display_argv),
                            "status": "not_run_after_failure",
                            "exit_code": None,
                            "duration_seconds": 0.0,
                            "output_tail": "",
                            "integrity_after": None,
                            "bluemap_source_integrity_after": None,
                            "external_input_integrity_before": None,
                            "external_input_integrity_after": None,
                        }
                    )
                break
        addon_record["commands"] = executed
        addon_record["post_run_integrity"] = repository_state(root, plan.component)
        addon_record["status"] = "failed" if child_failed or not addon_record["post_run_integrity"]["ok"] else "passed"
        if addon_record["status"] != "passed" and fail_fast:
            stopped = True

    final_integrity = [
        {"id": plan.component.identifier, **repository_state(root, plan.component)} for plan in plans
    ]
    report["final_integrity"] = final_integrity
    final_external_inputs = [
        {"id": plan.component.identifier, **external_input_state(plan)}
        for plan in plans
    ]
    report["final_external_input_integrity"] = final_external_inputs
    final_bluemap_integrity = bluemap_source_state(
        root,
        bluemap_source,
        expected_commit=expected_bluemap_commit,
        require_gitlink_match=require_bluemap_gitlink_match,
    )
    report["final_bluemap_source_integrity"] = final_bluemap_integrity
    passed = sum(record.get("status") == "passed" for record in report["addons"])
    failed = sum(record.get("status") in {"failed", "integrity_failed"} for record in report["addons"])
    not_run = len(report["addons"]) - passed - failed
    command_statuses = [
        command.get("status") for record in report["addons"] for command in record.get("commands", [])
    ]
    external_inputs_ok = all(item["ok"] for item in final_external_inputs)
    integrity_ok = (
        all(item["ok"] for item in final_integrity)
        and bool(final_bluemap_integrity["ok"])
        and external_inputs_ok
    )
    report["summary"] = {
        "status": "passed" if passed == len(plans) and integrity_ok else "failed",
        "addon_count": len(plans),
        "passed_addons": passed,
        "failed_addons": failed,
        "not_run_addons": not_run,
        "command_count": len(command_statuses),
        "passed_commands": command_statuses.count("passed"),
        "failed_commands": sum(status in {"failed", "timeout", "error", "integrity_failed"} for status in command_statuses),
        "not_run_commands": sum(isinstance(status, str) and status.startswith("not_run") for status in command_statuses),
        "final_integrity_ok": integrity_ok,
        "final_bluemap_source_integrity_ok": final_bluemap_integrity["ok"],
        "final_external_input_integrity_ok": external_inputs_ok,
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    return report


def evaluate_expected_rejection(
    report: dict[str, object],
    *,
    expected_pass_addons: set[str] | None = None,
) -> dict[str, object]:
    report["mode"] = "expected-rejection"
    runner = report.get("runner")
    if isinstance(runner, dict):
        runner["expected_rejection_evaluator"] = {
            "version": RUNNER_VERSION,
            "sha256": sha256_file(Path(__file__)),
        }
    summary = report.get("summary")
    target = report.get("target")
    if not isinstance(summary, dict) or not isinstance(target, dict):
        raise GateError("expected-rejection report is missing suite target or summary")

    active_commit = target.get("active_bluemap_expected_commit")
    manifest_commit = target.get("manifest_bluemap_commit")
    integration_override = target.get("bluemap_integration_override")
    configuration_ok = bool(
        integration_override
        and isinstance(active_commit, str)
        and isinstance(manifest_commit, str)
        and active_commit != manifest_commit
    )
    rejection_pattern = (
        re.compile(
            rf"Refusing(?: to evaluate)? BlueMap {re.escape(active_commit)}; "
            rf"expected {re.escape(manifest_commit)}"
        )
        if configuration_ok
        else None
    )

    matched = 0
    unexpected: list[dict[str, str]] = []
    addons = report.get("addons")
    if not isinstance(addons, list):
        raise GateError("expected-rejection report has no add-on records")
    for addon in addons:
        if not isinstance(addon, dict):
            continue
        if "observed_status" in addon:
            addon["status"] = addon.pop("observed_status")
        addon.pop("expected_rejection", None)
        commands = addon.get("commands")
        if not isinstance(commands, list):
            continue
        for command in commands:
            if isinstance(command, dict) and "observed_status" in command:
                command["status"] = command.pop("observed_status")
    expected_pass = expected_pass_addons or set()
    addon_ids = {
        str(addon.get("id")) for addon in addons if isinstance(addon, dict)
    }
    unknown_expected_pass = sorted(expected_pass - addon_ids)
    if unknown_expected_pass:
        raise GateError(
            "--expected-pass-addon names add-ons outside the suite: "
            + ", ".join(unknown_expected_pass)
        )
    passed_as_expected = 0
    for addon in addons:
        if not isinstance(addon, dict):
            raise GateError("expected-rejection report has a malformed add-on record")
        addon_id = str(addon.get("id"))
        commands = addon.get("commands")
        failed_commands = (
            [
                command
                for command in commands
                if isinstance(command, dict)
                and command.get("status") in {"failed", "timeout", "error", "integrity_failed"}
            ]
            if isinstance(commands, list)
            else []
        )
        command = failed_commands[0] if len(failed_commands) == 1 else None
        output = command.get("output_tail", "") if command else ""
        expects_pass = addon_id in expected_pass
        matched_pass = bool(
            expects_pass
            and addon.get("status") == "passed"
            and not failed_commands
        )
        matched_rejection = bool(
            not expects_pass
            and configuration_ok
            and addon.get("status") == "failed"
            and command is not None
            and command.get("id") == "gradle-clean-check-build"
            and command.get("exit_code") not in {None, 0}
            and isinstance(output, str)
            and rejection_pattern is not None
            and rejection_pattern.search(output)
        )
        addon["expected_rejection"] = {
            "matched": matched_rejection,
            "expects_pass": expects_pass,
            "matched_pass": matched_pass,
            "active_bluemap_commit": active_commit,
            "manifest_bluemap_commit": manifest_commit,
        }
        if matched_rejection:
            matched += 1
            addon["observed_status"] = addon["status"]
            addon["status"] = "expected_rejection"
            command["observed_status"] = command["status"]
            command["status"] = "expected_rejection"
        elif matched_pass:
            passed_as_expected += 1
            addon["observed_status"] = addon["status"]
            addon["status"] = "expected_pass"
        else:
            reason = "result did not match the declared candidate-build expectation"
            if not configuration_ok:
                reason = "active BlueMap commit is not an explicit non-manifest integration override"
            unexpected.append({"id": addon_id, "reason": reason})

    final_integrity_ok = bool(summary.get("final_integrity_ok"))
    duration_seconds = summary.get("duration_seconds", 0.0)
    command_statuses = [
        command.get("status")
        for addon in addons
        if isinstance(addon, dict)
        for command in addon.get("commands", [])
        if isinstance(command, dict)
    ]
    report["expectation"] = {
        "kind": "declared-candidate-build-outcomes",
        "configuration_ok": configuration_ok,
        "active_bluemap_commit": active_commit,
        "manifest_bluemap_commit": manifest_commit,
        "required_command": "gradle-clean-check-build",
        "required_message": "Refusing [to evaluate] BlueMap <active>; expected <manifest>",
        "expected_pass_addons": sorted(expected_pass),
    }
    report["summary"] = {
        "status": (
            "passed"
            if matched + passed_as_expected == len(addons) and final_integrity_ok
            else "failed"
        ),
        "addon_count": len(addons),
        "expected_rejection_addons": matched,
        "expected_pass_addons": passed_as_expected,
        "unexpected_addons": len(unexpected),
        "unexpected_results": unexpected,
        "command_count": len(command_statuses),
        "passed_commands_before_rejection": command_statuses.count("passed"),
        "expected_rejection_commands": command_statuses.count("expected_rejection"),
        "not_run_commands": sum(
            isinstance(status, str) and status.startswith("not_run")
            for status in command_statuses
        ),
        "final_integrity_ok": final_integrity_ok,
        "final_bluemap_source_integrity_ok": summary.get(
            "final_bluemap_source_integrity_ok", False
        ),
        "final_external_input_integrity_ok": summary.get(
            "final_external_input_integrity_ok", False
        ),
        "duration_seconds": duration_seconds,
    }
    return report


def write_json_atomic(path: Path, report: dict[str, object], *, replace: bool) -> None:
    if path.exists() and not replace:
        raise GateError(f"output already exists (pass --replace to overwrite it): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", default="1.2.0")
    parser.add_argument("--manifest", type=Path, help="override versions/<version>/manifest.json")
    parser.add_argument(
        "--bluemap-source",
        type=Path,
        help="clean BlueMap source checkout; defaults to the meta-repository bluemap submodule",
    )
    parser.add_argument(
        "--expected-bluemap-commit",
        help="explicit full BlueMap integration commit; permits the active worktree to differ from the immutable manifest gitlink",
    )
    parser.add_argument(
        "--gallery-artifact-dir",
        action="append",
        default=[],
        metavar="ADDON=PATH",
        help="exact third-party artifact directory required by a gallery check; repeat per add-on",
    )
    parser.add_argument(
        "--gradle-artifact",
        action="append",
        default=[],
        metavar="ADDON:PROPERTY=PATH",
        help=(
            "exact JAR passed as a declared Gradle property; paths are hashed and redacted "
            "from the report; repeat per property"
        ),
    )
    parser.add_argument("--expected-addons", type=int, default=51)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="verify/discover only; execute no child commands")
    mode.add_argument("--run", action="store_true", help="execute the full sequential suite")
    mode.add_argument(
        "--expect-rejection",
        action="store_true",
        help=(
            "execute the candidate-negative suite and pass only when each add-on matches "
            "its declared rejection or reviewed pass expectation"
        ),
    )
    parser.add_argument(
        "--expected-pass-addon",
        action="append",
        default=[],
        metavar="ADDON",
        help=(
            "with --expect-rejection, require this add-on's source build to pass instead; "
            "repeat for each reviewed exception"
        ),
    )
    parser.add_argument("--output", type=Path, help="JSON report path; required with --run")
    parser.add_argument("--replace", action="store_true", help="replace an existing explicit output")
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--tail-lines", type=int, default=80)
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--python-command", default=sys.executable)
    parser.add_argument(
        "--gradle-command",
        help="Gradle executable for children without wrappers; defaults to the pinned AE2 Gradle 9.4 wrapper",
    )
    args = parser.parse_args(argv)
    if (args.run or args.expect_rejection) and args.output is None:
        parser.error("--run and --expect-rejection require --output")
    if args.replace and args.output is None:
        parser.error("--replace requires --output")
    if args.expected_pass_addon and not args.expect_rejection:
        parser.error("--expected-pass-addon requires --expect-rejection")
    if any(not ADDON_ID_RE.fullmatch(value) for value in args.expected_pass_addon):
        parser.error("--expected-pass-addon values must be add-on ids")
    if len(args.expected_pass_addon) != len(set(args.expected_pass_addon)):
        parser.error("--expected-pass-addon values must be unique")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.tail_lines <= 0:
        parser.error("--tail-lines must be positive")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.repo.resolve()
    manifest = (args.manifest or root / "versions" / args.version / "manifest.json").resolve()
    bluemap_source = args.bluemap_source or root / "bluemap"
    if not bluemap_source.is_absolute():
        bluemap_source = root / bluemap_source
    bluemap_source = bluemap_source.resolve()
    try:
        manifest_validation = validate_manifest_selection(root, manifest, args.version)
        gradle_command = resolve_gradle_command(root, args.gradle_command)
        gallery_artifact_dirs = parse_gallery_artifact_dirs(root, args.gallery_artifact_dir)
        gradle_artifacts = parse_gradle_artifacts(root, args.gradle_artifact)
        plan_report, plans = build_plan(
            root,
            manifest,
            expected_addons=args.expected_addons,
            bluemap_source=bluemap_source,
            expected_bluemap_commit=args.expected_bluemap_commit,
            manifest_validation=manifest_validation,
            gallery_artifact_dirs=gallery_artifact_dirs,
            gradle_artifacts=gradle_artifacts,
            python_command=args.python_command,
            gradle_command=gradle_command,
        )
        if args.run or args.expect_rejection:
            report = execute_suite(
                root,
                plan_report,
                plans,
                bluemap_source=bluemap_source,
                timeout_seconds=args.timeout_seconds,
                tail_lines=args.tail_lines,
                fail_fast=args.fail_fast,
            )
            if args.expect_rejection:
                report = evaluate_expected_rejection(
                    report,
                    expected_pass_addons=set(args.expected_pass_addon),
                )
        else:
            report = plan_report
        if args.output is not None:
            output = args.output if args.output.is_absolute() else root / args.output
            write_json_atomic(output, report, replace=args.replace)
            print(f"wrote child-gate {report['mode']} report: {output}")
        else:
            print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["summary"]["status"] in {"ready", "passed"} else 1
    except GateError as exc:
        print(f"child-gate suite error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
