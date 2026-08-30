#!/usr/bin/env python3
"""Focused tests for staging compatibility source rewriting."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_candidate_addons.py")
SPEC = importlib.util.spec_from_file_location("candidate_builder", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


SOURCE = """package example;

public final class AdapterCompatibility {
    private static final String OLD = "old";

    static boolean supported(String version, String commit) {
        return OLD.equals(version) && OLD.equals(commit);
    }
}
"""

LEGACY_SOURCE = """package example;

import de.bluecolored.bluemap.core.BlueMap;

public final class AdapterCompatibility {
    public static boolean currentRuntimeSupported() {
        return ("5.22".equals(BlueMap.VERSION)
                && "old".equals(BlueMap.GIT_HASH));
    }
}
"""

ENTRYPOINT_SOURCE = """package example;

import java.lang.reflect.Method;

public final class BlueMapFixtureAddon implements Runnable {
    public void run() {
        try {
            if (!AdapterCompatibility.currentRuntimeSupported()) {
                inactive("unsupported", null);
                return;
            }
            Method install = BlueMap522Adapter.class.getMethod("install");
            install.invoke(null);
        } catch (ReflectiveOperationException exception) {
            inactive("adapter unavailable", exception);
        }
    }

    private static void inactive(String reason, Throwable cause) {
    }
}
"""

ADAPTER_SOURCE = """package example;

public final class BlueMap522Adapter {
    private BlueMap522Adapter() {
    }

