#!/usr/bin/env python3
"""Focused tests for staging compatibility source rewriting."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
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
    print("PASS: candidate add-on source rewriting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
