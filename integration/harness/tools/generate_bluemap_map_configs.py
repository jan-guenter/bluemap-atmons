#!/usr/bin/env python3
"""Generate one exact BlueMap map config per selected structure dimension."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9/._-]+$")
MAP_ID = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
BASELINE = {
    "atmons": "1.2.0",
    "minecraft": "1.21.1",
    "neoforge": "21.1.248",
    "bluemapApi": "2.8.0",
}


def safe_map_id(dimension: str) -> str:
    if not isinstance(dimension, str) or not RESOURCE_LOCATION.fullmatch(dimension):
        raise ValueError(f"Invalid dimension: {dimension!r}")
    slug = re.sub(r"[^a-z0-9]+", "_", dimension.lower()).strip("_")
    slug = slug[:64].rstrip("_") or "dimension"
    suffix = hashlib.sha256(dimension.encode("utf-8")).hexdigest()[:12]
    return f"atmons_{slug}_{suffix}"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _dimensions(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    runtime = catalog.get("runtime")
    if (
        catalog.get("schemaVersion") != 1
        or not isinstance(runtime, dict)
        or any(runtime.get(key) != value for key, value in BASELINE.items())
        or runtime.get("packCommit") != "c7bb230f21d14d26859d0b92548f089b3a493ad9"
        or not re.fullmatch(r"[0-9a-f]{40}", runtime.get("bluemapCommit", ""))
        or not re.fullmatch(r"[0-9a-f]{64}", runtime.get("bluemapJarSha256", ""))
        or not isinstance(runtime.get("bluemapVersion"), str)
        or not runtime["bluemapVersion"]
    ):
        raise ValueError("Catalog does not match the exact ATMons 1.2.0 baseline")
    values = catalog.get("dimensions")
    if not isinstance(values, list):
        raise ValueError("Catalog dimensions must be an array")
    dimensions: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("Catalog dimension entry must be an object")
        dimension = value.get("id")
        expected_map_id = safe_map_id(dimension)
        if value.get("safeMapId") != expected_map_id:
            raise ValueError(f"Catalog safeMapId mismatch for {dimension}")
        if value.get("mapConfigFile") != f"maps/{expected_map_id}.conf":
            raise ValueError(f"Catalog mapConfigFile mismatch for {dimension}")
        anchor = value.get("anchor")
        if not isinstance(anchor, dict) or not all(
            isinstance(anchor.get(axis), int) for axis in ("x", "y", "z")
        ):
            raise ValueError(f"Catalog anchor is invalid for {dimension}")
        if dimension in dimensions:
            raise ValueError(f"Duplicate catalog dimension: {dimension}")
        dimensions[dimension] = value
    return dimensions


def _selected_dimensions(catalog: dict[str, Any]) -> set[str]:
    structures = catalog.get("structures")
    if not isinstance(structures, list):
        raise ValueError("Catalog structures must be an array")
    selected: set[str] = set()
    terminal = 0
    located = 0
    for structure in structures:
        if not isinstance(structure, dict) or not isinstance(
            structure.get("selection"), dict
        ):
            raise ValueError("Catalog structure selection is invalid")
        eligibility = structure.get("eligibility")
        if not isinstance(eligibility, list):
            raise ValueError("Catalog structure eligibility is invalid")
        selection = structure["selection"]
        status = selection.get("status")
        if (eligibility and status != "located") or (
            not eligibility and status != "registry-only"
        ):
            raise ValueError(
                "Catalog contains an eligible unlocated or invalid registry-only selection"
            )
        terminal += 1
        if status == "located":
            dimension = selection.get("dimension")
            if not RESOURCE_LOCATION.fullmatch(dimension or ""):
                raise ValueError("Located structure has an invalid dimension")
            selected.add(dimension)
            located += 1
    summary = catalog.get("summary")
    if (
        not structures
        or terminal != len(structures)
        or not isinstance(summary, dict)
        or summary.get("registered", 0) < 1
        or summary.get("located") != located
        or summary.get("unlocated") != len(structures) - located
        or summary.get("markers") != located
    ):
        raise ValueError("Catalog summary is incomplete or differs from terminal selections")
    if not selected:
        raise ValueError("Catalog has no located structures")
    return selected


def _catalog_masks(catalog: dict[str, Any]) -> dict[str, list[dict[str, int]]]:
    keys = ("minX", "maxX", "minZ", "maxZ", "minY", "maxY")
    result: dict[str, list[dict[str, int]]] = {}
    for structure in catalog.get("structures", []):
        selection = structure.get("selection", {}) if isinstance(structure, dict) else {}
        if selection.get("status") != "located":
            continue
        dimension = selection.get("dimension")
        bounds = selection.get("borderedBounds")
        if not RESOURCE_LOCATION.fullmatch(dimension or "") or not isinstance(bounds, dict):
            raise ValueError("Located structure has invalid render-mask evidence")
        mask = {
            "minX": bounds.get("minX"),
            "maxX": bounds.get("maxX"),
            "minZ": bounds.get("minZ"),
            "maxZ": bounds.get("maxZ"),
            "minY": bounds.get("minY"),
            "maxY": bounds.get("maxY"),
        }
        if not all(isinstance(mask[key], int) for key in keys):
            raise ValueError("Located structure borderedBounds are invalid")
        result.setdefault(dimension, []).append(mask)
    for masks in result.values():
        masks.sort(key=lambda mask: tuple(mask[key] for key in keys))
    return result


def _presentation_anchors(catalog: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Choose the lower-median located structure marker in each dimension."""
    located: dict[str, list[tuple[str, dict[str, int]]]] = {}
    keys = ("minX", "maxX", "minZ", "maxZ")
    for structure in catalog.get("structures", []):
        selection = structure.get("selection", {}) if isinstance(structure, dict) else {}
        if selection.get("status") != "located":
            continue
        structure_id = structure.get("id")
        dimension = selection.get("dimension")
        bounds = selection.get("borderedBounds")
        if (
            not RESOURCE_LOCATION.fullmatch(structure_id or "")
            or not RESOURCE_LOCATION.fullmatch(dimension or "")
            or not isinstance(bounds, dict)
            or not all(isinstance(bounds.get(key), int) for key in keys)
        ):
            raise ValueError("Located structure has invalid presentation evidence")
        located.setdefault(dimension, []).append((structure_id, bounds))

    anchors: dict[str, dict[str, int]] = {}
    for dimension, structures in located.items():
        structures.sort(key=lambda value: value[0])
        _, bounds = structures[(len(structures) - 1) // 2]
        anchors[dimension] = {
            # BlueMap markers cover inclusive block bounds through max + 1.
            # This integer form matches JavaScript Math.round at the center.
            "x": (bounds["minX"] + bounds["maxX"] + 2) // 2,
            "z": (bounds["minZ"] + bounds["maxZ"] + 2) // 2,
        }
    return anchors


def _render_masks(
    render_masks: dict[str, Any], catalog: dict[str, Any]
) -> dict[str, list[dict[str, int]]]:
    if render_masks.get("schemaVersion") != 1:
        raise ValueError("Unsupported render-mask schemaVersion")
    for field in ("worldIdentity", "planFingerprint", "runtimeAttestationSha256"):
        if render_masks.get(field) != catalog.get(field):
            raise ValueError(f"Render-mask {field} does not match the catalog")
    values = render_masks.get("dimensions")
    if not isinstance(values, list):
        raise ValueError("Render-mask dimensions must be an array")
    masks_by_dimension: dict[str, list[dict[str, int]]] = {}
    keys = ("minX", "maxX", "minZ", "maxZ", "minY", "maxY")
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("Render-mask dimension entry must be an object")
        dimension = value.get("dimension")
        if not RESOURCE_LOCATION.fullmatch(dimension or ""):
            raise ValueError(f"Invalid render-mask dimension: {dimension!r}")
        masks = value.get("renderMask")
        if not isinstance(masks, list) or not masks:
            raise ValueError(f"Render masks are empty for {dimension}")
        checked: list[dict[str, int]] = []
        for mask in masks:
            if not isinstance(mask, dict) or not all(
                isinstance(mask.get(key), int) for key in keys
            ):
                raise ValueError(f"Invalid render mask for {dimension}")
            if (
                mask["minX"] > mask["maxX"]
                or mask["minZ"] > mask["maxZ"]
                or mask["minY"] > mask["maxY"]
            ):
                raise ValueError(f"Inverted render mask for {dimension}")
            checked.append({key: mask[key] for key in keys})
        if dimension in masks_by_dimension:
            raise ValueError(f"Duplicate render-mask dimension: {dimension}")
        checked.sort(key=lambda mask: tuple(mask[key] for key in keys))
        masks_by_dimension[dimension] = checked
    expected = _catalog_masks(catalog)
    if masks_by_dimension != expected:
        raise ValueError("Render masks do not exactly equal catalog borderedBounds")
    return masks_by_dimension


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _config_text(
    dimension: str,
    world: Path,
    storage: str,
    sorting: int,
    anchor: dict[str, int],
    masks: list[dict[str, int]],
) -> str:
    mask_lines = []
    for mask in masks:
        mask_lines.append(
            "  { min-x: %d, max-x: %d, min-z: %d, max-z: %d, "
            "min-y: %d, max-y: %d }"
            % (
                mask["minX"],
                mask["maxX"],
                mask["minZ"],
                mask["maxZ"],
                mask["minY"],
                mask["maxY"],
            )
        )
    return "\n".join(
        [
            "## Generated from structure-catalog.json. Do not rename this file.",
            f"world: {_quoted(str(world))}",
            f"dimension: {_quoted(dimension)}",
            f"name: {_quoted('ATMons 1.2.0 structures: ' + dimension)}",
            f"sorting: {sorting}",
            f"start-pos: {{ x: {anchor['x']}, z: {anchor['z']} }}",
            f"storage: {_quoted(storage)}",
            "min-inhabited-time: 0",
            "render-edges: false",
            "enable-perspective-view: true",
            "enable-flat-view: true",
            "enable-free-flight-view: true",
            "enable-hires: true",
            "render-mask: [",
            ",\n".join(mask_lines),
            "]",
            "",
        ]
    )


def generate(
    catalog_path: Path,
    render_masks_path: Path,
    config_root: Path,
    world: Path,
    storage: str,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    if not world.is_absolute():
        raise ValueError("--world must be an absolute server world-root path")
    if not MAP_ID.fullmatch(storage):
        raise ValueError("--storage must be a BlueMap-safe storage id")

    catalog = _read_json(catalog_path)
    dimensions = _dimensions(catalog)
    selected = _selected_dimensions(catalog)
    presentation_anchors = _presentation_anchors(catalog)
    render_masks = _read_json(render_masks_path)
    masks_by_dimension = _render_masks(render_masks, catalog)
    missing_catalog = selected.difference(dimensions)
    missing_masks = selected.difference(masks_by_dimension)
    missing_anchors = selected.difference(presentation_anchors)
    if missing_catalog:
        raise ValueError(f"Selected dimensions missing from catalog: {sorted(missing_catalog)}")
    if missing_masks:
        raise ValueError(f"Selected dimensions missing render masks: {sorted(missing_masks)}")
    if missing_anchors:
        raise ValueError(
            f"Selected dimensions missing presentation anchors: {sorted(missing_anchors)}"
        )

    maps: list[dict[str, Any]] = []
    for index, dimension in enumerate(sorted(selected)):
        map_id = safe_map_id(dimension)
        relative_config = Path("maps") / f"{map_id}.conf"
        config_path = config_root / relative_config
        _atomic_write(
            config_path,
            _config_text(
                dimension,
                world,
                storage,
                400 + index,
                presentation_anchors[dimension],
                masks_by_dimension[dimension],
            ),
        )
        maps.append(
            {
                "dimension": dimension,
                "mapId": map_id,
                "configFile": relative_config.as_posix(),
                "maskCount": len(masks_by_dimension[dimension]),
                "sizeBytes": config_path.stat().st_size,
                "sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
            }
        )

    manifest = {
        "schemaVersion": 1,
        "catalogSha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        "renderMasksSha256": hashlib.sha256(render_masks_path.read_bytes()).hexdigest(),
        "worldIdentity": catalog["worldIdentity"],
        "planFingerprint": catalog["planFingerprint"],
        "runtimeAttestationSha256": catalog["runtimeAttestationSha256"],
        "world": str(world),
        "storage": storage,
        "maps": maps,
    }
    output_manifest = manifest_path or config_root / "atmons-structure-maps.json"
    _atomic_write(
        output_manifest,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--render-masks", type=Path, required=True)
    parser.add_argument("--bluemap-config-root", type=Path, required=True)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--storage", default="file")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = generate(
            args.catalog,
            args.render_masks,
            args.bluemap_config_root,
            args.world,
            args.storage,
            args.manifest,
        )
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(manifest, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
