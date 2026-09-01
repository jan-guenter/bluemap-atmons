#!/usr/bin/env python3
"""Build and verify all composed galleries against one running ATMons server."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shlex
import socket
import struct
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
TRACKED_MANIFEST = ROOT / "versions" / "1.2.0" / "manifest.json"
TRACKED_MANIFEST_SHA256 = "04345f7966745ec5f659e0780d682aa72dc2f3ad61d967f8a20f3afa910c3065"
COMPOSER_PATH = ROOT / "integration" / "galleries" / "compose.py"
COMPOSER_VERSION = "2.4.1"
COMPOSER_SHA256 = "d0b685f3ab4dafec4c0985117ed687e76e5232365587915dda520b8a5266c71b"
CANDIDATE_BUILDER_PATH = ROOT / "integration" / "build_candidate_addons.py"
CANDIDATE_BUILDER_SHA256 = "bcc9186c17b835a681e1ab26c57c79477dde124eeee1c12396beedda2acaf0e6"
EXPECTED_COMPOSITION_OPTIONS = {
    "minimumY": 195,
    "originX": 8192,
    "originZ": 8192,
    "padding": 8,
    "rowWidth": 1024,
}

ERROR_MARKERS = (
    "unknown function",
    "unknown or incomplete command",
    "no function was run",
    "incorrect argument",
    "expected whitespace",
    "command failed",
)
DEFAULT_VERIFY_SETTLE_SECONDS = 0.1
DEFAULT_COMPLETION_TIMEOUT_SECONDS = 240.0
SERVER_ARCHIVE_SHA256 = "de112ed8d79b3ff027e399a5108b706f6a2db3be74b15d0db6f6b9d6ac268e6c"
SERVER_ARCHIVE_SIZE = 1_055_896_389
SERVER_ARCHIVE_MOD_COUNT = 375
TRUSTED_BASE_INVENTORY_SHA256 = "aba2db94fbcd6cf756d6ab2f03e7adc35422d4a2c1eb82e47d998ed740e4d70c"
INACTIVE_ADDON_PATTERN = re.compile(
    r"^.*\bBlueMap [^\r\n]* add-on (?:is )?inactive:", re.IGNORECASE | re.MULTILINE
)
ACTIVATION_PATTERN = re.compile(
    r"BlueMap ATMons integration candidate activated: "
    r"(?P<id>[a-z0-9][a-z0-9-]*)@(?P<commit>[0-9a-f]{40})(?=\s|$)"
)
CANONICAL_RUNTIME_LOG = "/data/logs/latest.log"
CANONICAL_PACKS_DIRECTORY = "/data/config/bluemap/packs"
class SuiteError(RuntimeError):
    pass


class Transport(Protocol):
    def command(self, command: str) -> str: ...

    def close(self) -> None: ...


class RconTransport:
    def __init__(self, host: str, port: int, password: str, timeout: float) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.socket: socket.socket | None = None
        self.request_id = 0x424D40
        self.connect()

    def connect(self) -> None:
        self.close()
        sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        sock.settimeout(self.timeout)
        self.socket = sock
        request_id = self._next_request_id()
        self._send(request_id, 3, self.password)
        response_id, response_type, _body = self._read_packet()
        if response_id == -1:
            self.close()
            raise SuiteError("RCON authentication failed")
        if response_type != 2:
            response_id, response_type, _body = self._read_packet()
        if response_id != request_id or response_type != 2:
            self.close()
            raise SuiteError(
                f"RCON authentication response ID {response_id} != {request_id}"
            )

    def _next_request_id(self) -> int:
        self.request_id += 1
        if self.request_id > 0x7FFFFFF0:
            self.request_id = 1
        return self.request_id

    @staticmethod
    def _packet(request_id: int, kind: int, body: str) -> bytes:
        payload = struct.pack("<ii", request_id, kind) + body.encode("utf-8") + b"\0\0"
        return struct.pack("<i", len(payload)) + payload

    def _send(self, request_id: int, kind: int, body: str) -> None:
        if self.socket is None:
            raise SuiteError("RCON socket is closed")
        self.socket.sendall(self._packet(request_id, kind, body))

    def _read_exact(self, count: int) -> bytes:
        if self.socket is None:
            raise SuiteError("RCON socket is closed")
        chunks = bytearray()
        while len(chunks) < count:
            chunk = self.socket.recv(count - len(chunks))
            if not chunk:
                raise SuiteError("RCON connection closed during response")
            chunks.extend(chunk)
        return bytes(chunks)

    def _read_packet(self) -> tuple[int, int, str]:
        length = struct.unpack("<i", self._read_exact(4))[0]
        if length < 10 or length > 4 * 1024 * 1024:
            raise SuiteError(f"invalid RCON response length: {length}")
        payload = self._read_exact(length)
        response_id, response_type = struct.unpack("<ii", payload[:8])
        return response_id, response_type, payload[8:-2].decode("utf-8", errors="replace")

    def command(self, command: str) -> str:
        if self.socket is None:
            # A new command after an explicit close/restart may establish a
            # fresh connection. A command that was already sent is never replayed.
            self.connect()
        try:
            command_id = self._next_request_id()
            barrier_id = self._next_request_id()
            self._send(command_id, 2, command)
            response_id, response_type, body = self._read_packet()
            if response_id != command_id or response_type != 0:
                raise SuiteError(
                    f"unexpected first RCON response {response_id}/{response_type}; "
                    f"expected {command_id}/0"
                )
            # Minecraft processes packets serially. A distinct, read-only
            # command is therefore a reliable barrier after every split
            # command-response packet, including responses larger than 4096 B.
            # Send it only after receiving the first response packet: the
            # 1.21.1 server rejects pipelined command packets and closes the
            # connection for an empty command.
            self._send(barrier_id, 2, "list")
            bodies = [body]
            while True:
                response_id, response_type, body = self._read_packet()
                if response_type != 0:
                    raise SuiteError(
                        f"unexpected RCON response type {response_type}; expected 0"
                    )
                if response_id == command_id:
                    bodies.append(body)
                    continue
                if response_id == barrier_id:
                    return "".join(bodies)
                raise SuiteError(
                    f"unexpected RCON response ID {response_id}; expected "
                    f"{command_id} or barrier {barrier_id}"
                )
        except (OSError, SuiteError):
            self.close()
            raise

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None


class ExecTransport:
    def __init__(self, prefix: list[str], timeout: float) -> None:
        if not prefix:
            raise SuiteError("exec transport prefix is empty")
        self.prefix = prefix
        self.timeout = timeout

    def command(self, command: str) -> str:
        result = subprocess.run(
            [*self.prefix, command],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=self.timeout,
        )
        if result.returncode:
            raise SuiteError(
                f"command transport exited {result.returncode}: {result.stdout.strip()}"
            )
        return result.stdout.strip()

    def close(self) -> None:
        return


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def digest_inventory(inventory: dict[str, dict[str, int | str]]) -> str:
    digest = hashlib.sha256()
    for name in sorted(inventory):
        digest.update(
            f"{name}\t{inventory[name]['sizeBytes']}\t{inventory[name]['sha256']}\n".encode(
                "utf-8"
            )
        )
    return digest.hexdigest()


def require_pinned_manifest() -> None:
    if sha256(TRACKED_MANIFEST) != TRACKED_MANIFEST_SHA256:
        raise SuiteError(
            "tracked ATMons 1.2.0 manifest differs from its immutable released-profile digest"
        )


def load_addon_override_lock(path: Path, tracked: dict) -> dict:
    if sha256(CANDIDATE_BUILDER_PATH) != CANDIDATE_BUILDER_SHA256:
        raise SuiteError("candidate builder differs from its reviewed immutable digest")
    spec = importlib.util.spec_from_file_location(
        "bluemap_atmons_candidate_builder", CANDIDATE_BUILDER_PATH
    )
    if spec is None or spec.loader is None:
        raise SuiteError("cannot load the pinned candidate builder")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    try:
        return builder.load_addon_override_lock(path, tracked)
    except builder.CandidateError as exc:
        raise SuiteError(str(exc)) from exc


def load_trusted_base_inventory(
    path: Path,
) -> tuple[dict[str, dict[str, int | str]], str]:
    file_sha256 = sha256(path)
    if file_sha256 != TRUSTED_BASE_INVENTORY_SHA256:
        raise SuiteError(
            "trusted base inventory differs from the canonical ATMons 1.2.0 inventory: "
            f"{file_sha256}"
        )
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SuiteError(f"cannot read trusted base inventory {path}: {exc}") from exc
    expected_header = [
        "# schema=bluemap-atmons-server-mod-inventory-v1",
        f"# serverArchiveSizeBytes={SERVER_ARCHIVE_SIZE}",
        f"# serverArchiveSha256={SERVER_ARCHIVE_SHA256}",
    ]
    if lines[:3] != expected_header:
        raise SuiteError(
            "trusted base inventory is not derived from the exact ATMons 1.2.0 server archive"
        )
    inventory: dict[str, dict[str, int | str]] = {}
    previous = ""
    for line in lines[3:]:
        fields = line.split("\t")
        if (
            len(fields) != 3
            or not fields[0].endswith(".jar")
            or Path(fields[0]).name != fields[0]
            or not fields[1].isdigit()
            or int(fields[1]) < 1
            or not re.fullmatch(r"[0-9a-f]{64}", fields[2])
            or fields[0] <= previous
        ):
            raise SuiteError(f"malformed/unsorted trusted inventory row: {line!r}")
        name, size_text, digest = fields
        inventory[name] = {"sizeBytes": int(size_text), "sha256": digest}
        previous = name
    if len(inventory) != SERVER_ARCHIVE_MOD_COUNT:
        raise SuiteError(
            f"trusted server archive inventory has {len(inventory)} JARs, "
            f"expected {SERVER_ARCHIVE_MOD_COUNT}"
        )
    return inventory, file_sha256


def require_exact_inventory(
    label: str,
    actual: dict[str, dict[str, int | str]],
    expected: dict[str, dict[str, int | str]],
) -> None:
    if actual == expected:
        return
    missing = sorted(set(expected).difference(actual))[:10]
    extra = sorted(set(actual).difference(expected))[:10]
    changed = sorted(
        name for name in set(actual).intersection(expected) if actual[name] != expected[name]
    )[:10]
    raise SuiteError(
        f"{label} inventory differs from trusted inputs; "
        f"missing={missing}, extra={extra}, changed={changed}"
    )


def validate_activation_log(log_text: str, component_ids: list[str], commit: str) -> int:
    inactive_diagnostics = [
        match.group(0).strip() for match in INACTIVE_ADDON_PATTERN.finditer(log_text)
    ]
    if inactive_diagnostics:
        raise SuiteError(
            "add-on inactive diagnostics were emitted after installation: "
            + "; ".join(inactive_diagnostics[:10])
        )
    actual = Counter(
        (match.group("id"), match.group("commit"))
        for match in ACTIVATION_PATTERN.finditer(log_text)
    )
    expected = Counter((component_id, commit) for component_id in component_ids)
    if actual != expected:
        raise SuiteError(
            "successful candidate adapter-install markers are not the exact canonical set; "
            f"missing={sorted((expected - actual).elements())[:10]}, "
            f"extra={sorted((actual - expected).elements())[:10]}"
        )
    return len(component_ids)


def load_candidate_manifest(path: Path, override_lock: dict | None = None) -> dict:
    require_pinned_manifest()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuiteError(f"cannot read candidate manifest {path}: {exc}") from exc
    if (
        type(value.get("schemaVersion")) is not int
        or value.get("schemaVersion") != 1
        or value.get("atmons", {}).get("version") != "1.2.0"
        or value.get("summary", {}).get("status") != "passed"
        or value.get("summary", {}).get("passed") != 51
        or len(value.get("components", [])) != 51
    ):
        raise SuiteError("candidate manifest is not a successful 51-addon ATMons 1.2.0 run")
    try:
        tracked = json.loads(TRACKED_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuiteError(f"cannot read tracked compatibility manifest: {exc}") from exc
    expected = [
        component for component in tracked["components"] if component["kind"] == "addon"
    ]
    candidate_identity = value.get("candidateBlueMap")
    if (
        not isinstance(candidate_identity, dict)
        or not isinstance(candidate_identity.get("version"), str)
        or not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,127}", candidate_identity["version"])
        or not re.fullmatch(r"[0-9a-f]{40}", candidate_identity.get("commit", ""))
    ):
        raise SuiteError("candidate BlueMap identity is invalid")
    override_header = value.get("localCandidateOverrides")
    if override_header is None and override_lock is not None:
        raise SuiteError(
            "--addon-override-lock was supplied for a release-based candidate manifest"
        )
    if override_header is not None and override_lock is None:
        raise SuiteError(
            "candidate manifest uses local add-on candidates but no matching "
            "--addon-override-lock was supplied"
        )
    if override_lock is not None:
        if (
            not isinstance(override_header, dict)
            or type(override_header.get("schemaVersion")) is not int
        ):
            raise SuiteError("candidate manifest add-on override schema is invalid")
        expected_header = {
            "schemaVersion": 1,
            "atmons": "1.2.0",
            "lockSha256": override_lock["lockSha256"],
            "componentIds": override_lock["componentIds"],
        }
        if override_header != expected_header:
            raise SuiteError("candidate manifest add-on override lock identity mismatch")
    components = value["components"]
    if [component.get("id") for component in components] != [
        component["id"] for component in expected
    ]:
        raise SuiteError("candidate components do not equal the canonical ordered add-on set")
    filenames: set[str] = set()
    for candidate, released in zip(components, expected, strict=True):
        override = (
            override_lock["records"].get(released["id"])
            if override_lock is not None
            else None
        )
        artifact = candidate.get("artifact")
        gate = candidate.get("gate")
        replacements = candidate.get("replacements")
        released_native_present = "releasedNativeFeatureBackport" in candidate
        released_native_feature_backport = (
            candidate.get("releasedNativeFeatureBackport")
            if override is None and released_native_present
            else None
        )
        if released_native_present and (
            override is not None
            or not isinstance(released_native_feature_backport, dict)
        ):
            raise SuiteError(
                f"unexpected released native candidate state: {released['id']}"
            )
        native_feature_backport = (
            override.get("nativeFeatureBackport")
            if override is not None
            else released_native_feature_backport
        )
        if native_feature_backport is not None and (
            native_feature_backport.get("blueMapVersion")
            != candidate_identity["version"]
            or native_feature_backport.get("blueMapCommit")
            != candidate_identity["commit"]
        ):
            raise SuiteError(
                f"native candidate BlueMap identity mismatch: {released['id']}"
            )
        expected_gate_mode = (
            "local-native-523-entrypoint-overlay"
            if override is not None and native_feature_backport is not None
            else (
                "released-native-523-entrypoint-overlay"
                if released_native_feature_backport is not None
                else (
                    "local-candidate-two-class-surgical-overlay"
                    if override is not None
                    else "two-class-surgical-overlay"
                )
            )
        )
        expected_replacement_count = 1 if native_feature_backport is not None else 2
        if (
            candidate.get("sourceCommit") != released["commit"]
            or candidate.get("sourceReleaseTag") != released["release_tag"]
            or candidate.get("releasedArtifactSha256") != released["artifact"]["sha256"]
            or not isinstance(artifact, dict)
            or artifact.get("filename") != released["artifact"]["filename"]
            or artifact["filename"] in filenames
            or not isinstance(artifact.get("sizeBytes"), int)
            or artifact["sizeBytes"] < 1
            or not re.fullmatch(r"[0-9a-f]{64}", artifact.get("sha256", ""))
            or not isinstance(gate, dict)
            or gate.get("mode") != expected_gate_mode
            or gate.get("status") != "passed"
            or gate.get("javacRelease") != 21
            or gate.get("zipIntegrity") != "passed"
            or not isinstance(replacements, list)
            or len(replacements) != expected_replacement_count
        ):
            raise SuiteError(f"candidate overlay contract is invalid: {released['id']}")
        if override is None:
            if "releasedBaseline" in candidate or "localCandidateBase" in candidate:
                raise SuiteError(
                    f"unexpected local candidate state: {released['id']}"
                )
        else:
            expected_released_baseline = {
                "sourceCommit": released["commit"],
                "releaseTag": released["release_tag"],
                "artifact": {
                    "filename": released["artifact"]["filename"],
                    "sizeBytes": released["artifact"]["size_bytes"],
                    "sha256": released["artifact"]["sha256"],
                },
            }
            expected_local_base = {
                "sourceCommit": override["sourceCommit"],
                "version": override["artifact"]["version"],
                "releaseProvenance": override["releaseProvenance"],
                "artifact": {
                    "filename": override["artifact"]["filename"],
                    "sizeBytes": override["artifact"]["sizeBytes"],
                    "sha256": override["artifact"]["sha256"],
                },
            }
            if native_feature_backport is not None:
                expected_local_base["nativeFeatureBackport"] = native_feature_backport
            if candidate.get("releasedBaseline") != expected_released_baseline:
                raise SuiteError(
                    f"candidate released baseline identity mismatch: {released['id']}"
                )
            if candidate.get("localCandidateBase") != expected_local_base:
                raise SuiteError(
                    f"candidate local base identity mismatch: {released['id']}"
                )
        filenames.add(artifact["filename"])
        by_kind = {
            replacement.get("kind"): replacement
            for replacement in replacements
            if isinstance(replacement, dict)
        }
        expected_kinds = (
            {"entrypoint"}
            if native_feature_backport is not None
            else {"compatibility", "entrypoint"}
        )
        if set(by_kind) != expected_kinds:
            raise SuiteError(f"candidate replacement classes are invalid: {released['id']}")
        for kind, replacement in by_kind.items():
            source = replacement.get("source", "")
            class_name = replacement.get("class", "")
            expected_source_prefix = f"sources/{released['id']}/"
            expected_source_name = (
                "AdapterCompatibility.java"
                if kind == "compatibility"
                else None
            )
            valid_name = (
                source.endswith("/" + expected_source_name)
                and class_name.endswith("/AdapterCompatibility.class")
                if kind == "compatibility"
                else re.search(r"/BlueMap[A-Za-z0-9]+Addon\.java$", source) is not None
                and re.search(r"/BlueMap[A-Za-z0-9]+Addon\.class$", class_name) is not None
            )
            if (
                not source.startswith(expected_source_prefix)
                or not valid_name
                or not re.fullmatch(r"[0-9a-f]{64}", replacement.get("sourceSha256", ""))
                or not re.fullmatch(r"[0-9a-f]{64}", replacement.get("classSha256", ""))
            ):
                raise SuiteError(
                    f"candidate {kind} replacement identity is invalid: {released['id']}"
                )
    return value


def stable_candidate_manifest(value: dict) -> dict:
    stable = json.loads(json.dumps(value))
    stable.pop("generatedAt", None)
    for component in stable.get("components", []):
        if isinstance(component, dict) and isinstance(component.get("gate"), dict):
            component["gate"].pop("sharedCompileDurationSeconds", None)
    return stable


def candidate_reproduction_command(
    identity: dict,
    output: Path,
    work: Path,
    override_lock_path: Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(CANDIDATE_BUILDER_PATH),
        "--manifest",
        str(TRACKED_MANIFEST),
        "--bluemap-version",
        identity["version"],
        "--bluemap-commit",
        identity["commit"],
        "--output",
        str(output),
        "--work-root",
        str(work),
    ]
    if override_lock_path is not None:
        command.extend(["--addon-override-lock", str(override_lock_path)])
    return command


def reproduce_candidate_overlays(
    path: Path,
    value: dict,
    override_lock_path: Path | None = None,
) -> dict[str, str | int]:
    if sha256(CANDIDATE_BUILDER_PATH) != CANDIDATE_BUILDER_SHA256:
        raise SuiteError("candidate builder differs from its reviewed immutable digest")
    if path.name != "candidate-manifest.json":
        raise SuiteError("candidate manifest does not use its canonical filename")
    identity = value["candidateBlueMap"]
    with tempfile.TemporaryDirectory(
        prefix="bluemap-atmons-runtime-candidates-"
    ) as temporary:
        output = Path(temporary) / "output"
        work = Path(temporary) / "work"
        command = candidate_reproduction_command(
            identity, output, work, override_lock_path
        )
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
        )
        if result.returncode:
            raise SuiteError(
                "independent candidate-overlay build failed: "
                + "\n".join(result.stdout.splitlines()[-80:])
            )
        try:
            reproduced_manifest = json.loads(
                (output / "candidate-manifest.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise SuiteError(f"independent candidate manifest is unreadable: {exc}") from exc
        if stable_candidate_manifest(value) != stable_candidate_manifest(reproduced_manifest):
            raise SuiteError(
                "candidate manifest differs from independent pinned-builder output"
            )
        for component in value["components"]:
            filename = component["artifact"]["filename"]
            supplied = path.parent / filename
            reproduced = output / filename
            if not supplied.is_file() or supplied.read_bytes() != reproduced.read_bytes():
                raise SuiteError(
                    f"candidate overlay {filename} differs from independent pinned-builder output"
                )
    return {
        "status": "passed",
        "builderSha256": CANDIDATE_BUILDER_SHA256,
        "verifiedOverlays": len(value["components"]),
    }


def parse_json_argv(value: str, option: str) -> list[str]:
    try:
        prefix = json.loads(value)
    except json.JSONDecodeError as exc:
        raise SuiteError(f"{option} is not valid JSON: {exc}") from exc
    if not isinstance(prefix, list) or not prefix or not all(
        isinstance(item, str) and item for item in prefix
    ):
        raise SuiteError(f"{option} must decode to a non-empty string array")
    return prefix


def remote_jar_inventory(
    prefix: list[str], directory: str, timeout: float
) -> dict[str, dict[str, int | str]]:
    script = r'''directory=$1
for path in "$directory"/*.jar; do
  test -f "$path"
  name=${path##*/}
  case "$name" in *'\t'*|*'\n'*) exit 71;; esac
  size=$(stat -c %s -- "$path")
  digest=$(sha256sum -- "$path")
  digest=${digest%% *}
  printf '%s\t%s\t%s\n' "$name" "$size" "$digest"
done
'''
    result = subprocess.run(
        [*prefix, "sh", "-ceu", script, "bluemap-atmons-attest", directory],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode:
        raise SuiteError(
            f"runtime artifact inventory exited {result.returncode}: {result.stdout.strip()}"
        )
    inventory: dict[str, dict[str, int | str]] = {}
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or not fields[1].isdigit() or not re.fullmatch(
            r"[0-9a-f]{64}", fields[2]
        ):
            raise SuiteError(f"malformed runtime artifact inventory row: {line!r}")
        name, size_text, digest = fields
        if name in inventory:
            raise SuiteError(f"duplicate runtime artifact filename: {name}")
        inventory[name] = {"sizeBytes": int(size_text), "sha256": digest}
    if not inventory:
        raise SuiteError("runtime artifact inventory is empty")
    return inventory


def remote_text(prefix: list[str], path: str, timeout: float) -> str:
    result = subprocess.run(
        [*prefix, "sh", "-ceu", 'exec cat -- "$1"', "bluemap-atmons-read", path],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode:
        raise SuiteError(f"could not read runtime log {path}: {result.stdout.strip()}")
    return result.stdout


def remote_file_identity(prefix: list[str], path: str, timeout: float) -> dict[str, int | str]:
    script = r'''path=$1
test -f "$path"
size=$(stat -c %s -- "$path")
digest=$(sha256sum -- "$path")
digest=${digest%% *}
printf '%s\t%s\n' "$size" "$digest"
'''
    result = subprocess.run(
        [*prefix, "sh", "-ceu", script, "bluemap-atmons-file", path],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    fields = result.stdout.strip().split("\t")
    if (
        result.returncode
        or len(fields) != 2
        or not fields[0].isdigit()
        or not re.fullmatch(r"[0-9a-f]{64}", fields[1])
    ):
        raise SuiteError(f"could not attest runtime file {path}: {result.stdout.strip()}")
    return {"sizeBytes": int(fields[0]), "sha256": fields[1]}


def remote_runtime_identity(prefix: list[str], timeout: float) -> str:
    script = r'''host=$(hostname)
start=$(sed 's/^.*) //' /proc/1/stat | awk '{print $20}')
printf '%s\t%s\n' "$host" "$start"
'''
    result = subprocess.run(
        [*prefix, "sh", "-ceu", script],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    value = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"[A-Za-z0-9._-]+\t[0-9]+", value):
        raise SuiteError(
            f"could not establish runtime container identity: {value or 'no response'}"
        )
    return value


def wait_runtime_identity_change(
    prefix: list[str], previous: str, timeout: float, command_timeout: float
) -> str:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        try:
            current = remote_runtime_identity(prefix, command_timeout)
            if current != previous:
                return current
        except (OSError, subprocess.TimeoutExpired, SuiteError) as exc:
            last_error = str(exc)
        time.sleep(1)
    detail = f"; last observation: {last_error}" if last_error else ""
    raise SuiteError("runtime container identity did not change after restart" + detail)


def attest_runtime_artifacts(
    candidate_manifest_path: Path,
    candidate_manifest: dict,
    bluemap_jar: Path,
    harness_jar: Path,
    prefix: list[str],
    mods_directory: str,
    packs_directory: str,
    trusted_base_inventory_path: Path,
    runtime_attestation_path: str,
    expected_runtime_jar_count: int,
    candidate_commit: str,
    gallery_composition_id: str,
    composition_manifest_sha256: str,
    gallery_layout_sha256: str,
    gallery_datapack_sha256: str,
    timeout: float,
) -> dict:
    if packs_directory != CANONICAL_PACKS_DIRECTORY:
        raise SuiteError(
            "runtime packs must be attested at the canonical BlueMap pack path "
            + CANONICAL_PACKS_DIRECTORY
        )
    identity = candidate_manifest["candidateBlueMap"]
    if identity.get("commit") != candidate_commit:
        raise SuiteError("candidate manifest BlueMap commit does not match --bluemap-commit")
    expected_packs: dict[str, dict[str, int | str]] = {}
    component_ids: list[str] = []
    for component in candidate_manifest["components"]:
        artifact = component.get("artifact", {})
        name = artifact.get("filename")
        if not isinstance(name, str) or name in expected_packs:
            raise SuiteError("candidate manifest contains an invalid/duplicate artifact filename")
        expected_packs[name] = {
            "sizeBytes": artifact.get("sizeBytes"),
            "sha256": artifact.get("sha256"),
        }
        component_ids.append(component["id"])
    base_inventory, base_inventory_file_sha256 = load_trusted_base_inventory(
        trusted_base_inventory_path
    )
    expected_mods = {
        name: identity
        for name, identity in base_inventory.items()
        if not (name.startswith("bluemap") and name.endswith(".jar"))
    }
    custom_mods: dict[str, dict[str, int | str]] = {}
    for path, label in ((bluemap_jar, "BlueMap"), (harness_jar, "integration harness")):
        if not path.is_file():
            raise SuiteError(f"{label} JAR does not exist: {path}")
        if path.name in expected_mods:
            raise SuiteError(f"duplicate expected runtime artifact filename: {path.name}")
        custom_mods[path.name] = {
            "sizeBytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        expected_mods[path.name] = custom_mods[path.name]

    actual_mods = remote_jar_inventory(prefix, mods_directory, timeout)
    if len(expected_mods) != expected_runtime_jar_count:
        raise SuiteError(
            f"trusted inputs derive {len(expected_mods)} runtime JARs, "
            f"expected exactly {expected_runtime_jar_count}"
        )
    require_exact_inventory("NeoForge runtime", actual_mods, expected_mods)
    actual_packs = remote_jar_inventory(prefix, packs_directory, timeout)
    require_exact_inventory("BlueMap candidate packs", actual_packs, expected_packs)
    inventory_sha256 = digest_inventory(actual_mods)
    pack_inventory_sha256 = digest_inventory(actual_packs)
    attestation_text = remote_text(prefix, runtime_attestation_path, timeout)
    try:
        attestation = json.loads(attestation_text)
    except json.JSONDecodeError as exc:
        raise SuiteError(f"runtime attestation JSON is malformed: {exc}") from exc
    required_attestation = {
        "schemaVersion": 1,
        "atmons": "1.2.0",
        "packCommit": "c7bb230f21d14d26859d0b92548f089b3a493ad9",
        "minecraft": "1.21.1",
        "neoforge": "21.1.248",
        "bluemapVersion": identity["version"],
        "bluemapCommit": candidate_commit,
        "bluemapJarSha256": custom_mods[bluemap_jar.name]["sha256"],
        "candidateManifestSha256": sha256(candidate_manifest_path),
        "galleryCompositionId": gallery_composition_id,
        "galleryCompositionManifestSha256": composition_manifest_sha256,
        "galleryLayoutSha256": gallery_layout_sha256,
        "galleryDatapackSha256": gallery_datapack_sha256,
        "runtimeJarInventorySha256": inventory_sha256,
        "runtimeJarCount": expected_runtime_jar_count,
        "runtimeModsDirectory": mods_directory,
        "baseRuntimeInventorySha256": base_inventory_file_sha256,
        "baseRuntimeJarCount": SERVER_ARCHIVE_MOD_COUNT,
        "candidatePackInventorySha256": pack_inventory_sha256,
        "candidatePackCount": len(expected_packs),
        "candidatePacksDirectory": packs_directory,
        "serverArchiveSha256": SERVER_ARCHIVE_SHA256,
        "serverArchiveSizeBytes": SERVER_ARCHIVE_SIZE,
    }
    if any(attestation.get(key) != value for key, value in required_attestation.items()):
        raise SuiteError("runtime attestation does not match observed artifact inventory")

    return {
        "status": "passed",
        "candidateManifestSha256": sha256(candidate_manifest_path),
        "runtimeJarCount": len(actual_mods),
        "runtimeJarInventorySha256": inventory_sha256,
        "baseRuntimeInventorySha256": base_inventory_file_sha256,
        "baseRuntimeJarCount": len(base_inventory),
        "candidatePackCount": len(actual_packs),
        "candidatePackInventorySha256": pack_inventory_sha256,
        "runtimeAttestationSha256": hashlib.sha256(
            attestation_text.encode("utf-8")
        ).hexdigest(),
        "verifiedCandidateAddons": len(candidate_manifest["components"]),
        "verifiedCustomArtifacts": len(custom_mods) + len(expected_packs),
        "candidateComponentIds": component_ids,
        "bluemap": custom_mods[bluemap_jar.name],
        "harness": custom_mods[harness_jar.name],
    }


def remote_log_snapshot(
    prefix: list[str], path: str, timeout: float
) -> tuple[dt.datetime, str]:
    if path != CANONICAL_RUNTIME_LOG:
        raise SuiteError(
            f"runtime log must be the canonical current-boot path {CANONICAL_RUNTIME_LOG}"
        )
    script = r'''path=$1
test -f "$path"
stat -c %y -- "$path"
exec cat -- "$path"
'''
    result = subprocess.run(
        [*prefix, "sh", "-ceu", script, "bluemap-atmons-log", path],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    first, separator, content = result.stdout.partition("\n")
    match = re.fullmatch(
        r"(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\."
        r"(?P<fraction>\d{1,9}) (?P<zone>[+-]\d{4})",
        first.strip(),
    )
    if result.returncode or not separator or match is None:
        raise SuiteError(f"could not capture canonical runtime log: {result.stdout.strip()}")
    fraction = (match.group("fraction") + "000000")[:6]
    modified = dt.datetime.strptime(
        f"{match.group('date')}.{fraction} {match.group('zone')}",
        "%Y-%m-%d %H:%M:%S.%f %z",
    )
    return modified, content


def attest_activation_log(
    prefix: list[str],
    path: str,
    runtime_identity: dict[str, str],
    component_ids: list[str],
    candidate_commit: str,
    timeout: float,
) -> dict[str, str | int]:
    modified, log_text = remote_log_snapshot(prefix, path, timeout)
    started = dt.datetime.fromisoformat(
        runtime_identity["startedAt"].replace("Z", "+00:00")
    )
    if modified < started:
        raise SuiteError("canonical runtime log predates the live harness boot identity")
    boot_marker = (
        "BlueMap ATMons integration harness boot: "
        f"bootId={runtime_identity['bootId']} "
        f"runtimeAttestationSha256={runtime_identity['runtimeAttestationSha256']}"
    )
    if log_text.count(boot_marker) != 1:
        raise SuiteError("canonical runtime log lacks one exact live harness boot marker")
    marker_count = validate_activation_log(log_text, component_ids, candidate_commit)
    return {
        "status": "passed",
        "path": path,
        "modifiedAt": modified.isoformat(),
        "bootId": runtime_identity["bootId"],
        "activationMarkers": marker_count,
        "sha256": hashlib.sha256(log_text.encode("utf-8")).hexdigest(),
    }


def load_layout(path: Path) -> dict:
    require_pinned_manifest()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuiteError(f"cannot read layout {path}: {exc}") from exc
    if value.get("schemaVersion") != 1 or value.get("runtime", {}).get("atmons") != "1.2.0":
        raise SuiteError("layout is not an ATMons 1.2.0 schema-1 gallery plan")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", value.get("compositionId", ""))
        or value.get("composerVersion") != COMPOSER_VERSION
    ):
        raise SuiteError("layout has no exact composer identity")
    galleries = value.get("galleries")
    if (
        value.get("summary", {}).get("galleryCount") != 51
        or not isinstance(galleries, list)
        or len(galleries) != 51
    ):
        raise SuiteError("layout does not contain exactly 51 galleries")
    try:
        tracked = json.loads(TRACKED_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuiteError(f"cannot read tracked compatibility manifest: {exc}") from exc
    expected_ids = {
        component["id"]
        for component in tracked["components"]
        if component["kind"] == "addon"
    }
    actual_ids = [gallery.get("id") for gallery in galleries if isinstance(gallery, dict)]
    if len(actual_ids) != 51 or set(actual_ids) != expected_ids or len(set(actual_ids)) != 51:
        raise SuiteError("layout gallery IDs do not equal the 51 canonical add-ons")
    required_functions = {"load", "prepare", "build", "verify", "release", "clear"}
    completion_players: set[str] = set()
    function_ids: set[str] = set()
    for gallery in galleries:
        functions = gallery.get("functions") if isinstance(gallery, dict) else None
        function_values = list(functions.values()) if isinstance(functions, dict) else []
        if (
            not isinstance(functions, dict)
            or set(functions) != required_functions
            or not all(isinstance(functions[key], str) and functions[key] for key in functions)
            or len(set(function_values)) != len(function_values)
            or any(value in function_ids for value in function_values)
        ):
            identifier = gallery.get("id", "<unknown>") if isinstance(gallery, dict) else "<invalid>"
            raise SuiteError(f"gallery {identifier} lacks unique bounded function contracts")
        function_ids.update(function_values)
        completion = gallery.get("completion") if isinstance(gallery, dict) else None
        if (
            not isinstance(completion, dict)
            or completion.get("objective") != "bma_done"
            or not isinstance(completion.get("player"), str)
            or not completion["player"].startswith("#")
            or completion["player"] in completion_players
            or completion.get("mode")
            not in {"scheduled-game-tick-barrier", "terminal-predicate"}
        ):
            raise SuiteError(f"gallery {identifier} lacks an explicit completion contract")
        completion_players.add(completion["player"])
        verification = gallery.get("verification")
        if (
            not isinstance(verification, dict)
            or verification.get("objective") != "bma_test"
            or verification.get("failurePlayer") != completion["player"]
            or not isinstance(verification.get("mirroredChecks"), int)
            or verification["mirroredChecks"] < 1
        ):
            raise SuiteError(f"gallery {identifier} lacks an asserted verification contract")
    return value


def validate_composition_manifest(
    path: Path, layout_path: Path, layout: dict, datapack_path: Path
) -> dict[str, str | int]:
    require_pinned_manifest()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuiteError(f"cannot read gallery composition manifest {path}: {exc}") from exc
    tracked_manifest_sha256 = sha256(TRACKED_MANIFEST)
    expected_common = (
        manifest.get("schemaVersion") == 1
        and manifest.get("composerVersion") == COMPOSER_VERSION
        and manifest.get("compositionId") == layout.get("compositionId")
        and manifest.get("sourceManifestSha256") == tracked_manifest_sha256
    )
    options = manifest.get("options")
    if not expected_common or options != EXPECTED_COMPOSITION_OPTIONS:
        raise SuiteError("gallery composition manifest provenance/options are invalid")
    identities: dict[str, dict[str, int | str]] = {}
    for key, artifact in (("layout", layout_path), ("datapack", datapack_path)):
        record = manifest.get(key)
        expected = {
            "filename": artifact.name,
            "sizeBytes": artifact.stat().st_size if artifact.is_file() else -1,
            "sha256": sha256(artifact) if artifact.is_file() else "",
        }
        if record != expected:
            raise SuiteError(f"gallery composition {key} identity mismatch")
        identities[key] = expected
    try:
        with zipfile.ZipFile(datapack_path) as archive:
            identity_function = archive.read(
                "data/bluemap_atmons/function/identity.mcfunction"
            ).decode("utf-8")
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        raise SuiteError(f"cannot validate composed datapack identity function: {exc}") from exc
    if layout["compositionId"] not in identity_function:
        raise SuiteError("datapack identity function does not contain the composition ID")
    return {
        "compositionId": layout["compositionId"],
        "manifestSha256": sha256(path),
        "layoutSha256": str(identities["layout"]["sha256"]),
        "datapackSha256": str(identities["datapack"]["sha256"]),
        "datapackSizeBytes": int(identities["datapack"]["sizeBytes"]),
    }


def reproduce_composition(
    composition_manifest_path: Path,
    layout_path: Path,
    datapack_path: Path,
) -> dict[str, str]:
    if sha256(COMPOSER_PATH) != COMPOSER_SHA256:
        raise SuiteError("gallery composer differs from its reviewed immutable digest")
    if (
        composition_manifest_path.name != "gallery-composition-manifest.json"
        or layout_path.name != "gallery-layout.json"
        or datapack_path.name != "bluemap-atmons-galleries.zip"
    ):
        raise SuiteError("gallery artifacts do not use the canonical deterministic filenames")
    with tempfile.TemporaryDirectory(
        prefix="bluemap-atmons-runtime-recompose-"
    ) as temporary:
        root = Path(temporary)
        output = root / "bluemap-atmons-galleries"
        command = [
            sys.executable,
            str(COMPOSER_PATH),
            "--manifest",
            str(TRACKED_MANIFEST),
            "--output",
            str(output),
            "--origin-x",
            str(EXPECTED_COMPOSITION_OPTIONS["originX"]),
            "--origin-z",
            str(EXPECTED_COMPOSITION_OPTIONS["originZ"]),
            "--row-width",
            str(EXPECTED_COMPOSITION_OPTIONS["rowWidth"]),
            "--padding",
            str(EXPECTED_COMPOSITION_OPTIONS["padding"]),
            "--minimum-y",
            str(EXPECTED_COMPOSITION_OPTIONS["minimumY"]),
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
        )
        if result.returncode:
            raise SuiteError(
                "independent deterministic gallery composition failed: "
                + "\n".join(result.stdout.splitlines()[-40:])
            )
        regenerated = {
            composition_manifest_path: root / "gallery-composition-manifest.json",
            layout_path: root / "gallery-layout.json",
            datapack_path: root / "bluemap-atmons-galleries.zip",
        }
        for supplied, reproduced in regenerated.items():
            if not reproduced.is_file() or supplied.read_bytes() != reproduced.read_bytes():
                raise SuiteError(
                    f"supplied {supplied.name} differs from independent deterministic composition"
                )
    return {
        "status": "passed",
        "composerSha256": COMPOSER_SHA256,
        "sourceManifestSha256": TRACKED_MANIFEST_SHA256,
    }


def command_failed(response: str) -> bool:
    lowered = response.lower()
    return any(marker in lowered for marker in ERROR_MARKERS)


def run_checked(transport: Transport, command: str) -> tuple[str, float]:
    started = time.monotonic()
    response = transport.command(command)
    elapsed = time.monotonic() - started
    if command_failed(response):
        raise SuiteError(f"{command!r} failed: {response}")
    return response, elapsed


def wait_ready(transport: Transport, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        try:
            response = transport.command("list")
            if "players online" in response.lower() or "there are" in response.lower():
                return response
        except Exception as exc:  # readiness retry intentionally catches transport failures
            last_error = str(exc)
        time.sleep(2)
    raise SuiteError(f"server did not become RCON-ready within {timeout:.0f}s: {last_error}")


def verify_colocated_runtime(
    transport: Transport,
    artifact_prefix: list[str],
    runtime_identity_path: str,
    expected_attestation_sha256: str,
    timeout: float,
) -> dict[str, str]:
    identity_text = remote_text(artifact_prefix, runtime_identity_path, timeout)
    try:
        identity = json.loads(identity_text)
    except json.JSONDecodeError as exc:
        raise SuiteError(f"runtime identity JSON is malformed: {exc}") from exc
    boot_id = identity.get("bootId")
    attestation_sha256 = identity.get("runtimeAttestationSha256")
    started_at = identity.get("startedAt")
    if (
        identity.get("schemaVersion") != 1
        or not isinstance(boot_id, str)
        or not re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            boot_id,
        )
        or attestation_sha256 != expected_attestation_sha256
        or not isinstance(started_at, str)
    ):
        raise SuiteError("runtime identity file does not bind the attested server process")
    try:
        dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SuiteError("runtime identity start time is malformed") from exc
    command_response, _elapsed = run_checked(
        transport, "bluemapatmons runtime identity"
    )
    if (
        f"bootId={boot_id}" not in command_response
        or f"runtimeAttestationSha256={attestation_sha256}" not in command_response
    ):
        raise SuiteError(
            "artifact and command transports do not identify the same server process"
        )
    return {
        "bootId": boot_id,
        "runtimeAttestationSha256": attestation_sha256,
        "startedAt": started_at,
        "identityFileSha256": hashlib.sha256(
            identity_text.encode("utf-8")
        ).hexdigest(),
        "commandResponse": command_response,
    }


def run_restart(command: list[str]) -> None:
    result = subprocess.run(command, check=False, text=True)
    if result.returncode:
        raise SuiteError(f"restart hook exited {result.returncode}: {shlex.join(command)}")


def scoreboard_value(response: str) -> int:
    matches = re.findall(r"(?:has|is|=)\s+(-?\d+)\b", response)
    if not matches:
        raise SuiteError(f"could not parse scoreboard response: {response}")
    return int(matches[-1])


def wait_gallery_completion(
    transport: Transport, gallery: dict, timeout: float
) -> dict[str, int | float | str]:
    completion = gallery["completion"]
    deadline = time.monotonic() + timeout
    started = time.monotonic()
    polls = 0
    last_response = ""
    while time.monotonic() < deadline:
        last_response, _elapsed = run_checked(
            transport,
            f"scoreboard players get {completion['player']} {completion['objective']}",
        )
        polls += 1
        value = scoreboard_value(last_response)
        if value == 1:
            return {
                "status": "complete",
                "seconds": round(time.monotonic() - started, 3),
                "polls": polls,
                "scoreResponse": last_response,
                "mode": completion["mode"],
                "delayTicks": completion.get("delayTicks"),
                "timeoutTicks": completion.get("timeoutTicks"),
            }
        if value != 0:
            raise SuiteError(
                f"gallery {gallery['id']} completion score is invalid: {last_response}"
            )
        time.sleep(0.25)
    raise SuiteError(
        f"gallery {gallery['id']} did not reach its game-tick completion barrier "
        f"within {timeout:.1f}s; last response: {last_response}"
    )


def release_gallery(
    transport: Transport, gallery: dict, record: dict, phase: str
) -> Exception | None:
    try:
        response, elapsed = run_checked(
            transport, f"function {gallery['functions']['release']}"
        )
    except Exception as exc:  # cleanup failure is recorded without hiding the primary failure
        record.setdefault(phase, {})["cleanupError"] = str(exc)
        return exc
    record.setdefault(phase, {})["releaseSeconds"] = round(elapsed, 3)
    record[phase]["releaseResponse"] = response
    return None


def emergency_release_all(transport: Transport, layout: dict) -> list[dict[str, str]]:
    failures = []
    for gallery in layout["galleries"]:
        command = f"function {gallery['functions']['release']}"
        try:
            run_checked(transport, command)
        except Exception as exc:
            failures.append({"id": gallery["id"], "error": str(exc)})
    return failures


def run_gallery_cycles(
    transport: Transport,
    layout: dict,
    result: dict,
    settle_seconds: float,
    completion_timeout: float,
    verify_settle_seconds: float,
) -> None:
    _response, elapsed = run_checked(transport, "function bluemap_atmons:prepare")
    result["preflight"]["prepareSeconds"] = round(elapsed, 3)

    for gallery in layout["galleries"]:
        record = {"id": gallery["id"], "build": {}, "verification": {}}
        result["galleries"].append(record)
        primary_error: Exception | None = None
        try:
            response, elapsed = run_checked(
                transport, f"function {gallery['functions']['prepare']}"
            )
            record["build"]["prepareSeconds"] = round(elapsed, 3)
            record["build"]["prepareResponse"] = response
            response, elapsed = run_checked(
                transport, f"function {gallery['functions']['build']}"
            )
            record["build"]["seconds"] = round(elapsed, 3)
            record["build"]["response"] = response
            record["build"]["completion"] = wait_gallery_completion(
                transport, gallery, completion_timeout
            )
            if settle_seconds:
                time.sleep(settle_seconds)
            record["build"]["settleSeconds"] = settle_seconds
            record["build"]["status"] = "performed"

            verification = gallery["verification"]
            player = verification["failurePlayer"]
            objective = verification["objective"]
            pre_verification_response, _elapsed = run_checked(
                transport, f"scoreboard players get {player} {objective}"
            )
            record["verification"]["preVerificationFailures"] = scoreboard_value(
                pre_verification_response
            )
            record["verification"]["preVerificationResponse"] = (
                pre_verification_response
            )
            reset_response, reset_elapsed = run_checked(
                transport, f"scoreboard players set {player} {objective} 0"
            )
            record["verification"]["resetSeconds"] = round(reset_elapsed, 3)
            record["verification"]["resetResponse"] = reset_response
            response, elapsed = run_checked(
                transport, f"function {gallery['functions']['verify']}"
            )
            record["verification"]["seconds"] = round(elapsed, 3)
            record["verification"]["response"] = response
            if verify_settle_seconds:
                time.sleep(verify_settle_seconds)
            record["verification"]["settleSeconds"] = verify_settle_seconds
            score_response, _elapsed = run_checked(
                transport, f"scoreboard players get {player} {objective}"
            )
            failures = scoreboard_value(score_response)
            record["verification"].update(
                {
                    "status": "passed" if failures == 0 else "failed",
                    "failures": failures,
                    "mirroredChecks": verification["mirroredChecks"],
                    "scoreResponse": score_response,
                }
            )
            if failures != 0:
                raise SuiteError(
                    f"gallery {gallery['id']} immediate verification reported {failures} failures"
                )
        except Exception as exc:
            primary_error = exc
        cleanup_error = release_gallery(
            transport, gallery, record, "verification"
        )
        if primary_error is not None:
            raise primary_error
        if cleanup_error is not None:
            raise cleanup_error

    run_checked(transport, "save-all flush")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", type=Path, required=True)
    parser.add_argument("--composition-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument("--rcon", metavar="HOST:PORT")
    transport.add_argument(
        "--exec-prefix-json",
        help='JSON argv prefix; the Minecraft command is appended, e.g. ["kubectl",...,"rcon-cli"]',
    )
    parser.add_argument("--password-env", default="RCON_PASSWORD")
    parser.add_argument("--command-timeout", type=float, default=180)
    parser.add_argument("--readiness-timeout", type=float, default=900)
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=0.0,
        help="optional extra wall-clock margin after the game-tick completion barrier",
    )
    parser.add_argument(
        "--completion-timeout",
        type=float,
        default=DEFAULT_COMPLETION_TIMEOUT_SECONDS,
        help="wall-clock fail-safe while polling each explicit game-tick completion score",
    )
    parser.add_argument(
        "--verify-settle-seconds",
        type=float,
        default=DEFAULT_VERIFY_SETTLE_SECONDS,
        help="delay after each synchronous verify function before reading its score",
    )
    parser.add_argument(
        "--restart-exec-json",
        required=True,
        help="JSON argv for the mandatory controlled restart before gallery construction",
    )
    parser.add_argument("--bluemap-commit", required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument(
        "--addon-override-lock",
        type=Path,
        help="absolute schema-1 JSON lock required by local add-on candidate manifests",
    )
    parser.add_argument("--bluemap-jar", type=Path, required=True)
    parser.add_argument("--harness-jar", type=Path, required=True)
    parser.add_argument(
        "--artifact-exec-prefix-json",
        required=True,
        help="JSON argv prefix used to inspect the running server container",
    )
    parser.add_argument(
        "--runtime-mods-directory",
        required=True,
        help="exact directory NeoForge loaded; the ATMons integration profile uses /data/mods",
    )
    parser.add_argument(
        "--runtime-packs-directory",
        required=True,
        help="canonical BlueMap candidate-pack path /data/config/bluemap/packs",
    )
    parser.add_argument("--trusted-base-inventory", type=Path, required=True)
    parser.add_argument("--runtime-log", default="/data/logs/latest.log")
    parser.add_argument(
        "--runtime-identity-file",
        default="/data/config/bluemap-atmons-integration/runtime-identity.json",
    )
    parser.add_argument(
        "--runtime-attestation",
        default="/data/config/bluemap-atmons-integration/runtime-attestation.json",
    )
    parser.add_argument("--datapack-archive", type=Path, required=True)
    parser.add_argument("--installed-datapack", required=True)
    parser.add_argument("--expected-runtime-jar-count", type=int, required=True)
    args = parser.parse_args()

    result: dict = {
        "schemaVersion": 1,
        "startedAt": now(),
        "runtime": {},
        "preflight": {},
        "galleries": [],
        "summary": {},
    }
    try:
        layout_path = args.layout.resolve()
        layout = load_layout(layout_path)
        datapack_archive = args.datapack_archive.resolve()
        if not datapack_archive.is_file():
            raise SuiteError(f"composed datapack archive is missing: {datapack_archive}")
        composition = validate_composition_manifest(
            args.composition_manifest.resolve(),
            layout_path,
            layout,
            datapack_archive,
        )
        composition_reproduction = reproduce_composition(
            args.composition_manifest.resolve(),
            layout_path,
            datapack_archive,
        )
        require_pinned_manifest()
        try:
            tracked = json.loads(TRACKED_MANIFEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SuiteError(f"cannot read tracked compatibility manifest: {exc}") from exc
        override_lock_path = args.addon_override_lock
        override_lock = (
            load_addon_override_lock(override_lock_path, tracked)
            if override_lock_path is not None
            else None
        )
        candidate_manifest_path = args.candidate_manifest.resolve()
        candidate_manifest = load_candidate_manifest(
            candidate_manifest_path, override_lock
        )
        candidate_reproduction = reproduce_candidate_overlays(
            candidate_manifest_path, candidate_manifest, override_lock_path
        )
        candidate_identity = candidate_manifest["candidateBlueMap"]
        artifact_prefix = parse_json_argv(
            args.artifact_exec_prefix_json, "--artifact-exec-prefix-json"
        )
        artifact_attestation = attest_runtime_artifacts(
            candidate_manifest_path,
            candidate_manifest,
            args.bluemap_jar.resolve(),
            args.harness_jar.resolve(),
            artifact_prefix,
            args.runtime_mods_directory,
            args.runtime_packs_directory,
            args.trusted_base_inventory.resolve(),
            args.runtime_attestation,
            args.expected_runtime_jar_count,
            args.bluemap_commit,
            layout["compositionId"],
            str(composition["manifestSha256"]),
            str(composition["layoutSha256"]),
            str(composition["datapackSha256"]),
            args.command_timeout,
        )
        expected_datapack = {
            "sizeBytes": composition["datapackSizeBytes"],
            "sha256": composition["datapackSha256"],
        }
        actual_datapack = remote_file_identity(
            artifact_prefix,
            args.installed_datapack,
            args.command_timeout,
        )
        if actual_datapack != expected_datapack:
            raise SuiteError(
                "installed composed datapack does not match the local integration artifact"
            )
        result["runtime"] = {
            **layout["runtime"],
            "bluemapCommit": args.bluemap_commit,
            "bluemapVersion": candidate_identity["version"],
            "bluemapJarSha256": artifact_attestation["bluemap"]["sha256"],
        }
        result["preflight"]["artifactAttestation"] = artifact_attestation
        result["preflight"]["candidateReproduction"] = candidate_reproduction
        result["preflight"]["galleryComposition"] = {
            "status": "passed",
            "compositionId": layout["compositionId"],
            "compositionManifestSha256": composition["manifestSha256"],
            "layoutSha256": composition["layoutSha256"],
            "datapack": expected_datapack,
            "installedPath": args.installed_datapack,
            "reproduction": composition_reproduction,
        }
        if args.rcon:
            host, separator, port_text = args.rcon.rpartition(":")
            if not separator or not host:
                raise SuiteError("--rcon must be HOST:PORT")
            password = os.environ.get(args.password_env)
            if not password:
                raise SuiteError(f"environment variable {args.password_env} is not set")
            command_transport: Transport = RconTransport(
                host, int(port_text), password, args.command_timeout
            )
        else:
            prefix = parse_json_argv(args.exec_prefix_json, "--exec-prefix-json")
            command_transport = ExecTransport(prefix, args.command_timeout)

        try:
            result["preflight"]["list"] = wait_ready(command_transport, args.readiness_timeout)
            runtime_identity = verify_colocated_runtime(
                command_transport,
                artifact_prefix,
                args.runtime_identity_file,
                str(artifact_attestation["runtimeAttestationSha256"]),
                args.command_timeout,
            )
            result["preflight"]["runtimeIdentity"] = runtime_identity
            result["preflight"]["activationLog"] = attest_activation_log(
                artifact_prefix,
                args.runtime_log,
                runtime_identity,
                list(artifact_attestation["candidateComponentIds"]),
                args.bluemap_commit,
                args.command_timeout,
            )
            enabled, _elapsed = run_checked(command_transport, "datapack list enabled")
            result["preflight"]["enabledDatapacks"] = enabled
            if "bluemap-atmons" not in enabled.lower():
                raise SuiteError("the composed BlueMap ATMons gallery datapack is not enabled")
            version_response, _elapsed = run_checked(command_transport, "bluemap version")
            result["preflight"]["bluemapVersion"] = version_response
            run_checked(command_transport, "function bluemap_atmons:identity")
            identity_response, _elapsed = run_checked(
                command_transport,
                "data get storage bluemap_atmons:identity composition",
            )
            if layout["compositionId"] not in identity_response:
                raise SuiteError(
                    "installed datapack identity function does not match gallery-layout.json"
                )
            result["preflight"]["galleryComposition"]["identityResponse"] = identity_response

            pre_restart_identity = remote_runtime_identity(
                artifact_prefix, args.command_timeout
            )
            restart_command = parse_json_argv(
                args.restart_exec_json, "--restart-exec-json"
            )
            run_restart(restart_command)
            command_transport.close()
            post_restart_identity = wait_runtime_identity_change(
                artifact_prefix,
                pre_restart_identity,
                args.readiness_timeout,
                args.command_timeout,
            )
            result["preflight"]["postRestartList"] = wait_ready(
                command_transport, args.readiness_timeout
            )
            post_restart_attestation = attest_runtime_artifacts(
                candidate_manifest_path,
                candidate_manifest,
                args.bluemap_jar.resolve(),
                args.harness_jar.resolve(),
                artifact_prefix,
                args.runtime_mods_directory,
                args.runtime_packs_directory,
                args.trusted_base_inventory.resolve(),
                args.runtime_attestation,
                args.expected_runtime_jar_count,
                args.bluemap_commit,
                layout["compositionId"],
                str(composition["manifestSha256"]),
                str(composition["layoutSha256"]),
                str(composition["datapackSha256"]),
                args.command_timeout,
            )
            post_restart_runtime_identity = verify_colocated_runtime(
                command_transport,
                artifact_prefix,
                args.runtime_identity_file,
                str(post_restart_attestation["runtimeAttestationSha256"]),
                args.command_timeout,
            )
            if post_restart_runtime_identity["bootId"] == runtime_identity["bootId"]:
                raise SuiteError("controlled restart did not change the harness boot ID")
            post_restart_activation_log = attest_activation_log(
                artifact_prefix,
                args.runtime_log,
                post_restart_runtime_identity,
                list(post_restart_attestation["candidateComponentIds"]),
                args.bluemap_commit,
                args.command_timeout,
            )
            post_restart_version, _elapsed = run_checked(
                command_transport, "bluemap version"
            )
            if remote_file_identity(
                artifact_prefix, args.installed_datapack, args.command_timeout
            ) != expected_datapack:
                raise SuiteError("post-restart installed datapack identity mismatch")
            run_checked(command_transport, "function bluemap_atmons:identity")
            post_restart_composition, _elapsed = run_checked(
                command_transport,
                "data get storage bluemap_atmons:identity composition",
            )
            if layout["compositionId"] not in post_restart_composition:
                raise SuiteError("post-restart gallery composition identity mismatch")
            result["preflight"]["postRestartAttestation"] = {
                "previousContainerIdentity": pre_restart_identity,
                "containerIdentity": post_restart_identity,
                "runtimeIdentity": post_restart_runtime_identity,
                "activationLog": post_restart_activation_log,
                "artifacts": post_restart_attestation,
                "bluemapVersion": post_restart_version,
                "compositionResponse": post_restart_composition,
            }

            run_gallery_cycles(
                command_transport,
                layout,
                result,
                args.settle_seconds,
                args.completion_timeout,
                args.verify_settle_seconds,
            )

            statuses = [record["verification"]["status"] for record in result["galleries"]]
            build_statuses = [record["build"]["status"] for record in result["galleries"]]
            asserted_pass = (
                len(statuses) == 51
                and all(status == "passed" for status in statuses)
                and all(status == "performed" for status in build_statuses)
            )
            result["summary"] = {
                "galleryCount": len(result["galleries"]),
                "buildsPerformed": build_statuses.count("performed"),
                "buildsSkipped": build_statuses.count("skipped"),
                "passed": statuses.count("passed"),
                "failed": statuses.count("failed"),
                "performedUnasserted": statuses.count("performed-unasserted")
                + statuses.count("unasserted"),
                "status": "passed" if asserted_pass else "failed",
            }
            if result["summary"]["status"] != "passed":
                raise SuiteError(f"runtime suite did not produce 51 asserted passes: {result['summary']}")
        finally:
            try:
                result["cleanup"] = {
                    "emergencyReleaseFailures": emergency_release_all(
                        command_transport, layout
                    )
                }
            except Exception as cleanup_exc:
                result["cleanup"] = {"emergencyReleaseError": str(cleanup_exc)}
            command_transport.close()
    except Exception as exc:
        result["error"] = str(exc)
        result.setdefault("summary", {})["status"] = "failed"
        exit_code = 1
    else:
        exit_code = 0
    result["finishedAt"] = now()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result.get("summary", {}), sort_keys=True))
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
