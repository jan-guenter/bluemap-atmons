#!/usr/bin/env python3
"""Unit checks for runtime-suite response handling."""

from __future__ import annotations

import importlib.util
import hashlib
import inspect
import json
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_runtime_suite.py")
SPEC = importlib.util.spec_from_file_location("runtime_suite", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def candidate_record(released: dict) -> dict:
    return {
        "id": released["id"],
        "sourceCommit": released["commit"],
        "sourceReleaseTag": released["release_tag"],
        "releasedArtifactSha256": released["artifact"]["sha256"],
        "replacements": [
            {
                "kind": "compatibility",
                "source": f"sources/{released['id']}/example/AdapterCompatibility.java",
                "sourceSha256": "1" * 64,
                "class": "example/AdapterCompatibility.class",
                "classSha256": "2" * 64,
            },
            {
                "kind": "entrypoint",
                "source": f"sources/{released['id']}/example/BlueMapFixtureAddon.java",
                "sourceSha256": "3" * 64,
                "class": "example/BlueMapFixtureAddon.class",
                "classSha256": "4" * 64,
            },
        ],
        "artifact": {
            "filename": released["artifact"]["filename"],
            "sizeBytes": 1,
            "sha256": "5" * 64,
        },
        "gate": {
            "mode": "two-class-surgical-overlay",
            "javacRelease": 21,
            "sharedCompileDurationSeconds": 0.1,
            "zipIntegrity": "passed",
            "status": "passed",
        },
    }


def write_candidate_manifest(path: Path, tracked: dict) -> dict:
    addons = [
        component for component in tracked["components"] if component["kind"] == "addon"
    ]
    value = {
        "schemaVersion": 1,
        "atmons": tracked["atmons"],
        "candidateBlueMap": {"version": "candidate", "commit": "0" * 40},
        "components": [candidate_record(component) for component in addons],
        "summary": {
            "componentCount": 51,
            "passed": 51,
            "status": "passed",
            "evidenceMode": "full-integration",
        },
    }
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def expect_suite_error(callback, fragment: str) -> None:
    try:
        callback()
    except MODULE.SuiteError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"invalid runtime candidate state was accepted: {fragment}")


