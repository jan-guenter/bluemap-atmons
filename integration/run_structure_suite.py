#!/usr/bin/env python3
"""Publish, render, and attest the exact generated ATMons structure maps."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import time
from decimal import Decimal
from pathlib import Path

import run_runtime_suite as runtime


CANONICAL_PATHS = {
    "catalog": "/data/config/bluemap-atmons-integration/structure-catalog.json",
    "masks": "/data/config/bluemap-atmons-integration/structure-render-masks.json",
    "receipt": "/data/config/bluemap-atmons-integration/structure-generation-receipt.json",
    "work": "/data/config/bluemap-atmons-integration/structure-work-state.json",
    "maps": "/data/config/bluemap/atmons-structure-maps.json",
    "schedule": (
        "/data/config/bluemap-atmons-integration/structure-render-schedule.json"
    ),
    "config_root": "/data/config/bluemap",
    "storage_root": "/data/bluemap/web/maps",
    "runtime_identity": (
        "/data/config/bluemap-atmons-integration/runtime-identity.json"
    ),
    "world": "/data/world",
}
GENERATOR_PATH = (
    Path(__file__).resolve().parent
    / "harness"
    / "tools"
    / "generate_bluemap_map_configs.py"
)
GENERATOR_SHA256 = "1c5f7099840b07473c1d4ba5fe63b21f0ef3efa677a0a257749ca33a29ad21ea"
RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9/._-]+$")
REGION_FILE = re.compile(r"^x(-?\d+)z(-?\d+)\.regions\.dat(?:\.gz)?$")
RENDER_BUSY_RESPONSE = "BlueMap renderer is not running and idle"
RENDER_VERIFICATION = re.compile(
    r"Verified ([1-9][0-9]*) freshly rendered structure tiles across "
    r"([1-9][0-9]*) maps; evidenceSha256=([0-9a-f]{64})"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_map_id(dimension: str) -> str:
    if not RESOURCE_LOCATION.fullmatch(dimension):
        raise runtime.SuiteError(f"invalid dimension in structure evidence: {dimension!r}")
    slug = re.sub(r"[^a-z0-9]+", "_", dimension.lower()).strip("_")
    slug = slug[:64].rstrip("_") or "dimension"
    return f"atmons_{slug}_{hashlib.sha256(dimension.encode()).hexdigest()[:12]}"


def json_object(label: str, text: str) -> dict:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise runtime.SuiteError(f"{label} JSON is malformed: {exc}") from exc
    if not isinstance(value, dict):
        raise runtime.SuiteError(f"{label} must be a JSON object")
    return value


def exact_targets(catalog: dict) -> list[dict[str, int | str]]:
    by_key: dict[str, dict[str, int | str]] = {}
    structures = catalog.get("structures")
    if not isinstance(structures, list) or not structures:
        raise runtime.SuiteError("structure catalog is empty")
    located = 0
    registry_only = 0
    for structure in structures:
        if not isinstance(structure, dict):
            raise runtime.SuiteError("structure catalog entry is malformed")
        eligibility = structure.get("eligibility")
        selection = structure.get("selection")
        if not isinstance(eligibility, list) or not isinstance(selection, dict):
            raise runtime.SuiteError("structure eligibility/selection is malformed")
        status = selection.get("status")
        if eligibility:
            if status != "located":
                raise runtime.SuiteError("eligible structure was not located")
            located += 1
            dimension = selection.get("dimension")
            bounds = selection.get("chunkBounds")
            if not isinstance(dimension, str) or not isinstance(bounds, dict):
                raise runtime.SuiteError("located structure lacks chunk bounds")
            values = [bounds.get(key) for key in ("minX", "minZ", "maxX", "maxZ")]
            if not all(isinstance(value, int) for value in values):
                raise runtime.SuiteError("located structure chunk bounds are malformed")
            min_x, min_z, max_x, max_z = values
            if min_x > max_x or min_z > max_z:
                raise runtime.SuiteError("located structure chunk bounds are inverted")
            expected_count = (max_x - min_x + 1) * (max_z - min_z + 1)
            if selection.get("chunkCount") != expected_count:
                raise runtime.SuiteError("located structure chunk count is inconsistent")
            for x in range(min_x, max_x + 1):
                for z in range(min_z, max_z + 1):
                    key = f"{dimension}:{x}:{z}"
                    by_key[key] = {"dimension": dimension, "x": x, "z": z}
        else:
            if status != "registry-only":
                raise runtime.SuiteError("ineligible structure is not registry-only")
            registry_only += 1
    summary = catalog.get("summary")
    if not isinstance(summary, dict) or any(
        (
            summary.get("located") != located,
            summary.get("unlocated") != registry_only,
            summary.get("markers") != located,
        )
    ):
        raise runtime.SuiteError("structure catalog summary is inconsistent")
    return [by_key[key] for key in sorted(by_key)]


def target_digest(targets: list[dict[str, int | str]]) -> str:
    rows = "".join(
        f"{target['dimension']}:{target['x']}:{target['z']}\n" for target in targets
    )
    return sha256_bytes(rows.encode("utf-8"))


def region_digest(regions: dict[str, list[tuple[int, int]]]) -> str:
    rows = "".join(
        f"{dimension}:{x}:{z}\n"
        for dimension in sorted(regions)
        for x, z in sorted(regions[dimension])
    )
    return sha256_bytes(rows.encode("utf-8"))


def region_state_cells(regions: list[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(x // 64, z // 64) for x, z in regions}


def validate_evidence(texts: dict[str, str]) -> dict:
    catalog = json_object("catalog", texts["catalog"])
    masks = json_object("render masks", texts["masks"])
    receipt = json_object("generation receipt", texts["receipt"])
    work = json_object("work state", texts["work"])
    maps = json_object("structure map manifest", texts["maps"])
    targets = exact_targets(catalog)
    if (
        work.get("operation") != "generate"
        or work.get("status") != "complete"
        or work.get("planFingerprint") != catalog.get("planFingerprint")
        or work.get("cursor") != len(targets)
        or work.get("total") != len(targets)
        or work.get("targets") != targets
        or work.get("activeBatch") != []
        or work.get("ownedForcedChunks") != []
    ):
        raise runtime.SuiteError("generation work state is not exact and complete")
    catalog_sha = sha256_bytes(texts["catalog"].encode("utf-8"))
    masks_sha = sha256_bytes(texts["masks"].encode("utf-8"))
    if (
        receipt.get("schemaVersion") != 1
        or receipt.get("catalogSha256") != catalog_sha
        or receipt.get("worldIdentity") != catalog.get("worldIdentity")
        or receipt.get("planFingerprint") != catalog.get("planFingerprint")
        or receipt.get("runtimeAttestationSha256")
        != catalog.get("runtimeAttestationSha256")
        or receipt.get("targetCount") != len(targets)
        or receipt.get("targetDigestSha256") != target_digest(targets)
    ):
        raise runtime.SuiteError("generation receipt is not bound to exact targets")
    if (
        masks.get("worldIdentity") != catalog.get("worldIdentity")
        or masks.get("planFingerprint") != catalog.get("planFingerprint")
        or masks.get("runtimeAttestationSha256")
        != catalog.get("runtimeAttestationSha256")
        or maps.get("catalogSha256") != catalog_sha
        or maps.get("renderMasksSha256") != masks_sha
        or maps.get("worldIdentity") != catalog.get("worldIdentity")
        or maps.get("planFingerprint") != catalog.get("planFingerprint")
        or maps.get("runtimeAttestationSha256")
        != catalog.get("runtimeAttestationSha256")
        or maps.get("world") != CANONICAL_PATHS["world"]
        or maps.get("storage") != "file"
    ):
        raise runtime.SuiteError("structure map manifest is not bound to catalog/masks")
    expected_regions: dict[str, set[tuple[int, int]]] = {}
    expected_masks: dict[str, int] = {}
    for structure in catalog["structures"]:
        selection = structure["selection"]
        if selection["status"] != "located":
            continue
        dimension = selection["dimension"]
        expected_masks[dimension] = expected_masks.get(dimension, 0) + 1
        for region in selection.get("regions", []):
            if not isinstance(region, dict) or not all(
                isinstance(region.get(axis), int) for axis in ("x", "z")
            ):
                raise runtime.SuiteError("catalog region coordinates are malformed")
            expected_regions.setdefault(dimension, set()).add((region["x"], region["z"]))
    records = maps.get("maps")
    if not isinstance(records, list) or len(records) != len(expected_regions):
        raise runtime.SuiteError("structure map count differs from located dimensions")
    map_records: dict[str, dict] = {}
    for record in records:
        dimension = record.get("dimension") if isinstance(record, dict) else None
        expected_id = safe_map_id(dimension) if isinstance(dimension, str) else ""
        if (
            dimension not in expected_regions
            or record.get("mapId") != expected_id
            or record.get("configFile") != f"maps/{expected_id}.conf"
            or record.get("maskCount") != expected_masks[dimension]
            or not isinstance(record.get("sizeBytes"), int)
            or not re.fullmatch(r"[0-9a-f]{64}", record.get("sha256", ""))
            or expected_id in map_records
        ):
            raise runtime.SuiteError("structure map entry is invalid")
        map_records[expected_id] = record
    return {
        "catalog": catalog,
        "targets": targets,
        "targetDigestSha256": target_digest(targets),
        "mapRecords": map_records,
        "expectedRegions": {
            safe_map_id(dimension): sorted(regions)
            for dimension, regions in expected_regions.items()
        },
        "expectedRegionsByDimension": {
            dimension: sorted(regions)
            for dimension, regions in expected_regions.items()
        },
        "catalogSha256": catalog_sha,
        "renderMasksSha256": masks_sha,
    }


def replay_map_configs(
    texts: dict[str, str],
    evidence: dict,
    artifact_prefix: list[str],
    timeout: float,
) -> dict[str, str | int]:
    generator_bytes = GENERATOR_PATH.read_bytes()
    if sha256_bytes(generator_bytes) != GENERATOR_SHA256:
        raise runtime.SuiteError("structure map generator differs from the reviewed source")
    spec = importlib.util.spec_from_file_location(
        "bluemap_atmons_map_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise runtime.SuiteError("could not load the reviewed structure map generator")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    with tempfile.TemporaryDirectory(prefix="bluemap-atmons-map-replay-") as temporary:
        root = Path(temporary)
        catalog_path = root / "structure-catalog.json"
        masks_path = root / "structure-render-masks.json"
        config_root = root / "config" / "bluemap"
        manifest_path = config_root / "atmons-structure-maps.json"
        catalog_path.write_text(texts["catalog"], encoding="utf-8")
        masks_path.write_text(texts["masks"], encoding="utf-8")
        generator.generate(
            catalog_path,
            masks_path,
            config_root,
            Path(CANONICAL_PATHS["world"]),
            "file",
            manifest_path,
        )
        if manifest_path.read_text(encoding="utf-8") != texts["maps"]:
            raise runtime.SuiteError(
                "installed structure map manifest differs from deterministic replay"
            )
        compared = 0
        for map_id, record in evidence["mapRecords"].items():
            generated = (config_root / record["configFile"]).read_text(encoding="utf-8")
            installed = runtime.remote_text(
                artifact_prefix,
                f"{CANONICAL_PATHS['config_root']}/{record['configFile']}",
                timeout,
            )
            if installed != generated:
                raise runtime.SuiteError(
                    f"installed map config differs from deterministic replay: {map_id}"
                )
            compared += 1
    return {
        "generatorSha256": GENERATOR_SHA256,
        "mapConfigsCompared": compared,
        "status": "passed",
    }


def remote_tree(prefix: list[str], root: str, timeout: float) -> list[tuple[str, int, Decimal]]:
    script = r'''root=$1
test -d "$root"
find "$root" -type f -printf '%P\t%s\t%T@\n' | LC_ALL=C sort
'''
    result = subprocess.run(
        [*prefix, "sh", "-ceu", script, "bluemap-atmons-tree", root],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode:
        raise runtime.SuiteError(f"could not inventory map storage {root}: {result.stdout}")
    rows: list[tuple[str, int, Decimal]] = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or not fields[1].isdigit():
            raise runtime.SuiteError(f"malformed map-storage row: {line!r}")
        rows.append((fields[0], int(fields[1]), Decimal(fields[2])))
    return rows


def remote_epoch(prefix: list[str], timeout: float) -> Decimal:
    result = subprocess.run(
        [*prefix, "date", "+%s.%N"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    try:
        value = Decimal(result.stdout.strip())
    except Exception as exc:
        raise runtime.SuiteError(f"could not read artifact clock: {result.stdout}") from exc
    if result.returncode:
        raise runtime.SuiteError(f"could not read artifact clock: {result.stdout}")
    return value


def wait_render_verification(
    transport: runtime.Transport,
    expected_maps: int,
    timeout: float,
    poll_interval: float = 5.0,
) -> tuple[str, re.Match[str]]:
    deadline = time.monotonic() + timeout
    last = ""
    while True:
        last = transport.command("bluemapatmons structures verify-render")
        stripped = last.strip()
        if stripped == RENDER_BUSY_RESPONSE:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise runtime.SuiteError(
                    "BlueMap renderer did not complete exact structure renders: " + last
                )
            time.sleep(min(poll_interval, remaining))
            continue
        if runtime.command_failed(last):
            raise runtime.SuiteError(f"structure render verification failed: {last}")
        match = RENDER_VERIFICATION.fullmatch(stripped)
        if match is None or int(match.group(2)) != expected_maps:
            raise runtime.SuiteError(f"exact structure tile verification failed: {last}")
        return last, match


def attest_storage(
    prefix: list[str],
    storage_root: str,
    expected_regions: dict[str, list[tuple[int, int]]],
    scheduled_at: Decimal,
    timeout: float,
) -> dict[str, dict[str, int | str]]:
    evidence: dict[str, dict[str, int | str]] = {}
    for map_id, regions in sorted(expected_regions.items()):
        expected_state_cells = region_state_cells(regions)
        rows = remote_tree(prefix, f"{storage_root}/{map_id}", timeout)
        fresh_tiles = [
            row for row in rows
            if row[0].startswith("tiles/0/") and row[1] > 0 and row[2] >= scheduled_at
        ]
        fresh_region_states: set[tuple[int, int]] = set()
        for path, size, modified in rows:
            if not path.startswith("rstate/regions/") or size < 1 or modified < scheduled_at:
                continue
            flat_name = "".join(Path(path).relative_to("rstate/regions").parts)
            match = REGION_FILE.fullmatch(flat_name)
            if match:
                fresh_region_states.add((int(match.group(1)), int(match.group(2))))
        missing = sorted(expected_state_cells.difference(fresh_region_states))
        if not fresh_tiles or missing:
            raise runtime.SuiteError(
                f"map {map_id} lacks fresh tile/region output; "
                f"freshTiles={len(fresh_tiles)}, missingRegions={missing[:20]}"
            )
        digest = hashlib.sha256()
        for path, size, modified in rows:
            digest.update(f"{path}\t{size}\t{modified}\n".encode("utf-8"))
        evidence[map_id] = {
            "files": len(rows),
            "freshHiresTiles": len(fresh_tiles),
            "freshRegionStates": len(fresh_region_states),
            "inventorySha256": digest.hexdigest(),
        }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    command_transport = parser.add_mutually_exclusive_group(required=True)
    command_transport.add_argument("--rcon", metavar="HOST:PORT")
    command_transport.add_argument("--exec-prefix-json")
    parser.add_argument("--password-env", default="RCON_PASSWORD")
    parser.add_argument("--artifact-exec-prefix-json", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render-timeout", type=float, default=3600.0)
    parser.add_argument("--command-timeout", type=float, default=60.0)
    for key, value in CANONICAL_PATHS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", dest=key, default=value)
    args = parser.parse_args()
    output = args.output.resolve()
    report: dict = {"schemaVersion": 1, "startedAt": runtime.now(), "status": "failed"}
    transport: runtime.Transport | None = None
    try:
        artifact_prefix = runtime.parse_json_argv(
            args.artifact_exec_prefix_json, "--artifact-exec-prefix-json"
        )
        if args.rcon:
            host, separator, port_text = args.rcon.rpartition(":")
            if not separator or not host:
                raise runtime.SuiteError("--rcon must be HOST:PORT")
            password = os.environ.get(args.password_env)
            if not password:
                raise runtime.SuiteError(
                    f"environment variable {args.password_env} is not set"
                )
            transport = runtime.RconTransport(
                host, int(port_text), password, args.command_timeout
            )
        else:
            command_prefix = runtime.parse_json_argv(
                args.exec_prefix_json, "--exec-prefix-json"
            )
            transport = runtime.ExecTransport(command_prefix, args.command_timeout)
        supplied_paths = {key: getattr(args, key) for key in CANONICAL_PATHS}
        if supplied_paths != CANONICAL_PATHS:
            raise runtime.SuiteError("all structure-suite paths must remain canonical")
        evidence_paths = {
            "catalog": args.catalog,
            "masks": args.masks,
            "receipt": args.receipt,
            "work": args.work,
            "maps": args.maps,
        }
        texts = {
            key: runtime.remote_text(artifact_prefix, path, args.command_timeout)
            for key, path in evidence_paths.items()
        }
        evidence = validate_evidence(texts)
        initial_runtime_identity = runtime.verify_colocated_runtime(
            transport,
            artifact_prefix,
            args.runtime_identity,
            evidence["catalog"]["runtimeAttestationSha256"],
            args.command_timeout,
        )
        map_config_replay = replay_map_configs(
            texts, evidence, artifact_prefix, args.command_timeout
        )
        for map_id, record in evidence["mapRecords"].items():
            identity = runtime.remote_file_identity(
                artifact_prefix,
                f"{args.config_root}/{record['configFile']}",
                args.command_timeout,
            )
            if identity != {
                "sizeBytes": record["sizeBytes"],
                "sha256": record["sha256"],
            }:
                raise runtime.SuiteError(f"map config bytes changed for {map_id}")
        publish, _elapsed = runtime.run_checked(
            transport, "bluemapatmons structures publish"
        )
        expected_publish = (
            f"Published {evidence['catalog']['summary']['located']} structure markers "
            f"to {len(evidence['mapRecords'])} maps"
        )
        if publish.strip() != expected_publish:
            raise runtime.SuiteError(f"structure marker publication failed: {publish}")
        scheduled_at = remote_epoch(artifact_prefix, args.command_timeout)
        render, _elapsed = runtime.run_checked(
            transport, "bluemapatmons structures render"
        )
        expected_maps = len(evidence["mapRecords"])
        if f"Queued {expected_maps} exact BlueMap region-update tasks" not in render:
            raise runtime.SuiteError(f"structure render scheduling count mismatch: {render}")
        verify_render, verification_match = wait_render_verification(
            transport,
            expected_maps,
            args.render_timeout,
        )
        schedule_text = runtime.remote_text(
            artifact_prefix, args.schedule, args.command_timeout
        )
        schedule = json_object("structure render schedule", schedule_text)
        expected_region_count = sum(
            len(regions)
            for regions in evidence["expectedRegionsByDimension"].values()
        )
        scheduled_epoch_millis = schedule.get("scheduledAtEpochMillis")
        previous_region_max = schedule.get("previousRegionMaxEpochSecond")
        if (
            schedule.get("schemaVersion") != 1
            or schedule.get("catalogSha256") != evidence["catalogSha256"]
            or schedule.get("mapManifestSha256")
            != sha256_bytes(texts["maps"].encode("utf-8"))
            or schedule.get("worldIdentity")
            != evidence["catalog"].get("worldIdentity")
            or schedule.get("planFingerprint")
            != evidence["catalog"].get("planFingerprint")
            or schedule.get("runtimeAttestationSha256")
            != evidence["catalog"].get("runtimeAttestationSha256")
            or schedule.get("bootId") != initial_runtime_identity["bootId"]
            or schedule.get("mapCount") != expected_maps
            or schedule.get("regionCount") != expected_region_count
            or schedule.get("regionDigestSha256")
            != region_digest(evidence["expectedRegionsByDimension"])
            or not isinstance(scheduled_epoch_millis, int)
            or not isinstance(previous_region_max, int)
            or scheduled_epoch_millis // 1000 <= previous_region_max
            or not re.fullmatch(
                r"[0-9a-f]{64}",
                schedule.get("previousRegionStateDigestSha256", ""),
            )
            or Decimal(scheduled_epoch_millis) / Decimal(1000) < scheduled_at
        ):
            raise runtime.SuiteError(
                "structure render schedule is not bound to this exact run"
            )
        storage = attest_storage(
            artifact_prefix,
            args.storage_root,
            evidence["expectedRegions"],
            scheduled_at,
            args.command_timeout,
        )
        final_runtime_identity = runtime.verify_colocated_runtime(
            transport,
            artifact_prefix,
            args.runtime_identity,
            evidence["catalog"]["runtimeAttestationSha256"],
            args.command_timeout,
        )
        if final_runtime_identity["bootId"] != initial_runtime_identity["bootId"]:
            raise runtime.SuiteError("server boot changed during structure publication/render")
        report.update(
            {
                "status": "passed",
                "finishedAt": runtime.now(),
                "catalogSha256": evidence["catalogSha256"],
                "renderMasksSha256": evidence["renderMasksSha256"],
                "targetCount": len(evidence["targets"]),
                "targetDigestSha256": evidence["targetDigestSha256"],
                "mapCount": expected_maps,
                "publishResponse": publish,
                "renderResponse": render,
                "renderVerificationResponse": verify_render,
                "verifiedTileCount": int(verification_match.group(1)),
                "tileEvidenceSha256": verification_match.group(3),
                "runtimeIdentity": final_runtime_identity,
                "mapConfigReplay": map_config_replay,
                "scheduledAtEpoch": str(scheduled_at),
                "scheduleSha256": sha256_bytes(schedule_text.encode("utf-8")),
                "storage": storage,
            }
        )
        return_code = 0
    except Exception as exc:
        report["finishedAt"] = runtime.now()
        report["error"] = str(exc)
        return_code = 1
    finally:
        if transport is not None:
            transport.close()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output)}, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