    public static synchronized boolean install() {
        return true;
    }
}
"""


def create_checkout(root: Path, artifact: Path, version: str) -> tuple[Path, str]:
    checkout = root / "addon"
    source_root = checkout / "src/main/java/example"
    source_root.mkdir(parents=True)
    (source_root / "AdapterCompatibility.java").write_text(
        SOURCE, encoding="utf-8"
    )
    (source_root / "BlueMapFixtureAddon.java").write_text(
        ENTRYPOINT_SOURCE, encoding="utf-8"
    )
    (source_root / "BlueMap522Adapter.java").write_text(
        ADAPTER_SOURCE, encoding="utf-8"
    )
    provenance = checkout / "provenance/release.json"
    provenance.parent.mkdir(parents=True)
    provenance.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "owner-accepted-release-candidate",
                "version": version,
                "tag": f"v{version}",
                "final_release_artifacts": {
                    "production_jar": {
                        "file_name": artifact.name,
                        "size": artifact.stat().st_size,
                        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    }
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    subprocess.run(
        ["git", "-C", str(checkout), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(checkout), "config", "user.name", "test"], check=True
    )
    subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(checkout), "commit", "-qm", "fixture"], check=True
    )
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    return checkout, commit


def write_jar(path: Path, version: str = "0.2.0-alpha.1", payload: bytes = b"fixture") -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "META-INF/MANIFEST.MF",
            "Manifest-Version: 1.0\r\n"
            f"Implementation-Version: {version}\r\n\r\n",
        )
        archive.writestr("example/Fixture.class", payload)


def expect_override_error(path: Path, manifest: dict, fragment: str) -> None:
    try:
        MODULE.load_addon_override_lock(path, manifest)
    except MODULE.CandidateError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"invalid override lock was accepted: {fragment}")


def check_override_lock() -> None:
    with tempfile.TemporaryDirectory(prefix="bluemap-atmons-override-test-") as temporary:
        root = Path(temporary)
        artifact = root / "bluemap-fixture-addon-0.2.0-alpha.1.jar"
        write_jar(artifact)
        original_artifact = artifact.read_bytes()
        checkout, commit = create_checkout(root, artifact, "0.2.0-alpha.1")
        manifest = {
            "components": [
                {
                    "id": "fixture",
                    "kind": "addon",
                    "submodule_path": "addons/fixture",
                    "commit": "1" * 40,
                }
            ]
        }
        entry = {
            "id": "fixture",
            "source": {"checkout": str(checkout), "commit": commit},
            "artifact": {
                "path": str(artifact),
                "filename": artifact.name,
                "sizeBytes": artifact.stat().st_size,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "version": "0.2.0-alpha.1",
            },
        }
        base = {"schemaVersion": 1, "atmons": "1.2.0", "components": [entry]}
        lock_path = root / "override-lock.json"

        def write(value: dict) -> None:
            lock_path.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        def changed(callback) -> dict:
            value = json.loads(json.dumps(base))
            callback(value)
            return value

        write(base)
        loaded = MODULE.load_addon_override_lock(lock_path, manifest)
        assert loaded["componentIds"] == ["fixture"]
        assert loaded["records"]["fixture"]["sourceCommit"] == commit
        assert loaded["records"]["fixture"]["artifactPath"] == artifact
        assert loaded["records"]["fixture"]["releaseProvenance"]["path"] == (
            "provenance/release.json"
        )
        assert loaded["lockSha256"] == hashlib.sha256(lock_path.read_bytes()).hexdigest()

        released_jar = root / "released.jar"
        selected = MODULE.select_component_inputs(
            manifest["components"][0], released_jar, None
        )
        assert selected == {
            "sourceRoot": MODULE.ROOT / "addons/fixture",
            "sourceCommit": "1" * 40,
            "baseJar": released_jar,
            "gateMode": "two-class-surgical-overlay",
        }
        candidate = MODULE.select_component_inputs(
            manifest["components"][0],
            released_jar,
            loaded["records"]["fixture"],
        )
        assert candidate["sourceRoot"] == checkout
        assert candidate["sourceCommit"] == commit
        assert candidate["baseJar"] == artifact
        assert candidate["gateMode"] == "local-candidate-two-class-surgical-overlay"

        write(changed(lambda value: value["components"][0].__setitem__("id", "unknown")))
        expect_override_error(lock_path, manifest, "unknown add-on ID")

        write(changed(lambda value: value.__setitem__("schemaVersion", True)))
        expect_override_error(lock_path, manifest, "schema 1")

        duplicate = json.loads(json.dumps(base))
        duplicate["components"].append(json.loads(json.dumps(entry)))
        write(duplicate)
        expect_override_error(lock_path, manifest, "duplicate add-on override ID")

        write(
            changed(
                lambda value: value["components"][0]["artifact"].__setitem__(
                    "sha256", "0" * 64
                )
            )
        )
        expect_override_error(lock_path, manifest, "SHA-256 mismatch")

        write(
            changed(
                lambda value: value["components"][0]["artifact"].__setitem__(
                    "sizeBytes", artifact.stat().st_size + 1
                )
            )
        )
        expect_override_error(lock_path, manifest, "size mismatch")

        write(
            changed(
                lambda value: value["components"][0]["source"].__setitem__(
                    "commit", "0" * 40
                )
            )
        )
        expect_override_error(lock_path, manifest, "source checkout HEAD")

        write(
            changed(
                lambda value: value["components"][0]["source"].__setitem__(
                    "checkout", "relative/checkout"
                )
            )
        )
        expect_override_error(lock_path, manifest, "checkout must be an absolute path")

        write(
            changed(
                lambda value: value["components"][0]["artifact"].__setitem__(
                    "path", "relative/candidate.jar"
                )
            )
        )
        expect_override_error(lock_path, manifest, "artifact path must be absolute")

        write(base)
        (checkout / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        expect_override_error(lock_path, manifest, "source checkout is not clean")
        (checkout / "untracked.txt").unlink()

        write_jar(artifact, version="9.9.9")
        manifest_mismatch = json.loads(json.dumps(base))
        manifest_mismatch["components"][0]["artifact"]["sizeBytes"] = artifact.stat().st_size
        manifest_mismatch["components"][0]["artifact"]["sha256"] = hashlib.sha256(
            artifact.read_bytes()
        ).hexdigest()
        write(manifest_mismatch)
        expect_override_error(lock_path, manifest, "manifest version mismatch")
        artifact.write_bytes(original_artifact)

        write_jar(artifact, payload=b"different candidate bytes")
        provenance_mismatch = json.loads(json.dumps(base))
        provenance_mismatch["components"][0]["artifact"]["sizeBytes"] = artifact.stat().st_size
        provenance_mismatch["components"][0]["artifact"]["sha256"] = hashlib.sha256(
            artifact.read_bytes()
        ).hexdigest()
        write(provenance_mismatch)
        expect_override_error(lock_path, manifest, "differs from exact source provenance")
        artifact.write_bytes(original_artifact)

        artifact.write_bytes(b"not a zip")
        corrupt = json.loads(json.dumps(base))
        corrupt["components"][0]["artifact"]["sizeBytes"] = artifact.stat().st_size
        corrupt["components"][0]["artifact"]["sha256"] = hashlib.sha256(
            artifact.read_bytes()
        ).hexdigest()
        write(corrupt)
        expect_override_error(lock_path, manifest, "not a readable JAR")

        cli = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--bluemap-version",
                "candidate",
                "--bluemap-commit",
                "0" * 40,
                "--output",
                str(root / "cli-output"),
                "--addon-override-lock",
                "relative-lock.json",
            ],
            cwd=MODULE.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert cli.returncode == 1
        assert "Traceback" not in cli.stdout
        assert "--addon-override-lock must be an absolute path" in cli.stdout


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "AdapterCompatibility.java"
        path.write_text(SOURCE, encoding="utf-8")
        digest = MODULE.patch_compatibility(
            path,
            "5.22-feature.backport-5.23-stateless-java-web-server-45",
            "07a4293fd95f1fcee799a1aa69e564f38f00e699",
        )
        patched = path.read_text(encoding="utf-8")
        assert len(digest) == 64
        assert "INTEGRATION_CANDIDATE_VERSION" in patched
        assert "integrationCandidateSupported(version, commit)" in patched
        assert "BlueMap ATMons integration candidate activated:" in patched
        assert "|| OLD.equals(version)" in patched
        entrypoint = Path(directory) / "BlueMapFixtureAddon.java"
        entrypoint.write_text(ENTRYPOINT_SOURCE, encoding="utf-8")
        MODULE.patch_entrypoint(entrypoint)
        patched_entrypoint = entrypoint.read_text(encoding="utf-8")
        assert "Object integrationCandidateInstallResult = install.invoke(null);" in patched_entrypoint
        assert "!Boolean.TRUE.equals(integrationCandidateInstallResult)" in patched_entrypoint
        assert 'inactive("candidate adapter installation rejected", null);' in patched_entrypoint
        assert "AdapterCompatibility.integrationCandidateActivated();" in patched_entrypoint
        path.write_text(LEGACY_SOURCE, encoding="utf-8")
        MODULE.patch_compatibility(path, "candidate-version", "candidate-commit")
        legacy_patched = path.read_text(encoding="utf-8")
        assert "integrationCandidateSupported(BlueMap.VERSION, BlueMap.GIT_HASH)" in legacy_patched
        assert '|| ("5.22".equals(BlueMap.VERSION)' in legacy_patched

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        checkout = root / "addon"
        adapter = (
            checkout
            / "src/main/java/example/AdapterCompatibility.java"
        )
        entrypoint = checkout / "src/main/java/example/BlueMapFixtureAddon.java"
        adapter_impl = checkout / "src/main/java/example/BlueMap522Adapter.java"
        adapter.parent.mkdir(parents=True)
        adapter.write_text(SOURCE, encoding="utf-8")
        entrypoint.write_text(ENTRYPOINT_SOURCE, encoding="utf-8")
        adapter_impl.write_text(ADAPTER_SOURCE, encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        subprocess.run(
            ["git", "-C", str(checkout), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(checkout), "config", "user.name", "test"], check=True
        )
        subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(checkout), "commit", "-qm", "fixture"], check=True
        )
        commit = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        adapter.write_text("dirty working-tree content\n", encoding="utf-8")
        original_root = MODULE.ROOT
        MODULE.ROOT = root
        try:
            prepared, replacements = MODULE.prepare_component_sources(
                {"id": "fixture", "submodule_path": "addon", "commit": commit},
                root / "work",
                "candidate-version",
                "candidate-commit",
            )
        finally:
            MODULE.ROOT = original_root
        assert len(prepared) == 2
        assert {item["kind"] for item in replacements} == {"compatibility", "entrypoint"}
        compatibility = next(path for path in prepared if path.name == "AdapterCompatibility.java")
        patched_entrypoint = next(path for path in prepared if path.name == "BlueMapFixtureAddon.java")
        assert "dirty working-tree content" not in compatibility.read_text(encoding="utf-8")
        assert "INTEGRATION_CANDIDATE_VERSION" in compatibility.read_text(encoding="utf-8")
        assert "integrationCandidateInstallResult" in patched_entrypoint.read_text(encoding="utf-8")
    check_override_lock()
    print("PASS: candidate add-on source rewriting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
