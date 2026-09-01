#!/usr/bin/env python3
"""Build staging-only add-on JAR overlays for one exact BlueMap identity.

Published add-ons deliberately reject unknown BlueMap internals. For legacy
release bases, this tool compiles a copied AdapterCompatibility class with one
added candidate identity and rewrites the entrypoint. Explicit local release
overrides already migrated to the exact 5.23 feature backport keep their
shipped compatibility class and adapter intact; only their entrypoint is
rewritten to prove the Boolean install result and emit the integration marker.
Every replacement and resulting artifact is hashed. The ordinary source gates
are run separately by ``run_child_gates.py``. Nothing produced here is
published.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "versions" / "1.2.0" / "manifest.json"
VALIDATOR_PATH = ROOT / "tools" / "validate.py"
EXPECTED_MANIFEST_SHA256 = "ef1aebac5a1fbf2d4a1d91b3962a4078416239fba2e47fbcea941b8a2b1d34ca"
EXPECTED_VALIDATOR_SHA256 = "e4e5d66d4314c381a7a657065ff51a818f7f48e823eaa13b9b25f6366adef1ba"
CLASS_DECLARATION = re.compile(r"(public\s+final\s+class\s+AdapterCompatibility\s*\{\s*\n)")
SUPPORTED_RETURN = re.compile(
    r"(?P<header>(?:public\s+)?static\s+boolean\s+supported\s*\(\s*"
    r"String\s+version\s*,\s*String\s+(?P<identity>[A-Za-z_$][A-Za-z0-9_$]*)\s*\)\s*\{\s*\n)"
    r"(?P<indent>\s*)return\s+",
    re.MULTILINE,
)
CURRENT_RUNTIME_RETURN = re.compile(
    r"(?P<header>public\s+static\s+boolean\s+currentRuntimeSupported\s*"
    r"\(\s*\)\s*\{\s*\n)(?P<indent>\s*)return\s+",
    re.MULTILINE,
)
INSTALL_INVOKE = re.compile(r"^(?P<indent>\s*)install\.invoke\(null\);\s*$", re.MULTILINE)
INSTALL_SIGNATURE = re.compile(
    r"public\s+static\s+synchronized\s+boolean\s+install\s*\(\s*\)"
)
ENTRYPOINT_CLASS = re.compile(
    r"public\s+final\s+class\s+BlueMap[A-Za-z0-9]+Addon\s+implements\s+Runnable"
)
FEATURE_BACKPORT_VERSION = "5.22-feature.backport-5.23-stateless-java-web-server-46"
FEATURE_BACKPORT_COMMIT = "7e07f4e74ec1e92a6ead9aa1e66054af3e133aac"
FEATURE_BACKPORT_API_COMMIT = "285c9a60eff3ac2b0cab308ce1058d1565be0971"
ADAPTER_API_VERSION = "0.1.0-alpha.2"
ADAPTER_API_TAG = "v0.1.0-alpha.2"
ADAPTER_API_COMMIT = "e81f08bc4bfbf02d810ec8949a019130e2e61634"
ADAPTER_API_SOURCE_TREE = "2f974c9bb2ba13888d69682f86f30f58922d30eb"
ADAPTER_API_GITLINK = "modules/bluemap-addon-adapter-api"
ADAPTER_API_REPOSITORY = (
    "https://github.com/jan-guenter/bluemap-addon-adapter-api"
)
ADAPTER_API_COORDINATE = (
    "io.github.jan-guenter:bluemap-addon-adapter-api:" + ADAPTER_API_VERSION
)
RENDER_CORE_VERSION = "0.1.0-alpha.2"
RENDER_CORE_TAG = "v0.1.0-alpha.2"
RENDER_CORE_COMMIT = "24b84efdc8235f3f1323e1a8e9fd033080e3a79e"
RENDER_CORE_SOURCE_TREE = "424040931680fb82d37693f893ca887c0ed48eae"
RENDER_CORE_GITLINK = "modules/bluemap-addon-render-core"
RENDER_CORE_SOURCE_PACKAGE = (
    "io.github.janguenter.bluemap.addon.render.core.adapter.bluemap523"
)
ADAPTER_API_CLASS_PREFIX = (
    "io/github/janguenter/bluemap/addon/adapter/api/bluemap523/"
)
ADAPTER_API_CLASSES = {
    ADAPTER_API_CLASS_PREFIX + name + ".class"
    for name in (
        "BlueMapRuntimeCompatibility",
        "RegistryGuard",
        "ResourceExtensionType",
        "SyntheticDispatch",
    )
}
# Exact class payloads from the audited module release and audited
# source-bundled consumer builds. The two compiler variants produce identical
# ``javap -p -c -s -constants`` output for every class.
ADAPTER_API_CLASS_SHA256 = {
    ADAPTER_API_CLASS_PREFIX + "BlueMapRuntimeCompatibility.class": {
        "feeb9e6bcf6c3cf241314df6b70e33a0296abd54f9da63dc5bdc735762605006",
        "eb7fe1bfecb61700007b9029e2cb2870fa363a8e4ec9435e803ace6e42bb11e6",
    },
    ADAPTER_API_CLASS_PREFIX + "RegistryGuard.class": {
        "ccb6493f162472e2e24705fe4c5e905889c85fb6ec7febcab6a2f5cd3fbb43d6",
        "58c107277da1df273c6329253f76abf46b47fe2c1fcf006fe51700e2c45bef91",
    },
    ADAPTER_API_CLASS_PREFIX + "ResourceExtensionType.class": {
        "37d04ae4892c2ce967a58d408f5e9c5f0709ee18fb1ac8c1f94e08da014d8b5f",
        "e3e01aa1bafec529f50005a1c76125a686f967a9db1dab694217bb7915c0b5a2",
    },
    ADAPTER_API_CLASS_PREFIX + "SyntheticDispatch.class": {
        "8f8e04e7a2613d9a482015eb7d9d28925fba5f670c39c84a56d1417f5bebf70d",
        "270bcd0add7db596cd9fba2bf78454421ff19503d62f762634227faac6d6d988",
    },
}


class CandidateError(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    command: list[str], cwd: Path | None = None, timeout: int = 1800
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode:
        tail = "\n".join(result.stdout.splitlines()[-80:])
        raise CandidateError(f"{' '.join(command)} failed ({result.returncode}):\n{tail}")
    return result


def load_manifest(path: Path) -> dict:
    if sha256(DEFAULT_MANIFEST) != EXPECTED_MANIFEST_SHA256:
        raise CandidateError(
            "tracked ATMons 1.2.0 manifest differs from its immutable released-profile digest"
        )
    if sha256(VALIDATOR_PATH) != EXPECTED_VALIDATOR_SHA256:
        raise CandidateError(
            "shared manifest validator differs from its reviewed immutable digest"
        )
    spec = importlib.util.spec_from_file_location("bluemap_atmons_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise CandidateError("cannot load the repository manifest validator")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    try:
        errors, value = validator.validate_manifest(path)
    except (OSError, ValueError) as exc:
        raise CandidateError(f"cannot validate compatibility manifest {path}: {exc}") from exc
    if errors or value is None:
        raise CandidateError("invalid compatibility manifest: " + "; ".join(errors))
    if value.get("atmons", {}).get("version") != "1.2.0":
        raise CandidateError("candidate builder is exact to ATMons 1.2.0")
    if path.read_bytes() != DEFAULT_MANIFEST.read_bytes():
        raise CandidateError(
            "candidate builder requires the byte-exact tracked ATMons 1.2.0 manifest"
        )
    return value


def _require_exact_keys(value: dict, expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise CandidateError(
            f"{label} keys differ from the exact contract: "
            f"expected={sorted(expected)}, actual={sorted(value)}"
        )


def _validate_override_jar(path: Path, component_id: str, version: str) -> None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            if not names:
                raise CandidateError(f"{component_id}: local candidate JAR is empty")
            if len(names) != len(set(names)):
                raise CandidateError(
                    f"{component_id}: local candidate JAR contains duplicate ZIP entries"
                )
            corrupt = archive.testzip()
            if corrupt:
                raise CandidateError(
                    f"{component_id}: local candidate JAR has corrupt ZIP entry {corrupt}"
                )
            if names.count("META-INF/MANIFEST.MF") != 1:
                raise CandidateError(
                    f"{component_id}: local candidate JAR must contain one manifest"
                )
            try:
                manifest_text = archive.read("META-INF/MANIFEST.MF").decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CandidateError(
                    f"{component_id}: local candidate JAR manifest is not UTF-8"
                ) from exc
            implementation_versions = re.findall(
                r"^Implementation-Version:\s*([^\r\n]+)\r?$",
                manifest_text,
                re.MULTILINE,
            )
            if implementation_versions != [version]:
                raise CandidateError(
                    f"{component_id}: local candidate JAR manifest version mismatch"
                )
    except (OSError, zipfile.BadZipFile) as exc:
        raise CandidateError(
            f"{component_id}: local candidate artifact is not a readable JAR: {exc}"
        ) from exc


def _validate_override_release_provenance(
    checkout: Path,
    source_commit: str,
    component_id: str,
    artifact: dict,
) -> dict[str, str]:
    provenance_path = "provenance/release.json"
    try:
        raw = run(
            ["git", "show", f"{source_commit}:{provenance_path}"], checkout
        ).stdout.encode("utf-8")
        value = json.loads(raw)
    except (CandidateError, json.JSONDecodeError) as exc:
        raise CandidateError(
            f"{component_id}: exact source commit lacks readable release provenance"
        ) from exc
    if not isinstance(value, dict):
        raise CandidateError(f"{component_id}: release provenance must be an object")
    status = value.get("status")
    if status == "owner-accepted-release-candidate":
        artifacts = value.get("final_release_artifacts")
        status_valid = "candidate_artifacts" not in value
    elif status == "unpublished-migration-candidate":
        artifacts = value.get("candidate_artifacts")
        status_valid = (
            value.get("published") is False
            and "final_release_artifacts" not in value
        )
    else:
        artifacts = None
        status_valid = False
    production_jar = (
        artifacts.get("production_jar")
        if isinstance(artifacts, dict)
        else None
    )
    expected_production_jar = {
        "file_name": artifact["filename"],
        "size": artifact["sizeBytes"],
        "sha256": artifact["sha256"],
    }
    if (
        type(value.get("schema_version")) is not int
        or value.get("schema_version") != 1
        or not status_valid
        or value.get("version") != artifact["version"]
        or value.get("tag") != f"v{artifact['version']}"
        or production_jar != expected_production_jar
    ):
        raise CandidateError(
            f"{component_id}: local candidate artifact differs from exact source provenance"
        )
    return {
        "path": provenance_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "status": status,
    }


def _main_java_paths(checkout: Path, commit: str) -> list[str]:
    return run(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", "src/main/java"],
        checkout,
    ).stdout.splitlines()


def _native_adapter_paths(paths: list[str]) -> list[str]:
    return sorted(
        path
        for path in paths
        if path.endswith("/adapter/bluemap523/BlueMap523Adapter.java")
    )


def _normalize_adapter_api_migration(
    checkout: Path, commit: str, component_id: str
) -> dict:
    provenance_path = "provenance/release.json"
    try:
        value = json.loads(
            run(["git", "show", f"{commit}:{provenance_path}"], checkout).stdout
        )
    except (CandidateError, json.JSONDecodeError) as exc:
        raise CandidateError(
            f"{component_id}: native feature-backport migration provenance is unreadable"
        ) from exc
    if not isinstance(value, dict):
        raise CandidateError(
            f"{component_id}: native feature-backport migration provenance must be "
            "an object"
        )
    section_names = (
        "adapter_api_migration",
        "adapter_api_module_migration",
        "adapter_api_source",
        "adapter_api",
    )
    candidates = [(name, value[name]) for name in section_names if name in value]
    if len(candidates) != 1 or not isinstance(candidates[0][1], dict):
        raise CandidateError(
            f"{component_id}: expected exactly one Adapter API migration provenance "
            "object"
        )
    section_name, section = candidates[0]

    def field(source: dict, label: str, *names: str) -> str:
        present = [source[name] for name in names if name in source]
        if len(present) != 1 or not isinstance(present[0], str):
            raise CandidateError(
                f"{component_id}: Adapter API migration {label} is ambiguous or missing"
            )
        return present[0]

    def require_exact_mapping(source: object, expected: dict, label: str) -> None:
        if not isinstance(source, dict) or set(source) != set(expected):
            raise CandidateError(
                f"{component_id}: {label} differs from the exact 5.23 contract"
            )
        for key, expected_value in expected.items():
            actual = source[key]
            if type(actual) is not type(expected_value) or actual != expected_value:
                raise CandidateError(
                    f"{component_id}: {label} differs from the exact 5.23 contract"
                )

    def require_absent(names: tuple[str, ...], label: str) -> None:
        present = [name for name in names if name in value]
        if present:
            raise CandidateError(
                f"{component_id}: {label} conflicts with the exact 5.23 contract"
            )

    host_identity = {
        "bluemap_version": FEATURE_BACKPORT_VERSION,
        "bluemap_commit": FEATURE_BACKPORT_COMMIT,
        "bluemap_api_commit": FEATURE_BACKPORT_API_COMMIT,
    }
    published_source_only = False
    section_keys = set(section)

    if section_name == "adapter_api_migration" and "module_commit" in section_keys:
        require_exact_mapping(
            section,
            {
                "module_repository": ADAPTER_API_REPOSITORY,
                "module_version": ADAPTER_API_VERSION,
                "module_tag": ADAPTER_API_TAG,
                "module_commit": ADAPTER_API_COMMIT,
                "module_source_tree": ADAPTER_API_SOURCE_TREE,
                "compiled_source_count": 4,
                "standalone_module_jar_bundled": False,
            },
            "published Botany-style Adapter API provenance",
        )
        require_exact_mapping(value.get("host"), host_identity, "BlueMap host identity")
        require_absent(("bluemap",), "alternate BlueMap host provenance")
        normalized = {
            "section": section_name,
            "repository": ADAPTER_API_REPOSITORY,
            "version": ADAPTER_API_VERSION,
            "tag": ADAPTER_API_TAG,
            "commit": ADAPTER_API_COMMIT,
            "sourceTree": ADAPTER_API_SOURCE_TREE,
            "blueMapCommit": FEATURE_BACKPORT_COMMIT,
            "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
        }
        published_source_only = True
    elif (
        section_name == "adapter_api_migration"
        and "standalone_module_jar" in section_keys
    ):
        require_exact_mapping(
            section,
            {
                "repository": ADAPTER_API_REPOSITORY,
                "version": ADAPTER_API_VERSION,
                "tag": ADAPTER_API_TAG,
                "commit": ADAPTER_API_COMMIT,
                "source_tree": ADAPTER_API_SOURCE_TREE,
                "gitlink": ADAPTER_API_GITLINK,
                "standalone_module_jar": "not-bundled-or-installed",
            },
            "published Chisel-style Adapter API provenance",
        )
        require_exact_mapping(value.get("host"), host_identity, "BlueMap host identity")
        require_absent(("bluemap",), "alternate BlueMap host provenance")
        normalized = {
            "section": section_name,
            "repository": ADAPTER_API_REPOSITORY,
            "version": ADAPTER_API_VERSION,
            "tag": ADAPTER_API_TAG,
            "commit": ADAPTER_API_COMMIT,
            "sourceTree": ADAPTER_API_SOURCE_TREE,
            "blueMapCommit": FEATURE_BACKPORT_COMMIT,
            "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
        }
        published_source_only = True
    elif section_name == "adapter_api" and "source_files_bundled" in section_keys:
        require_exact_mapping(
            section,
            {
                "version": ADAPTER_API_VERSION,
                "commit": ADAPTER_API_COMMIT,
                "source_tree": ADAPTER_API_SOURCE_TREE,
                "source_files_bundled": 4,
                "module_jar_bundled": False,
            },
            "published compact Adapter API provenance",
        )
        require_exact_mapping(
            value.get("bluemap"),
            {
                "commit": FEATURE_BACKPORT_COMMIT,
                "api_commit": FEATURE_BACKPORT_API_COMMIT,
                "version": FEATURE_BACKPORT_VERSION,
            },
            "BlueMap host identity",
        )
        require_absent(("host",), "alternate BlueMap host provenance")
        normalized = {
            "section": section_name,
            "repository": ADAPTER_API_REPOSITORY,
            "version": ADAPTER_API_VERSION,
            "tag": ADAPTER_API_TAG,
            "commit": ADAPTER_API_COMMIT,
            "sourceTree": ADAPTER_API_SOURCE_TREE,
            "blueMapCommit": FEATURE_BACKPORT_COMMIT,
            "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
        }
        published_source_only = True
    elif section_name == "adapter_api" and "source_files_compiled" in section_keys:
        adapter_package = section.get("local_adapter_package")
        expected_section = {
            "version": ADAPTER_API_VERSION,
            "commit": ADAPTER_API_COMMIT,
            "source_tree": ADAPTER_API_SOURCE_TREE,
            "source_files_compiled": 4,
            "module_jar_installed": False,
            "module_jar_bundled": False,
            "module_jar_nested": False,
            "local_adapter_package": adapter_package,
        }
        if not isinstance(adapter_package, str) or re.fullmatch(
            r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*",
            adapter_package,
        ) is None:
            raise CandidateError(
                f"{component_id}: candidate compact Adapter API local_adapter_package "
                "is not a valid dotted Java package"
            )
        require_exact_mapping(
            section,
            expected_section,
            "candidate compact Adapter API provenance",
        )
        expected_adapter_path = (
            "src/main/java/"
            + adapter_package.replace(".", "/")
            + "/BlueMap523Adapter.java"
        )
        native_adapter_paths = _native_adapter_paths(
            _main_java_paths(checkout, commit)
        )
        if native_adapter_paths != [expected_adapter_path]:
            raise CandidateError(
                f"{component_id}: candidate compact Adapter API local_adapter_package "
                "does not identify the sole native adapter"
            )
        require_exact_mapping(
            value.get("bluemap"),
            {
                "version": FEATURE_BACKPORT_VERSION,
                "commit": FEATURE_BACKPORT_COMMIT,
                "api_commit": FEATURE_BACKPORT_API_COMMIT,
            },
            "BlueMap host identity",
        )
        require_absent(("host",), "alternate BlueMap host provenance")
        normalized = {
            "section": section_name,
            "repository": ADAPTER_API_REPOSITORY,
            "version": ADAPTER_API_VERSION,
            "tag": ADAPTER_API_TAG,
            "commit": ADAPTER_API_COMMIT,
            "sourceTree": ADAPTER_API_SOURCE_TREE,
            "blueMapCommit": FEATURE_BACKPORT_COMMIT,
            "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
            "localAdapterPackage": adapter_package,
        }
        published_source_only = True
    elif section_name == "adapter_api":
        raise CandidateError(
            f"{component_id}: compact Adapter API provenance differs from the exact "
            "5.23 contract"
        )
    elif (
        section_name == "adapter_api_migration" and "module" in section_keys
    ):
        require_exact_mapping(
            section,
            {
                "module": ADAPTER_API_COORDINATE,
                "repository": ADAPTER_API_REPOSITORY,
                "commit": ADAPTER_API_COMMIT,
                "source_tree": ADAPTER_API_SOURCE_TREE,
                "source_files_bundled": 4,
                "local_helpers_removed": 3,
                "bluemap_commit": FEATURE_BACKPORT_COMMIT,
                "bluemap_api_commit": FEATURE_BACKPORT_API_COMMIT,
            },
            "published Connected Glass-style Adapter API provenance",
        )
        require_absent(
            ("host", "bluemap"), "alternate BlueMap host provenance"
        )
        normalized = {
            "section": section_name,
            "repository": ADAPTER_API_REPOSITORY,
            "version": ADAPTER_API_VERSION,
            "tag": ADAPTER_API_TAG,
            "commit": ADAPTER_API_COMMIT,
            "sourceTree": ADAPTER_API_SOURCE_TREE,
            "blueMapCommit": FEATURE_BACKPORT_COMMIT,
            "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
        }
        published_source_only = True
    else:
        normalized = {
            "section": section_name,
            "repository": field(
                section, "repository", "repository", "module_repository"
            ),
            "version": field(section, "version", "version", "module_version"),
            "tag": field(section, "tag", "tag", "module_tag"),
            "commit": field(
                section,
                "commit",
                "release_target_commit",
                "module_release_commit",
                "commit",
            ),
            "sourceTree": field(
                section, "source tree", "source_tree", "module_source_tree"
            ),
        }

    if section_name == "adapter_api_source":
        companion = value.get("render_core_523_migration")
        if not isinstance(companion, dict):
            raise CandidateError(
                f"{component_id}: adapter_api_source requires exact "
                "render_core_523_migration provenance"
            )
        render_core = {
            "section": "render_core_523_migration",
            "repository": field(
                companion, "render-core repository", "module_repository"
            ),
            "version": field(companion, "render-core version", "module_version"),
            "tag": field(companion, "render-core tag", "module_tag"),
            "commit": field(
                companion, "render-core commit", "module_release_commit"
            ),
            "sourceTree": field(
                companion, "render-core source tree", "module_source_tree"
            ),
            "blueMapCommit": field(
                companion, "BlueMap commit", "bluemap_commit"
            ),
            "blueMapApiCommit": field(
                companion, "BlueMap API commit", "bluemap_api_commit"
            ),
            "sourcePackage": field(
                companion, "render-core source package", "source_package"
            ),
        }
        expected_render_core = {
            "repository": "https://github.com/jan-guenter/bluemap-addon-render-core",
            "version": RENDER_CORE_VERSION,
            "tag": RENDER_CORE_TAG,
            "commit": RENDER_CORE_COMMIT,
            "sourceTree": RENDER_CORE_SOURCE_TREE,
            "blueMapCommit": FEATURE_BACKPORT_COMMIT,
            "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
            "sourcePackage": RENDER_CORE_SOURCE_PACKAGE,
        }
        for key, expected_value in expected_render_core.items():
            if render_core[key] != expected_value:
                raise CandidateError(
                    f"{component_id}: render-core migration {key} differs from the exact "
                    "5.23 contract"
                )
        if (
            type(companion.get("compiled_source_count")) is not int
            or companion["compiled_source_count"] != 1
            or companion.get("standalone_module_jar_bundled") is not False
            or companion.get("standalone_module_jar_installed") is not False
        ):
            raise CandidateError(
                f"{component_id}: render-core migration does not prove the exact "
                "source-only module"
            )
        normalized["blueMapCommit"] = render_core["blueMapCommit"]
        normalized["blueMapApiCommit"] = render_core["blueMapApiCommit"]
        normalized["identitySection"] = render_core["section"]
        normalized["renderCore"] = render_core
    elif not published_source_only:
        normalized["blueMapCommit"] = field(
            section, "BlueMap commit", "bluemap_commit", "target_bluemap_commit"
        )
    expected = {
        "repository": ADAPTER_API_REPOSITORY,
        "version": ADAPTER_API_VERSION,
        "tag": ADAPTER_API_TAG,
        "commit": ADAPTER_API_COMMIT,
        "sourceTree": ADAPTER_API_SOURCE_TREE,
        "blueMapCommit": FEATURE_BACKPORT_COMMIT,
    }
    for key, expected_value in expected.items():
        if normalized[key] != expected_value:
            raise CandidateError(
                f"{component_id}: Adapter API migration {key} differs from the exact "
                "5.23 contract"
            )
    target_version = section.get("target_bluemap_version")
    if target_version is not None and target_version != FEATURE_BACKPORT_VERSION:
        raise CandidateError(
            f"{component_id}: Adapter API migration BlueMap version is not exact"
        )
    if not published_source_only:
        optional_standalone_fields = {
            key: section[key]
            for key in (
                "standalone_module_jar_bundled",
                "standalone_module_jar_nested",
            )
            if key in section
        }
        if section.get("standalone_module_jar_installed") is not False or any(
            value is not False for value in optional_standalone_fields.values()
        ):
            raise CandidateError(
                f"{component_id}: Adapter API migration does not prove a source-only module"
            )
    if section_name == "adapter_api_source" and (
        type(section.get("compiled_source_count")) is not int
        or section["compiled_source_count"] != 4
        or section.get("standalone_module_jar_bundled") is not False
    ):
        raise CandidateError(
            f"{component_id}: Adapter API source provenance does not prove the exact "
            "source-only module"
        )
    normalized["standaloneModuleJar"] = "not-bundled-or-installed"
    return normalized


def _native_feature_backport_contract(
    checkout: Path,
    commit: str,
    component_id: str,
    artifact_path: Path,
) -> dict | None:
    paths = _main_java_paths(checkout, commit)
    compatibility_paths = [
        path for path in paths if path.endswith("/AdapterCompatibility.java")
    ]
    if compatibility_paths:
        if len(compatibility_paths) != 1:
            raise CandidateError(
                f"{component_id}: expected at most one AdapterCompatibility.java"
            )
        return None

    adapter_paths = _native_adapter_paths(paths)
    if len(adapter_paths) != 1:
        raise CandidateError(
            f"{component_id}: native feature-backport override must contain exactly one "
            "adapter/bluemap523/BlueMap523Adapter.java"
        )
    entrypoint = discover_entrypoint(checkout, commit)
    entrypoint_source = run(["git", "show", f"{commit}:{entrypoint}"], checkout).stdout
    adapter_source = run(
        ["git", "show", f"{commit}:{adapter_paths[0]}"], checkout
    ).stdout
    migration = _normalize_adapter_api_migration(checkout, commit, component_id)
    direct_runtime_gate = entrypoint_source.count(
        "BlueMapRuntimeCompatibility.matchesCurrent()"
    )
    forwarded_runtime_gate = int(
        entrypoint_source.count("runtimeSupported(BlueMap.VERSION, BlueMap.GIT_HASH)")
        == 1
        and entrypoint_source.count("BlueMapRuntimeCompatibility.matches(") == 1
    )
    requirements = {
        "public synchronized Boolean adapter install": len(
            INSTALL_SIGNATURE.findall(adapter_source)
        ),
        "Runnable BlueMap add-on entrypoint": len(
            ENTRYPOINT_CLASS.findall(entrypoint_source)
        ),
        "5.23 runtime compatibility import": entrypoint_source.count(
            "io.github.janguenter.bluemap.addon.adapter.api.bluemap523."
            "BlueMapRuntimeCompatibility"
        ),
        "5.23 runtime compatibility gate": direct_runtime_gate + forwarded_runtime_gate,
        "reflective install lookup": entrypoint_source.count('getMethod("install")'),
        "reflective install invocation": len(INSTALL_INVOKE.findall(entrypoint_source)),
    }
    invalid = [label for label, count in requirements.items() if count != 1]
    if invalid:
        raise CandidateError(
            f"{component_id}: native feature-backport install contract changed: "
            + ", ".join(invalid)
        )

    gitlink = run(
        ["git", "ls-tree", commit, "--", ADAPTER_API_GITLINK], checkout
    ).stdout.strip()
    expected_gitlink = (
        f"160000 commit {ADAPTER_API_COMMIT}\t{ADAPTER_API_GITLINK}"
    )
    if gitlink != expected_gitlink:
        raise CandidateError(
            f"{component_id}: native feature-backport override does not pin the exact "
            f"Adapter API commit {ADAPTER_API_COMMIT}"
        )
    if migration["section"] == "adapter_api_source":
        render_core_gitlink = run(
            ["git", "ls-tree", commit, "--", RENDER_CORE_GITLINK], checkout
        ).stdout.strip()
        expected_render_core_gitlink = (
            f"160000 commit {RENDER_CORE_COMMIT}\t{RENDER_CORE_GITLINK}"
        )
        if render_core_gitlink != expected_render_core_gitlink:
            raise CandidateError(
                f"{component_id}: native feature-backport override does not pin the exact "
                f"render-core commit {RENDER_CORE_COMMIT}"
            )

    with zipfile.ZipFile(artifact_path, "r") as archive:
        names = archive.namelist()
        class_sha256 = {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in ADAPTER_API_CLASSES
            if name in names
        }
    shared_classes = {
        name
        for name in names
        if name.startswith(ADAPTER_API_CLASS_PREFIX) and name.endswith(".class")
    }
    nested_jars = [name for name in names if name.lower().endswith(".jar")]
    stale_522_classes = [
        name
        for name in names
        if re.search(r"(?:^|/)bluemap522/", name) and name.endswith(".class")
    ]
    if shared_classes != ADAPTER_API_CLASSES:
        raise CandidateError(
            f"{component_id}: native feature-backport artifact does not contain the exact "
            "four-class Adapter API roster"
        )
    invalid_class_bytes = sorted(
        name
        for name, digest in class_sha256.items()
        if digest not in ADAPTER_API_CLASS_SHA256[name]
    )
    if invalid_class_bytes:
        raise CandidateError(
            f"{component_id}: native feature-backport artifact contains unrecognized "
            "Adapter API bytecode"
        )
    if nested_jars:
        raise CandidateError(
            f"{component_id}: native feature-backport artifact contains nested JARs"
        )
    if stale_522_classes:
        raise CandidateError(
            f"{component_id}: native feature-backport artifact contains 5.22-package classes"
        )

    return {
        "blueMapVersion": FEATURE_BACKPORT_VERSION,
        "blueMapCommit": FEATURE_BACKPORT_COMMIT,
        "blueMapApiCommit": FEATURE_BACKPORT_API_COMMIT,
        "adapterApiVersion": ADAPTER_API_VERSION,
        "adapterApiTag": ADAPTER_API_TAG,
        "adapterApiCommit": ADAPTER_API_COMMIT,
        "adapterApiSourceTree": ADAPTER_API_SOURCE_TREE,
        "adapterApiGitlink": ADAPTER_API_GITLINK,
        "adapterApiClassCount": len(ADAPTER_API_CLASSES),
        "adapterApiClassSha256": class_sha256,
        "migrationProvenance": migration,
        "standaloneModuleJarBundled": False,
    }


def load_addon_override_lock(path: Path, manifest: dict) -> dict:
    if not path.is_absolute():
        raise CandidateError("--addon-override-lock must be an absolute path")
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateError(f"cannot read add-on override lock {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CandidateError("add-on override lock must be a JSON object")
    _require_exact_keys(value, {"schemaVersion", "atmons", "components"}, "override lock")
    if (
        type(value["schemaVersion"]) is not int
        or value["schemaVersion"] != 1
        or value["atmons"] != "1.2.0"
    ):
        raise CandidateError("add-on override lock is not ATMons 1.2.0 schema 1")
    entries = value["components"]
    if not isinstance(entries, list) or not entries:
        raise CandidateError("add-on override lock components must be a non-empty array")
    known = {
        component["id"]: component
        for component in manifest["components"]
        if component["kind"] == "addon"
    }
    records: dict[str, dict] = {}
    artifact_paths: set[Path] = set()
    for index, entry in enumerate(entries):
        label = f"override lock component {index}"
        if not isinstance(entry, dict):
            raise CandidateError(f"{label} must be an object")
        _require_exact_keys(entry, {"id", "source", "artifact"}, label)
        component_id = entry["id"]
        if not isinstance(component_id, str) or component_id not in known:
            raise CandidateError(f"{label} has unknown add-on ID {component_id!r}")
        if component_id in records:
            raise CandidateError(f"duplicate add-on override ID: {component_id}")
        source = entry["source"]
        artifact = entry["artifact"]
        if not isinstance(source, dict) or not isinstance(artifact, dict):
            raise CandidateError(f"{component_id}: source and artifact must be objects")
        _require_exact_keys(source, {"checkout", "commit"}, f"{component_id} source")
        _require_exact_keys(
            artifact,
            {"path", "filename", "sizeBytes", "sha256", "version"},
            f"{component_id} artifact",
        )
        checkout_text = source["checkout"]
        source_commit = source["commit"]
        if not isinstance(checkout_text, str) or not Path(checkout_text).is_absolute():
            raise CandidateError(f"{component_id}: source checkout must be an absolute path")
        if not isinstance(source_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", source_commit
        ):
            raise CandidateError(f"{component_id}: source commit must be 40 lowercase hex")
        checkout = Path(checkout_text).resolve()
        if not checkout.is_dir():
            raise CandidateError(f"{component_id}: source checkout does not exist")
        try:
            top_level = Path(
                run(["git", "rev-parse", "--show-toplevel"], checkout).stdout.strip()
            ).resolve()
            actual_commit = run(["git", "rev-parse", "HEAD"], checkout).stdout.strip()
            dirty = run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"], checkout
            ).stdout
        except (OSError, subprocess.SubprocessError, CandidateError) as exc:
            raise CandidateError(
                f"{component_id}: source checkout is not an inspectable Git worktree: {exc}"
            ) from exc
        if top_level != checkout:
            raise CandidateError(
                f"{component_id}: source checkout must name the Git worktree root"
            )
        if actual_commit != source_commit:
            raise CandidateError(
                f"{component_id}: source checkout HEAD {actual_commit} != {source_commit}"
            )
        if dirty:
            raise CandidateError(f"{component_id}: source checkout is not clean")

        artifact_path_text = artifact["path"]
        filename = artifact["filename"]
        size_bytes = artifact["sizeBytes"]
        artifact_sha256 = artifact["sha256"]
        version = artifact["version"]
        if not isinstance(artifact_path_text, str) or not Path(
            artifact_path_text
        ).is_absolute():
            raise CandidateError(f"{component_id}: artifact path must be absolute")
        artifact_path = Path(artifact_path_text).resolve()
        if not artifact_path.is_file():
            raise CandidateError(f"{component_id}: local candidate artifact does not exist")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not filename.endswith(".jar")
            or artifact_path.name != filename
        ):
            raise CandidateError(f"{component_id}: artifact filename/path mismatch")
        if (
            isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or size_bytes < 1
            or artifact_path.stat().st_size != size_bytes
        ):
            raise CandidateError(f"{component_id}: local candidate artifact size mismatch")
        if (
            not isinstance(artifact_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256)
            or sha256(artifact_path) != artifact_sha256
        ):
            raise CandidateError(f"{component_id}: local candidate artifact SHA-256 mismatch")
        if not isinstance(version, str) or not re.fullmatch(
            r"[0-9A-Za-z][0-9A-Za-z._+-]{0,127}", version
        ):
            raise CandidateError(f"{component_id}: local candidate version is invalid")
        if artifact_path in artifact_paths:
            raise CandidateError(f"{component_id}: local candidate artifact path is duplicated")
        _validate_override_jar(artifact_path, component_id, version)
        release_provenance = _validate_override_release_provenance(
            checkout, source_commit, component_id, artifact
        )
        native_feature_backport = _native_feature_backport_contract(
            checkout, source_commit, component_id, artifact_path
        )
        if (
            release_provenance["status"] == "unpublished-migration-candidate"
            and native_feature_backport is None
        ):
            raise CandidateError(
                f"{component_id}: unpublished migration candidate lacks the exact "
                "native 5.23 adapter contract"
            )
        artifact_paths.add(artifact_path)
        records[component_id] = {
            "checkout": checkout,
            "sourceCommit": source_commit,
            "artifactPath": artifact_path,
            "artifact": {
                "filename": filename,
                "sizeBytes": size_bytes,
                "sha256": artifact_sha256,
                "version": version,
            },
            "releaseProvenance": release_provenance,
            "nativeFeatureBackport": native_feature_backport,
        }
    ordered_ids = [component_id for component_id in known if component_id in records]
    return {
        "lockSha256": hashlib.sha256(raw).hexdigest(),
        "componentIds": ordered_ids,
        "records": records,
    }


def patch_compatibility(
    path: Path, version: str, commit: str, component_id: str = "fixture"
) -> str:
    source = path.read_text(encoding="utf-8")
    if "INTEGRATION_CANDIDATE_VERSION" in source:
        raise CandidateError(f"{path}: source already contains a candidate identity")
    declaration_match = CLASS_DECLARATION.search(source)
    if not declaration_match:
        raise CandidateError(f"{path}: unsupported AdapterCompatibility shape")
    constants = (
        "    private static final String INTEGRATION_CANDIDATE_VERSION =\n"
        f"            \"{version}\";\n"
        "    private static final String INTEGRATION_CANDIDATE_COMMIT =\n"
        f"            \"{commit}\";\n"
        "    private static final String INTEGRATION_CANDIDATE_COMPONENT =\n"
        f"            \"{component_id}\";\n\n"
        "    private static boolean integrationCandidateSupported(\n"
        "            String version, String commit\n"
        "    ) {\n"
        "        return INTEGRATION_CANDIDATE_VERSION.equals(version)\n"
        "                && INTEGRATION_CANDIDATE_COMMIT.equals(commit);\n"
        "    }\n\n"
        "    public static void integrationCandidateActivated() {\n"
        "        System.out.println(\"BlueMap ATMons integration candidate activated: \"\n"
        "                + INTEGRATION_CANDIDATE_COMPONENT + \"@\"\n"
        "                + INTEGRATION_CANDIDATE_COMMIT);\n"
        "    }\n\n"
    )
    source = (
        source[: declaration_match.end()]
        + constants
        + source[declaration_match.end() :]
    )
    method_match = SUPPORTED_RETURN.search(source)
    if method_match:
        identity = method_match.group("identity")
        indent = method_match.group("indent")
        replacement = (
            method_match.group("header")
            + indent
            + f"return integrationCandidateSupported(version, {identity})\n"
            + indent
            + "        || "
        )
    else:
        method_match = CURRENT_RUNTIME_RETURN.search(source)
        if not method_match:
            raise CandidateError(f"{path}: unsupported AdapterCompatibility shape")
        indent = method_match.group("indent")
        replacement = (
            method_match.group("header")
            + indent
            + "return integrationCandidateSupported(BlueMap.VERSION, BlueMap.GIT_HASH)\n"
            + indent
            + "        || "
        )
    source = source[: method_match.start()] + replacement + source[method_match.end() :]
    path.write_text(source, encoding="utf-8", newline="\n")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def patch_entrypoint(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    matches = list(INSTALL_INVOKE.finditer(source))
    if len(matches) != 1:
        raise CandidateError(f"{path}: expected one reflective adapter install call")
    match = matches[0]
    indent = match.group("indent")
    replacement = (
        f"{indent}Object integrationCandidateInstallResult = install.invoke(null);\n"
        f"{indent}if (!Boolean.TRUE.equals(integrationCandidateInstallResult)) {{\n"
        f'{indent}    inactive("candidate adapter installation rejected", null);\n'
        f"{indent}    return;\n"
        f"{indent}}}\n"
        f"{indent}AdapterCompatibility.integrationCandidateActivated();"
    )
    source = source[: match.start()] + replacement + source[match.end() :]
    path.write_text(source, encoding="utf-8", newline="\n")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def patch_native_entrypoint(path: Path, component_id: str, commit: str) -> str:
    source = path.read_text(encoding="utf-8")
    matches = list(INSTALL_INVOKE.finditer(source))
    if len(matches) != 1:
        raise CandidateError(f"{path}: expected one reflective adapter install call")
    match = matches[0]
    indent = match.group("indent")
    replacement = (
        f"{indent}Object integrationCandidateInstallResult = install.invoke(null);\n"
        f"{indent}if (!Boolean.TRUE.equals(integrationCandidateInstallResult)) {{\n"
        f'{indent}    inactive("candidate adapter installation rejected", null);\n'
        f"{indent}    return;\n"
        f"{indent}}}\n"
        f'{indent}System.out.println("BlueMap ATMons integration candidate activated: '
        f'{component_id}@{commit}");'
    )
    source = source[: match.start()] + replacement + source[match.end() :]
    path.write_text(source, encoding="utf-8", newline="\n")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def discover_adapter(checkout: Path, commit: str) -> str:
    candidates = sorted(
        path
        for path in _main_java_paths(checkout, commit)
        if path.endswith("/AdapterCompatibility.java")
    )
    if len(candidates) != 1:
        raise CandidateError(
            f"{checkout.name}: expected one main AdapterCompatibility.java, found {len(candidates)}"
        )
    return candidates[0]


def discover_entrypoint(checkout: Path, commit: str) -> str:
    result = run(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", "src/main/java"],
        checkout,
    )
    candidates = sorted(
        path
        for path in result.stdout.splitlines()
        if re.search(r"/BlueMap[A-Za-z0-9]+Addon\.java$", path)
    )
    if len(candidates) != 1:
        raise CandidateError(
            f"{checkout.name}: expected one BlueMap add-on entrypoint, found {len(candidates)}"
        )
    return candidates[0]


def validate_install_contract(
    component_id: str, checkout: Path, commit: str, adapter_path: str, entrypoint: str
) -> None:
    adapter_impl = str(Path(adapter_path).with_name("BlueMap522Adapter.java"))
    adapter_source = run(["git", "show", f"{commit}:{adapter_impl}"], checkout).stdout
    entrypoint_source = run(["git", "show", f"{commit}:{entrypoint}"], checkout).stdout
    requirements = {
        "public synchronized Boolean adapter install": len(
            INSTALL_SIGNATURE.findall(adapter_source)
        ),
        "Runnable BlueMap add-on entrypoint": len(
            ENTRYPOINT_CLASS.findall(entrypoint_source)
        ),
        "runtime compatibility gate": entrypoint_source.count(
            "AdapterCompatibility.currentRuntimeSupported()"
        ),
        "reflective install lookup": entrypoint_source.count('getMethod("install")'),
        "reflective install invocation": len(INSTALL_INVOKE.findall(entrypoint_source)),
    }
    invalid = [label for label, count in requirements.items() if count != 1]
    if invalid:
        raise CandidateError(
            f"{component_id}: candidate install contract changed: " + ", ".join(invalid)
        )


def download_verified(component: dict, cache: Path) -> Path:
    artifact = component["artifact"]
    destination = cache / artifact["filename"]
    if destination.is_file():
        if destination.stat().st_size == artifact["size_bytes"] and sha256(destination) == artifact["sha256"]:
            return destination
        destination.unlink()
    request = urllib.request.Request(
        artifact["url"], headers={"User-Agent": "bluemap-atmons-integration/1"}
    )
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    if temporary.stat().st_size != artifact["size_bytes"] or sha256(temporary) != artifact["sha256"]:
        temporary.unlink(missing_ok=True)
        raise CandidateError(f"{component['id']}: downloaded release artifact identity mismatch")
    temporary.replace(destination)
    return destination


def prepare_component_sources(
    component: dict,
    work_root: Path,
    version: str,
    commit: str,
    source_root: Path | None = None,
    source_commit: str | None = None,
    native_feature_backport: dict | None = None,
) -> tuple[list[Path], list[dict[str, str]]]:
    source_root = source_root or ROOT / component["submodule_path"]
    source_commit = source_commit or component["commit"]
    actual_commit = run(["git", "rev-parse", "HEAD"], source_root).stdout.strip()
    if actual_commit != source_commit:
        raise CandidateError(
            f"{component['id']}: source checkout is {actual_commit}, expected {source_commit}"
        )
    entrypoint_path = discover_entrypoint(source_root, source_commit)
    if native_feature_backport is None:
        adapter_path = discover_adapter(source_root, source_commit)
        validate_install_contract(
            component["id"], source_root, source_commit, adapter_path, entrypoint_path
        )
        source_specs = (("compatibility", adapter_path), ("entrypoint", entrypoint_path))
    else:
        if version != FEATURE_BACKPORT_VERSION or commit != FEATURE_BACKPORT_COMMIT:
            raise CandidateError(
                f"{component['id']}: native feature-backport release can only be tested "
                f"against {FEATURE_BACKPORT_VERSION}@{FEATURE_BACKPORT_COMMIT}"
            )
        source_specs = (("entrypoint", entrypoint_path),)
    prepared: list[Path] = []
    replacements: list[dict[str, str]] = []
    for kind, source_path in source_specs:
        source = run(
            ["git", "show", f"{source_commit}:{source_path}"], source_root
        ).stdout
        package_match = re.search(r"^package\s+([A-Za-z0-9_.]+);", source, re.MULTILINE)
        if not package_match:
            raise CandidateError(
                f"{component['id']}: {kind} package declaration is missing"
            )
        package_path = package_match.group(1).replace(".", "/")
        destination = (
            work_root
            / "sources"
            / component["id"]
            / package_path
            / Path(source_path).name
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8", newline="\n")
        if kind == "compatibility":
            source_sha = patch_compatibility(
                destination, version, commit, component["id"]
            )
        elif native_feature_backport is None:
            source_sha = patch_entrypoint(destination)
        else:
            source_sha = patch_native_entrypoint(
                destination, component["id"], commit
            )
        class_name = f"{package_path}/{Path(source_path).stem}.class"
        prepared.append(destination)
        replacements.append(
            {
                "kind": kind,
                "source": destination.relative_to(work_root).as_posix(),
                "sourceSha256": source_sha,
                "class": class_name,
            }
        )
    return prepared, replacements


def select_component_inputs(
    component: dict,
    released_jar: Path | None,
    override: dict | None,
    released_native_feature_backport: dict | None = None,
) -> dict:
    if override is None:
        if released_jar is None:
            raise CandidateError(
                f"{component['id']}: verified released base JAR is missing"
            )
        selected = {
            "sourceRoot": ROOT / component["submodule_path"],
            "sourceCommit": component["commit"],
            "baseJar": released_jar,
            "gateMode": (
                "released-native-523-entrypoint-overlay"
                if released_native_feature_backport is not None
                else "two-class-surgical-overlay"
            ),
        }
        if released_native_feature_backport is not None:
            selected["nativeFeatureBackport"] = released_native_feature_backport
        return selected
    return {
        "sourceRoot": override["checkout"],
        "sourceCommit": override["sourceCommit"],
        "baseJar": override["artifactPath"],
        "gateMode": (
            "local-native-523-entrypoint-overlay"
            if override["nativeFeatureBackport"] is not None
            else "local-candidate-two-class-surgical-overlay"
        ),
        "nativeFeatureBackport": override["nativeFeatureBackport"],
    }


def compile_adapters(
    sources: list[Path], classes: Path, blue_jar: Path, component_jars: list[Path]
) -> float:
    joml = sorted(
        Path.home().glob(
            ".gradle/caches/modules-2/files-2.1/org.joml/joml/1.10.5/*/joml-1.10.5.jar"
        )
    )
    if not joml:
        raise CandidateError("JOML 1.10.5 is absent from the established Gradle cache")
    classes.mkdir(parents=True, exist_ok=True)
    argument_file = classes.parent / "javac-sources.txt"
    argument_file.write_text("\n".join(str(path) for path in sources) + "\n", encoding="utf-8")
    started = time.monotonic()
    run(
        [
            "javac",
            "--release",
            "21",
            "-encoding",
            "UTF-8",
            "-cp",
            ":".join(str(path) for path in (blue_jar, joml[0], *component_jars)),
            "-d",
            str(classes),
            f"@{argument_file}",
        ],
        timeout=300,
    )
    return time.monotonic() - started


def replace_classes(
    source_jar: Path, destination: Path, replacements: dict[str, Path]
) -> None:
    class_bytes = {name: path.read_bytes() for name, path in replacements.items()}
    with zipfile.ZipFile(source_jar, "r") as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise CandidateError(f"{source_jar.name}: duplicate ZIP entries are unsupported")
        signatures = [
            name
            for name in names
            if re.fullmatch(r"META-INF/[^/]+\.(?:SF|RSA|DSA|EC)", name, re.IGNORECASE)
        ]
        if signatures:
            raise CandidateError(f"{source_jar.name}: signed JAR cannot be surgically rewritten")
        for class_name in replacements:
            if names.count(class_name) != 1:
                raise CandidateError(
                    f"{source_jar.name}: expected one {class_name}, found {names.count(class_name)}"
                )
        with zipfile.ZipFile(destination, "w") as target:
            for info in source.infolist():
                payload = (
                    class_bytes[info.filename]
                    if info.filename in class_bytes
                    else source.read(info.filename)
                )
                target.writestr(info, payload)
    with zipfile.ZipFile(destination, "r") as candidate:
        corrupt = candidate.testzip()
        if corrupt:
            raise CandidateError(f"{destination.name}: corrupt ZIP entry {corrupt}")


def build_surgical_components(
    components: list[dict],
    manifest: dict,
    output: Path,
    work_root: Path,
    candidate_version: str,
    candidate_commit: str,
    addon_overrides: dict[str, dict] | None = None,
) -> list[dict]:
    addon_overrides = addon_overrides or {}
    cache = work_root / "downloads"
    cache.mkdir(parents=True, exist_ok=True)
    blue_component = next(
        component for component in manifest["components"] if component["kind"] == "bluemap"
    )
    blue_jar = download_verified(blue_component, cache)
    released_jars = {
        component["id"]: download_verified(component, cache)
        for component in components
        if component["id"] not in addon_overrides
    }
    prepared_components = []
    for component in components:
        released_jar = released_jars.get(component["id"])
        override = addon_overrides.get(component["id"])
        released_native_feature_backport = (
            _native_feature_backport_contract(
                ROOT / component["submodule_path"],
                component["commit"],
                component["id"],
                released_jar,
            )
            if override is None and released_jar is not None
            else None
        )
        selected = select_component_inputs(
            component,
            released_jar,
            override,
            released_native_feature_backport,
        )
        sources, replacements = prepare_component_sources(
            component,
            work_root,
            candidate_version,
            candidate_commit,
            selected["sourceRoot"],
            selected["sourceCommit"],
            selected.get("nativeFeatureBackport"),
        )
        prepared_components.append(
            (component, override, selected, sources, replacements)
        )
    compile_seconds = compile_adapters(
        [
            source
            for _component, _override, _selected, sources, _replacements in prepared_components
            for source in sources
        ],
        work_root / "classes",
        blue_jar,
        [selected["baseJar"] for _component, _override, selected, _sources, _replacements in prepared_components],
    )
    records = []
    for index, (component, override, selected, _sources, replacements) in enumerate(
        prepared_components, start=1
    ):
        print(f"[{index}/{len(prepared_components)}] {component['id']}", flush=True)
        base_jar = selected["baseJar"]
        class_files = {
            replacement["class"]: work_root / "classes" / replacement["class"]
            for replacement in replacements
        }
        if not all(path.is_file() for path in class_files.values()):
            raise CandidateError(f"{component['id']}: compiled candidate classes are missing")
        identity_class = next(
            class_files[replacement["class"]]
            for replacement in replacements
            if replacement["kind"]
            == (
                "entrypoint"
                if selected.get("nativeFeatureBackport") is not None
                else "compatibility"
            )
        )
        if candidate_commit.encode("ascii") not in identity_class.read_bytes():
            raise CandidateError(f"{component['id']}: compiled candidate identity mismatch")
        destination = output / component["artifact"]["filename"]
        if destination.resolve() == base_jar.resolve():
            raise CandidateError(
                f"{component['id']}: output would overwrite the selected base JAR"
            )
        replace_classes(base_jar, destination, class_files)
        replacement_records = [
            {
                **replacement,
                "classSha256": sha256(class_files[replacement["class"]]),
            }
            for replacement in replacements
        ]
        record = {
            "id": component["id"],
            "sourceCommit": component["commit"],
            "sourceReleaseTag": component["release_tag"],
            "releasedArtifactSha256": component["artifact"]["sha256"],
            "replacements": replacement_records,
            "artifact": {
                "filename": destination.name,
                "sizeBytes": destination.stat().st_size,
                "sha256": sha256(destination),
            },
            "gate": {
                "mode": selected["gateMode"],
                "javacRelease": 21,
                "sharedCompileDurationSeconds": round(compile_seconds, 3),
                "zipIntegrity": "passed",
                "status": "passed",
            },
        }
        if override is not None:
            record["releasedBaseline"] = {
                "sourceCommit": component["commit"],
                "releaseTag": component["release_tag"],
                "artifact": {
                    "filename": component["artifact"]["filename"],
                    "sizeBytes": component["artifact"]["size_bytes"],
                    "sha256": component["artifact"]["sha256"],
                },
            }
            record["localCandidateBase"] = {
                "sourceCommit": override["sourceCommit"],
                "version": override["artifact"]["version"],
                "releaseProvenance": override["releaseProvenance"],
                "artifact": {
                    "filename": override["artifact"]["filename"],
                    "sizeBytes": override["artifact"]["sizeBytes"],
                    "sha256": override["artifact"]["sha256"],
                },
            }
            if override["nativeFeatureBackport"] is not None:
                record["localCandidateBase"]["nativeFeatureBackport"] = override[
                    "nativeFeatureBackport"
                ]
        elif selected.get("nativeFeatureBackport") is not None:
            record["releasedNativeFeatureBackport"] = selected[
                "nativeFeatureBackport"
            ]
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--bluemap-version", required=True)
    parser.add_argument("--bluemap-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--limit", type=int, help="test only the first N add-ons")
    parser.add_argument(
        "--addon-override-lock",
        type=Path,
        help="absolute schema-1 JSON lock for explicit local add-on candidates",
    )
    args = parser.parse_args()

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(args.manifest.resolve())
    components = [component for component in manifest["components"] if component["kind"] == "addon"]
    if args.limit is not None and not 1 <= args.limit <= manifest["release"]["addon_count"]:
        print("ERROR: --limit must be between 1 and the manifest add-on count", file=sys.stderr)
        return 1
    if args.limit:
        components = components[: args.limit]
    partial = len(components) != manifest["release"]["addon_count"]
    try:
        override_lock = (
            load_addon_override_lock(args.addon_override_lock, manifest)
            if args.addon_override_lock is not None
            else None
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if override_lock is not None:
        selected_ids = {component["id"] for component in components}
        excluded = sorted(set(override_lock["componentIds"]) - selected_ids)
        if excluded:
            print(
                "ERROR: --limit excludes requested add-on overrides: "
                + ", ".join(excluded),
                file=sys.stderr,
            )
            return 1
    if not re.fullmatch(r"[0-9a-f]{40}", args.bluemap_commit):
        print("ERROR: --bluemap-commit must be 40 lowercase hex characters", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,127}", args.bluemap_version):
        print("ERROR: --bluemap-version contains unsupported characters", file=sys.stderr)
        return 1

    temporary = args.work_root is None
    work_root = (
        Path(tempfile.mkdtemp(prefix="bluemap-atmons-candidates."))
        if temporary
        else args.work_root.resolve()
    )
    work_root.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": 1,
        "generatedAt": now(),
        "atmons": manifest["atmons"],
        "candidateBlueMap": {
            "version": args.bluemap_version,
            "commit": args.bluemap_commit,
        },
        "components": [],
        "summary": {},
    }
    if override_lock is not None:
        report["localCandidateOverrides"] = {
            "schemaVersion": 1,
            "atmons": "1.2.0",
            "lockSha256": override_lock["lockSha256"],
            "componentIds": override_lock["componentIds"],
        }
    exit_code = 0
    try:
        report["components"] = build_surgical_components(
            components,
            manifest,
            output,
            work_root,
            args.bluemap_version,
            args.bluemap_commit,
            override_lock["records"] if override_lock is not None else None,
        )
        report["summary"] = {
            "componentCount": len(report["components"]),
            "passed": len(report["components"]),
            "status": "partial" if partial else "passed",
            "evidenceMode": "partial-development" if partial else "full-integration",
        }
    except Exception as exc:
        report["error"] = {
            "type": type(exc).__name__,
            "message": "candidate build failed; see stderr for the local diagnostic",
        }
        report["summary"] = {
            "componentCount": len(components),
            "passed": len(report["components"]),
            "status": "failed",
        }
        print(f"ERROR: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        (output / "candidate-manifest.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if temporary and not args.keep_work:
            shutil.rmtree(work_root)
    print(json.dumps(report["summary"], sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
