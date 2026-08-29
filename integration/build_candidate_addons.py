#!/usr/bin/env python3
"""Build staging-only add-on JAR overlays for one exact BlueMap identity.

Published add-ons deliberately reject unknown BlueMap internals. This tool
keeps their released commits and artifacts immutable, compiles only a copied
AdapterCompatibility class with one added candidate identity, rewrites the
entrypoint to require a successful Boolean adapter-install result, replaces
those two classes in verified release JARs, and records every resulting hash. The
ordinary source gates are run separately by ``run_child_gates.py``. Nothing
produced here is published.
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
EXPECTED_MANIFEST_SHA256 = "c181203ddaf4ad353cecf7975af21acb1f55011b5a8c8f1b25bf79a8202db138"
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


def discover_adapter(checkout: Path, commit: str) -> str:
    result = run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            commit,
            "--",
            "src/main/java",
        ],
        checkout,
    )
    candidates = sorted(
        path
        for path in result.stdout.splitlines()
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
    component: dict, work_root: Path, version: str, commit: str
) -> tuple[list[Path], list[dict[str, str]]]:
    source_root = ROOT / component["submodule_path"]
    actual_commit = run(["git", "rev-parse", "HEAD"], source_root).stdout.strip()
    if actual_commit != component["commit"]:
        raise CandidateError(
            f"{component['id']}: submodule is {actual_commit}, expected {component['commit']}"
        )
    adapter_path = discover_adapter(source_root, component["commit"])
    entrypoint_path = discover_entrypoint(source_root, component["commit"])
    validate_install_contract(
        component["id"], source_root, component["commit"], adapter_path, entrypoint_path
    )
    prepared: list[Path] = []
    replacements: list[dict[str, str]] = []
    for kind, source_path in (("compatibility", adapter_path), ("entrypoint", entrypoint_path)):
        source = run(
            ["git", "show", f"{component['commit']}:{source_path}"], source_root
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
        source_sha = (
            patch_compatibility(destination, version, commit, component["id"])
            if kind == "compatibility"
            else patch_entrypoint(destination)
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
) -> list[dict]:
    cache = work_root / "downloads"
    cache.mkdir(parents=True, exist_ok=True)
    blue_component = next(
        component for component in manifest["components"] if component["kind"] == "bluemap"
    )
    blue_jar = download_verified(blue_component, cache)
    released_jars = {
        component["id"]: download_verified(component, cache)
        for component in components
    }
    prepared_components = [
        (component, *prepare_component_sources(component, work_root, candidate_version, candidate_commit))
        for component in components
    ]
    compile_seconds = compile_adapters(
        [
            source
            for _component, sources, _replacements in prepared_components
            for source in sources
        ],
        work_root / "classes",
        blue_jar,
        list(released_jars.values()),
    )
    records = []
    for index, (component, _sources, replacements) in enumerate(
        prepared_components, start=1
    ):
        print(f"[{index}/{len(prepared_components)}] {component['id']}", flush=True)
        released_jar = released_jars[component["id"]]
        class_files = {
            replacement["class"]: work_root / "classes" / replacement["class"]
            for replacement in replacements
        }
        if not all(path.is_file() for path in class_files.values()):
            raise CandidateError(f"{component['id']}: compiled candidate classes are missing")
        compatibility_class = next(
            class_files[replacement["class"]]
            for replacement in replacements
            if replacement["kind"] == "compatibility"
        )
        if candidate_commit.encode("ascii") not in compatibility_class.read_bytes():
            raise CandidateError(f"{component['id']}: compiled candidate identity mismatch")
        destination = output / component["artifact"]["filename"]
        replace_classes(released_jar, destination, class_files)
        replacement_records = [
            {
                **replacement,
                "classSha256": sha256(class_files[replacement["class"]]),
            }
            for replacement in replacements
        ]
        records.append(
            {
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
                    "mode": "two-class-surgical-overlay",
                    "javacRelease": 21,
                    "sharedCompileDurationSeconds": round(compile_seconds, 3),
                    "zipIntegrity": "passed",
                    "status": "passed",
                },
            }
        )
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
    exit_code = 0
    try:
        report["components"] = build_surgical_components(
            components,
            manifest,
            output,
            work_root,
            args.bluemap_version,
            args.bluemap_commit,
        )
        report["summary"] = {
            "componentCount": len(report["components"]),
            "passed": len(report["components"]),
            "status": "partial" if partial else "passed",
            "evidenceMode": "partial-development" if partial else "full-integration",
        }
    except Exception as exc:
        report["error"] = str(exc)
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