def check_candidate_override_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="bluemap-atmons-runtime-override-") as temporary:
        root = Path(temporary)
        tracked = json.loads(MODULE.TRACKED_MANIFEST.read_text(encoding="utf-8"))
        manifest_path = root / "candidate-manifest.json"
        default_value = write_candidate_manifest(manifest_path, tracked)
        assert MODULE.load_candidate_manifest(manifest_path) == default_value

        released_native_value = json.loads(json.dumps(default_value))
        released_native_record = released_native_value["components"][0]
        released_native_contract = {
            "blueMapVersion": released_native_value["candidateBlueMap"]["version"],
            "blueMapCommit": released_native_value["candidateBlueMap"]["commit"],
            "adapterApiCommit": "8" * 40,
        }
        released_native_record["releasedNativeFeatureBackport"] = (
            released_native_contract
        )
        released_native_record["gate"]["mode"] = (
            "released-native-523-entrypoint-overlay"
        )
        released_native_record["replacements"] = [
            replacement
            for replacement in released_native_record["replacements"]
            if replacement["kind"] == "entrypoint"
        ]
        manifest_path.write_text(
            json.dumps(released_native_value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert MODULE.load_candidate_manifest(manifest_path) == released_native_value

        released_native_mismatch = json.loads(json.dumps(released_native_value))
        released_native_mismatch["candidateBlueMap"]["commit"] = "9" * 40
        manifest_path.write_text(
            json.dumps(released_native_mismatch, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path),
            "native candidate BlueMap identity mismatch",
        )
        manifest_path.write_text(
            json.dumps(default_value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        artifact = root / "bluemap-ae2-addon-0.2.0-alpha.1.jar"
        with zipfile.ZipFile(artifact, "w") as archive:
            archive.writestr(
                "META-INF/MANIFEST.MF",
                "Manifest-Version: 1.0\r\n"
                "Implementation-Version: 0.2.0-alpha.1\r\n\r\n",
            )
            archive.writestr("example/Fixture.class", b"fixture")
        checkout = root / "candidate-source"
        checkout.mkdir()
        (checkout / "README.md").write_text("fixture\n", encoding="utf-8")
        compatibility = checkout / "src/main/java/example/AdapterCompatibility.java"
        compatibility.parent.mkdir(parents=True)
        compatibility.write_text(
            "package example;\npublic final class AdapterCompatibility {}\n",
            encoding="utf-8",
        )
        provenance = checkout / "provenance/release.json"
        provenance.parent.mkdir(parents=True)
        provenance.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "owner-accepted-release-candidate",
                    "version": "0.2.0-alpha.1",
                    "tag": "v0.2.0-alpha.1",
                    "final_release_artifacts": {
                        "production_jar": {
                            "file_name": artifact.name,
                            "size": artifact.stat().st_size,
                            "sha256": MODULE.sha256(artifact),
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
        lock_value = {
            "schemaVersion": 1,
            "atmons": "1.2.0",
            "components": [
                {
                    "id": "ae2",
                    "source": {"checkout": str(checkout), "commit": commit},
                    "artifact": {
                        "path": str(artifact),
                        "filename": artifact.name,
                        "sizeBytes": artifact.stat().st_size,
                        "sha256": MODULE.sha256(artifact),
                        "version": "0.2.0-alpha.1",
                    },
                }
            ],
        }
        lock_path = root / "addon-override-lock.json"
        lock_path.write_text(
            json.dumps(lock_value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lock = MODULE.load_addon_override_lock(lock_path, tracked)
        original_builder_sha256 = MODULE.CANDIDATE_BUILDER_SHA256
        try:
            MODULE.CANDIDATE_BUILDER_SHA256 = "0" * 64
            expect_suite_error(
                lambda: MODULE.load_addon_override_lock(lock_path, tracked),
                "candidate builder differs",
            )
        finally:
            MODULE.CANDIDATE_BUILDER_SHA256 = original_builder_sha256

        override_value = json.loads(json.dumps(default_value))
        released = next(
            component
            for component in tracked["components"]
            if component["id"] == "ae2"
        )
        record = next(
            component
            for component in override_value["components"]
            if component["id"] == "ae2"
        )
        record["gate"]["mode"] = "local-candidate-two-class-surgical-overlay"
        record["releasedBaseline"] = {
            "sourceCommit": released["commit"],
            "releaseTag": released["release_tag"],
            "artifact": {
                "filename": released["artifact"]["filename"],
                "sizeBytes": released["artifact"]["size_bytes"],
                "sha256": released["artifact"]["sha256"],
            },
        }
        record["localCandidateBase"] = {
            "sourceCommit": commit,
            "version": "0.2.0-alpha.1",
            "releaseProvenance": lock["records"]["ae2"]["releaseProvenance"],
            "artifact": {
                "filename": artifact.name,
                "sizeBytes": artifact.stat().st_size,
                "sha256": MODULE.sha256(artifact),
            },
        }
        override_value["localCandidateOverrides"] = {
            "schemaVersion": 1,
            "atmons": "1.2.0",
            "lockSha256": lock["lockSha256"],
            "componentIds": ["ae2"],
        }
        manifest_path.write_text(
            json.dumps(override_value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert MODULE.load_candidate_manifest(manifest_path, lock) == override_value
        serialized = manifest_path.read_text(encoding="utf-8")
        assert str(checkout) not in serialized
        assert str(artifact) not in serialized

        native_lock = json.loads(json.dumps(lock, default=str))
        native_contract = {
            "blueMapVersion": default_value["candidateBlueMap"]["version"],
            "blueMapCommit": default_value["candidateBlueMap"]["commit"],
            "adapterApiCommit": "8" * 40,
        }
        native_lock["records"]["ae2"]["nativeFeatureBackport"] = native_contract
        native_value = json.loads(json.dumps(override_value))
        native_record = next(
            component
            for component in native_value["components"]
            if component["id"] == "ae2"
        )
        native_record["gate"]["mode"] = "local-native-523-entrypoint-overlay"
        native_record["replacements"] = [
            replacement
            for replacement in native_record["replacements"]
            if replacement["kind"] == "entrypoint"
        ]
        native_record["localCandidateBase"][
            "nativeFeatureBackport"
        ] = native_contract
        manifest_path.write_text(
            json.dumps(native_value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert MODULE.load_candidate_manifest(manifest_path, native_lock) == native_value

        mismatched_identity = json.loads(json.dumps(native_value))
        mismatched_identity["candidateBlueMap"]["commit"] = "9" * 40
        manifest_path.write_text(
            json.dumps(mismatched_identity, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path, native_lock),
            "native candidate BlueMap identity mismatch",
        )

        manifest_path.write_text(
            json.dumps(override_value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        invalid_schema = json.loads(json.dumps(override_value))
        invalid_schema["schemaVersion"] = True
        manifest_path.write_text(json.dumps(invalid_schema) + "\n", encoding="utf-8")
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path, lock),
            "not a successful 51-addon",
        )
        invalid_header_schema = json.loads(json.dumps(override_value))
        invalid_header_schema["localCandidateOverrides"]["schemaVersion"] = True
        manifest_path.write_text(
            json.dumps(invalid_header_schema) + "\n", encoding="utf-8"
        )
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path, lock),
            "override schema is invalid",
        )

        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path),
            "no matching --addon-override-lock",
        )
        mismatch = json.loads(json.dumps(override_value))
        mismatch["components"][0]["localCandidateBase"]["artifact"]["sha256"] = "9" * 64
        manifest_path.write_text(json.dumps(mismatch) + "\n", encoding="utf-8")
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path, lock),
            "local base identity mismatch",
        )
        mismatch = json.loads(json.dumps(override_value))
        mismatch["components"][0]["releasedBaseline"]["artifact"]["sha256"] = "8" * 64
        manifest_path.write_text(json.dumps(mismatch) + "\n", encoding="utf-8")
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path, lock),
            "released baseline identity mismatch",
        )

        manifest_path.write_text(
            json.dumps(default_value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        expect_suite_error(
            lambda: MODULE.load_candidate_manifest(manifest_path, lock),
            "supplied for a release-based candidate manifest",
        )
        assert MODULE.load_candidate_manifest(manifest_path) == default_value

        plain_command = MODULE.candidate_reproduction_command(
            default_value["candidateBlueMap"], root / "out", root / "work"
        )
        assert "--addon-override-lock" not in plain_command
        locked_command = MODULE.candidate_reproduction_command(
            override_value["candidateBlueMap"],
            root / "out",
            root / "work",
            lock_path,
        )
        option = locked_command.index("--addon-override-lock")
        assert locked_command[option + 1] == str(lock_path)


def main() -> int:
    assert MODULE.sha256(MODULE.COMPOSER_PATH) == MODULE.COMPOSER_SHA256
    assert MODULE.scoreboard_value("#ae2 has 0 [bma_test]") == 0
    assert MODULE.scoreboard_value("Score is 17") == 17
    assert MODULE.command_failed("Unknown function demo:nope")
    assert not MODULE.command_failed("Executed 42 commands from function demo:ok")
    assert MODULE.DEFAULT_VERIFY_SETTLE_SECONDS == 0.1
    assert MODULE.DEFAULT_COMPLETION_TIMEOUT_SECONDS == 240.0
    check_candidate_override_contract()
    check_trusted_inventory_and_composition()
    check_gallery_lifecycle_order()
    check_restart_hook_required()
    commit = "0" * 40
    active_log = "\n".join(
        f"BlueMap ATMons integration candidate activated: {component}@{commit}"
        for component in ("one", "two")
    )
    assert MODULE.validate_activation_log(active_log, ["one", "two"], commit) == 2
    try:
        MODULE.validate_activation_log(active_log, ["one", "two", "three"], commit)
    except MODULE.SuiteError as exc:
        assert "three" in str(exc) and "adapter-install" in str(exc)
    else:
        raise AssertionError("missing activation marker was accepted")
    try:
        MODULE.validate_activation_log(
            active_log + "\n" + active_log.splitlines()[0], ["one", "two"], commit
        )
    except MODULE.SuiteError as exc:
        assert "extra=" in str(exc)
    else:
        raise AssertionError("duplicate activation marker was accepted")
    try:
        MODULE.validate_activation_log(
            active_log + "\n[main/ERROR] BlueMap Two add-on is inactive: collision.",
            ["one", "two"],
            commit,
        )
    except MODULE.SuiteError as exc:
        assert "inactive diagnostics" in str(exc)
    else:
        raise AssertionError("inactive add-on diagnostic was accepted")
    check_multipart_rcon()
    print("PASS: runtime suite unit checks")
    return 0


def check_trusted_inventory_and_composition() -> None:
    with tempfile.TemporaryDirectory(prefix="bluemap-atmons-runtime-test-") as temporary:
        root = Path(temporary)
        inventory = root / "base.tsv"
        rows = [
            f"mod{index:03d}.jar\t{index + 1}\t{hashlib.sha256(str(index).encode()).hexdigest()}"
            for index in range(MODULE.SERVER_ARCHIVE_MOD_COUNT)
        ]
        inventory.write_text(
            "# schema=bluemap-atmons-server-mod-inventory-v1\n"
            f"# serverArchiveSizeBytes={MODULE.SERVER_ARCHIVE_SIZE}\n"
            f"# serverArchiveSha256={MODULE.SERVER_ARCHIVE_SHA256}\n"
            + "\n".join(rows)
            + "\n",
            encoding="utf-8",
        )
        try:
            MODULE.load_trusted_base_inventory(inventory)
        except MODULE.SuiteError as exc:
            assert "canonical ATMons 1.2.0 inventory" in str(exc)
        else:
            raise AssertionError("unreviewed trusted-base inventory was accepted")
        original_inventory_sha256 = MODULE.TRUSTED_BASE_INVENTORY_SHA256
        try:
            MODULE.TRUSTED_BASE_INVENTORY_SHA256 = MODULE.sha256(inventory)
            loaded, file_digest = MODULE.load_trusted_base_inventory(inventory)
            assert len(loaded) == MODULE.SERVER_ARCHIVE_MOD_COUNT
            assert file_digest == MODULE.sha256(inventory)
        finally:
            MODULE.TRUSTED_BASE_INVENTORY_SHA256 = original_inventory_sha256

        composition_id = "a" * 64
        layout = root / "gallery-layout.json"
        layout.write_text("{}\n", encoding="utf-8")
        datapack = root / "bluemap-atmons-galleries.zip"
        with zipfile.ZipFile(datapack, "w") as archive:
            archive.writestr(
                "data/bluemap_atmons/function/identity.mcfunction",
                f'data modify storage demo composition set value "{composition_id}"\n',
            )
        composition = root / "gallery-composition-manifest.json"
        composition.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "compositionId": composition_id,
                    "composerVersion": "2.4.0",
                    "sourceManifestSha256": MODULE.sha256(MODULE.TRACKED_MANIFEST),
                    "options": {
                        "minimumY": 195,
                        "originX": 8192,
                        "originZ": 8192,
                        "padding": 8,
                        "rowWidth": 1024,
                    },
                    "layout": {
                        "filename": layout.name,
                        "sizeBytes": layout.stat().st_size,
                        "sha256": MODULE.sha256(layout),
                    },
                    "datapack": {
                        "filename": datapack.name,
                        "sizeBytes": datapack.stat().st_size,
                        "sha256": MODULE.sha256(datapack),
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        verified = MODULE.validate_composition_manifest(
            composition, layout, {"compositionId": composition_id}, datapack
        )
        assert verified["manifestSha256"] == MODULE.sha256(composition)


def check_gallery_lifecycle_order() -> None:
    class RecordingTransport:
        def __init__(self) -> None:
            self.commands: list[str] = []
            self.failure_scores = {"#one": 6, "#two": 4}

        def command(self, command: str) -> str:
            self.commands.append(command)
            if command.startswith("scoreboard players get"):
                player = command.split()[3]
                objective = command.split()[4]
                value = (
                    1
                    if objective == "bma_done"
                    else self.failure_scores[player]
                )
                return f"{player} has {value} [{objective}]\n"
            if command.startswith("scoreboard players set"):
                player = command.split()[3]
                objective = command.split()[4]
                value = int(command.split()[5])
                assert objective == "bma_test" and value == 0
                self.failure_scores[player] = value
                return f"Set {player} {objective} to {value}\n"
            if command.startswith("function "):
                return f"Running {command}\n"
            return "Saved the game\n"

        def close(self) -> None:
            return

    galleries = []
    for identifier in ("one", "two"):
        player = f"#{identifier}"
        galleries.append(
            {
                "id": identifier,
                "functions": {
                    "prepare": f"demo:prepare_{identifier}",
                    "build": f"demo:build_{identifier}",
                    "verify": f"demo:verify_{identifier}",
                    "release": f"demo:release_{identifier}",
                },
                "completion": {
                    "objective": "bma_done",
                    "player": player,
                    "mode": "scheduled-game-tick-barrier",
                },
                "verification": {
                    "objective": "bma_test",
                    "failurePlayer": player,
                    "mirroredChecks": 3,
                },
            }
        )
    transport = RecordingTransport()
    result = {"preflight": {}, "galleries": []}
    MODULE.run_gallery_cycles(transport, {"galleries": galleries}, result, 0, 1, 0)
    assert transport.commands == [
        "function bluemap_atmons:prepare",
        "function demo:prepare_one",
        "function demo:build_one",
        "scoreboard players get #one bma_done",
        "scoreboard players get #one bma_test",
        "scoreboard players set #one bma_test 0",
        "function demo:verify_one",
        "scoreboard players get #one bma_test",
        "function demo:release_one",
        "function demo:prepare_two",
        "function demo:build_two",
        "scoreboard players get #two bma_done",
        "scoreboard players get #two bma_test",
        "scoreboard players set #two bma_test 0",
        "function demo:verify_two",
        "scoreboard players get #two bma_test",
        "function demo:release_two",
        "save-all flush",
    ]
    assert [record["build"]["status"] for record in result["galleries"]] == [
        "performed",
        "performed",
    ]
    assert [record["verification"]["status"] for record in result["galleries"]] == [
        "passed",
        "passed",
    ]
    assert [
        record["verification"]["preVerificationFailures"]
        for record in result["galleries"]
    ] == [6, 4]
    assert [record["verification"]["failures"] for record in result["galleries"]] == [
        0,
        0,
    ]

    main_source = inspect.getsource(MODULE.main)
    restart = main_source.index("run_restart(restart_command)")
    attested = main_source.index('result["preflight"]["postRestartAttestation"]')
    galleries_started = main_source.index("run_gallery_cycles(")
    assert restart < attested < galleries_started


def check_restart_hook_required() -> None:
    command = [
        sys.executable,
        str(MODULE_PATH),
        "--layout", "missing-layout.json",
        "--composition-manifest", "missing-composition.json",
        "--output", "missing-result.json",
        "--rcon", "127.0.0.1:1",
        "--bluemap-commit", "0" * 40,
        "--candidate-manifest", "missing-candidate.json",
        "--bluemap-jar", "missing-bluemap.jar",
        "--harness-jar", "missing-harness.jar",
        "--artifact-exec-prefix-json", '["false"]',
        "--runtime-mods-directory", "/data/mods",
        "--runtime-packs-directory", MODULE.CANONICAL_PACKS_DIRECTORY,
        "--trusted-base-inventory", "missing-inventory.tsv",
        "--datapack-archive", "missing-datapack.zip",
        "--installed-datapack", "/data/world/datapacks/missing.zip",
        "--expected-runtime-jar-count", "377",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    assert completed.returncode == 2
    assert "--restart-exec-json" in completed.stderr
    assert "required" in completed.stderr


def check_multipart_rcon() -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)

    def read_exact(connection: socket.socket, count: int) -> bytes:
        value = bytearray()
        while len(value) < count:
            value.extend(connection.recv(count - len(value)))
        return bytes(value)

    def read_packet(connection: socket.socket) -> tuple[int, int, str]:
        length = struct.unpack("<i", read_exact(connection, 4))[0]
        payload = read_exact(connection, length)
        request_id, kind = struct.unpack("<ii", payload[:8])
        return request_id, kind, payload[8:-2].decode()

    def packet(request_id: int, kind: int, body: str) -> bytes:
        payload = struct.pack("<ii", request_id, kind) + body.encode() + b"\0\0"
        return struct.pack("<i", len(payload)) + payload

    def server() -> None:
        connection, _address = listener.accept()
        with connection:
            auth_id, auth_kind, _password = read_packet(connection)
            assert auth_kind == 3
            connection.sendall(packet(auth_id, 2, ""))
            command_id, command_kind, command = read_packet(connection)
            connection.sendall(packet(command_id, 0, "A" * 4096))
            barrier_id, barrier_kind, barrier = read_packet(connection)
            assert command_kind == 2 and command == "help"
            assert barrier_kind == 2 and barrier == "list"
            connection.sendall(packet(command_id, 0, "B" * 100))
            connection.sendall(packet(barrier_id, 0, ""))

    thread = threading.Thread(target=server)
    thread.start()
    try:
        transport = MODULE.RconTransport(
            "127.0.0.1", listener.getsockname()[1], "secret", 5.0
        )
        try:
            assert transport.command("help") == "A" * 4096 + "B" * 100
        finally:
            transport.close()
    finally:
        thread.join(timeout=5)
        listener.close()
    assert not thread.is_alive()


if __name__ == "__main__":
    raise SystemExit(main())
