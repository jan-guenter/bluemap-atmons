#!/usr/bin/env python3
"""Compose every pinned add-on gallery into one collision-free datapack.

The source galleries intentionally use fixed absolute coordinates. This tool
copies their tracked datapacks, removes automatic load tags, translates world
coordinates and embedded absolute block positions, and emits a deterministic
layout/test plan. Source submodules are never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "versions" / "1.2.0" / "manifest.json"
VALIDATOR_PATH = ROOT / "tools" / "validate.py"
EXPECTED_MANIFEST_SHA256 = "cbc304b94475aaa82f502cc29fddcb35863f4490ce94ee450319f9d0a4faaa3f"
EXPECTED_VALIDATOR_SHA256 = "e4e5d66d4314c381a7a657065ff51a818f7f48e823eaa13b9b25f6366adef1ba"
NUMBER = r"-?\d+(?:\.\d+)?(?:[dDfF])?"
TRIPLE = rf"({NUMBER})\s+({NUMBER})\s+({NUMBER})"
INTEGER_TRIPLE = re.compile(r"\[I;(-?\d+),(-?\d+),(-?\d+)\]")
DOUBLE_TRIPLE = re.compile(
    r"(?P<prefix>\bPos:\[)(-?\d+(?:\.\d+)?)[dD],"
    r"(-?\d+(?:\.\d+)?)[dD],(-?\d+(?:\.\d+)?)[dD](?P<suffix>\])"
)
DISPLAY_TRIPLE = re.compile(r"\[(-?\d+)\s+(-?\d+)\s+(-?\d+)\]")
XYZ_OBJECT = re.compile(r"\bX:(-?\d+),Y:(-?\d+),Z:(-?\d+)")
SCALAR_SOURCE_POS = re.compile(
    r"(?P<x_prefix>\bsx:)(?P<x>-?\d+)(?P<y_prefix>,\s*sy:)"
    r"(?P<y>-?\d+)(?P<z_prefix>,\s*sz:)(?P<z>-?\d+)"
)
PACKED_POS = re.compile(r"(?P<prefix>\bAttachedPos:)(?P<value>-?\d+)L")
SELECTOR_AXIS = {
    axis: re.compile(rf"(?P<prefix>[\[,]{axis}=)(?P<value>{NUMBER})(?=[,\]])")
    for axis in "xyz"
}
WORLD_MIN_Y = -64
WORLD_MAX_Y = 319
PALETTE = (
    "minecraft:red_terracotta",
    "minecraft:orange_terracotta",
    "minecraft:yellow_terracotta",
    "minecraft:lime_terracotta",
    "minecraft:green_terracotta",
    "minecraft:cyan_terracotta",
    "minecraft:light_blue_terracotta",
    "minecraft:blue_terracotta",
    "minecraft:purple_terracotta",
    "minecraft:magenta_terracotta",
    "minecraft:pink_terracotta",
    "minecraft:brown_terracotta",
    "minecraft:white_terracotta",
    "minecraft:light_gray_terracotta",
    "minecraft:gray_terracotta",
    "minecraft:black_terracotta",
)
OUTPUT_MARKER = ".bluemap-atmons-gallery-output"
OUTPUT_MARKER_CONTENT = "owned by integration/galleries/compose.py\n"
COMPOSER_VERSION = "2.4.1"
FUNCTION_REFERENCE = re.compile(
    r"(?:^|\brun\s+)(?P<scheduled>schedule\s+)?function\s+"
    r"(?P<identifier>[a-z0-9_.-]+:[a-z0-9_./-]+)"
    r"(?:\s+(?P<delay>\d+)(?P<unit>[tsd]))?"
)


class CompositionError(RuntimeError):
    """A gallery cannot be composed without guessing."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Bounds:
    min_x: int
    min_y: int
    min_z: int
    max_x: int
    max_y: int
    max_z: int

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def depth(self) -> int:
        return self.max_z - self.min_z + 1

    def shifted(self, dx: int, dy: int, dz: int) -> "Bounds":
        return Bounds(
            self.min_x + dx,
            self.min_y + dy,
            self.min_z + dz,
            self.max_x + dx,
            self.max_y + dy,
            self.max_z + dz,
        )

    def contains(self, x: float, y: float, z: float, margin: int = 2) -> bool:
        return (
            self.min_x - margin <= x <= self.max_x + margin
            and self.min_y - margin <= y <= self.max_y + margin
            and self.min_z - margin <= z <= self.max_z + margin
        )

    def as_json(self) -> dict[str, int]:
        return {
            "minX": self.min_x,
            "minY": self.min_y,
            "minZ": self.min_z,
            "maxX": self.max_x,
            "maxY": self.max_y,
            "maxZ": self.max_z,
        }


@dataclass
class Gallery:
    component_id: str
    repository: str
    commit: str
    root: Path
    pack_root: Path
    namespace: str
    function_dir_name: str
    functions: list[Path]
    source_load_function: str | None
    source_bounds: Bounds
    objective: str | None


@dataclass(frozen=True)
class SettledVerifierNormalization:
    component_id: str
    commit: str
    relative_path: str
    original: str
    replacement: str


@dataclass(frozen=True)
class CumulativeScoreResetRule:
    component_id: str
    commit: str
    relative_path: str
    counters: tuple[tuple[str, str], ...]


SETTLED_VERIFIER_NORMALIZATIONS = (
    SettledVerifierNormalization(
        "pneumaticcraft",
        "3efe836cc5a362bb546a02c4ab9684de5ffb3add",
        "data/pneumaticcraft_gallery/function/verify.mcfunction",
        "execute unless block 194 100 200 "
        "pneumaticcraft:heat_pipe[east=true,west=true] run tellraw @a "
        '{"text":"gallery mismatch: heat-pipe-control","color":"red"}',
        "execute unless block 194 100 200 pneumaticcraft:heat_pipe run tellraw @a "
        '{"text":"gallery mismatch: heat-pipe-control","color":"red"}',
    ),
    SettledVerifierNormalization(
        "morered",
        "ec3880e823944f2fbd7318bde0950658538e429e",
        "data/morered_gallery/function/verify.mcfunction",
        "execute unless block 194 100 203 "
        "morered:hexidecrubrometer[face=floor,facing=north,power=15] run tellraw @a "
        '{"text":"gallery mismatch: hexidecrubrometer-power-15","color":"red"}',
        "execute unless block 194 100 203 "
        "morered:hexidecrubrometer[face=floor,facing=north] run tellraw @a "
        '{"text":"gallery mismatch: hexidecrubrometer-power-15","color":"red"}',
    ),
    SettledVerifierNormalization(
        "xnet",
        "3e650621695aba1aa67b268e91e9c1e1d307ab11",
        "data/xnet_gallery/function/verify.mcfunction",
        "execute unless block 194 100 175 "
        "xnet:netcable[color=red,north=none,south=none,east=block,west=cable,"
        "up=none,down=none,waterlogged=false] run tellraw @a "
        '{"text":"gallery mismatch: cable-red-block-ended","color":"red"}',
        "execute unless block 194 100 175 "
        "xnet:netcable[color=red,north=none,south=none,east=none,west=cable,"
        "up=none,down=none,waterlogged=false] run tellraw @a "
        '{"text":"gallery mismatch: cable-red-block-ended","color":"red"}',
    ),
    SettledVerifierNormalization(
        "xnet",
        "3e650621695aba1aa67b268e91e9c1e1d307ab11",
        "data/xnet_gallery/function/verify.mcfunction",
        "execute unless block 188 100 178 "
        "xnet:controller[error=true,facing=north] run tellraw @a "
        '{"text":"gallery mismatch: controller-error-north","color":"red"}',
        "execute unless block 188 100 178 "
        "xnet:controller[error=false,facing=north] run tellraw @a "
        '{"text":"gallery mismatch: controller-error-north","color":"red"}',
    ),
)

CUMULATIVE_SCORE_RESET_RULES = (
    CumulativeScoreResetRule(
        "ae2",
        "eff3a5dc33e69b0196dc18edb0045bfd4affe44e",
        "data/ae2_m3/function/build.mcfunction",
        (
            ("#m3f_builds", "ae2m3run"),
            ("#s1_builds", "ae2s1run"),
            ("#m45_builds", "ae2m45run"),
            ("#appmek_builds", "ae2amrun"),
        ),
    ),
    CumulativeScoreResetRule(
        "factory-blocks",
        "ad403575652e11d9b676d4af690d00bc676bf9ac",
        "data/factory_blocks_gallery/function/build.mcfunction",
        (("#builds", "fb_gallery"),),
    ),
    CumulativeScoreResetRule(
        "laserio",
        "28e45556464f803ca730de4358704a1654d4ebb0",
        "data/laserio_gallery/function/build.mcfunction",
        (("#builds", "laserio_glr"),),
    ),
    CumulativeScoreResetRule(
        "rftools-builder",
        "ed979af9b295ca3411903e98df95af9f5bb6ea16",
        "data/rftools_builder_gallery/function/build.mcfunction",
        (("#builds", "rftb_gallery"),),
    ),
    CumulativeScoreResetRule(
        "enderio",
        "97141a036a8374ce2de3ba6a9f5ac0f937d0bbc7",
        "data/enderio_gallery/function/build.mcfunction",
        (("#builds", "enderio_gallery"),),
    ),
    CumulativeScoreResetRule(
        "modular-routers",
        "da5686a6b7f79a4c5468793ae48baa2907855ab7",
        "data/modularrouters_gallery/function/build.mcfunction",
        (("#builds", "mr_gallery"),),
    ),
    CumulativeScoreResetRule(
        "securitycraft",
        "1ebddc5fa3db68630604983eeeae9a0a076be20d",
        "data/securitycraft_gallery/function/build.mcfunction",
        (("#builds", "sc_gallery"),),
    ),
    CumulativeScoreResetRule(
        "functional-storage",
        "737c13e823c883229f0bc45e8ba512ba77b803e7",
        "data/functionalstorage_gallery/function/build_once.mcfunction",
        (("#builds", "fs_gallery"),),
    ),
    CumulativeScoreResetRule(
        "logistics-networks",
        "d5a9ebb2702b217c8f671cc2ea489b73a52f7766",
        "data/logisticsnetworks_gallery/function/build_loaded.mcfunction",
        (("#builds", "ln_gallery"),),
    ),
)


XNET_SETTLED_TOPOLOGY_COMMIT = "3e650621695aba1aa67b268e91e9c1e1d307ab11"
XNET_SETTLED_TOPOLOGY_ANCHOR = "function xnet_gallery:verify"
XNET_SETTLED_TOPOLOGY = (
    "# Integration-only stable XNet topology; source gallery remains immutable.",
    "setblock 178 100 175 xnet:netcable[color=red]",
    "setblock 180 100 175 xnet:netcable[color=red]",
    "setblock 179 100 175 xnet:netcable[color=red,north=none,south=none,east=cable,west=cable,up=none,down=none,waterlogged=false]",
    "setblock 182 100 174 xnet:netcable[color=yellow]",
    "setblock 183 100 175 xnet:netcable[color=yellow]",
    "setblock 182 100 175 xnet:netcable[color=yellow,north=cable,south=none,east=cable,west=none,up=none,down=none,waterlogged=false]",
    "setblock 185 100 174 xnet:netcable[color=green]",
    "setblock 186 100 175 xnet:netcable[color=green]",
    "setblock 184 100 175 xnet:netcable[color=green]",
    "setblock 185 100 175 xnet:netcable[color=green,north=cable,south=none,east=cable,west=cable,up=none,down=none,waterlogged=false]",
    "setblock 188 100 174 xnet:netcable[color=routing]",
    "setblock 188 100 176 xnet:netcable[color=routing]",
    "setblock 187 100 175 xnet:netcable[color=routing]",
    "setblock 189 100 175 xnet:netcable[color=routing]",
    "setblock 188 100 175 xnet:netcable[color=routing,north=cable,south=cable,east=cable,west=cable,up=none,down=none,waterlogged=false]",
    "setblock 191 99 175 xnet:netcable[color=blue]",
    "setblock 191 101 175 xnet:netcable[color=blue]",
    "setblock 191 100 175 xnet:netcable[color=blue,north=none,south=none,east=none,west=none,up=cable,down=cable,waterlogged=false]",
    "setblock 193 100 175 xnet:netcable[color=red]",
    "setblock 194 100 175 xnet:netcable[color=red,north=none,south=none,east=none,west=cable,up=none,down=none,waterlogged=false]",
    "setblock 176 100 177 minecraft:chest",
    "setblock 176 100 179 xnet:netcable[color=green]",
    "setblock 176 100 178 xnet:connector[color=green,north=block,south=cable,east=none,west=none,up=none,down=none,waterlogged=false]",
    "setblock 178 100 178 minecraft:chest",
    "setblock 180 100 178 xnet:netcable[color=yellow]",
    "setblock 179 100 178 xnet:advanced_connector[color=yellow,north=none,south=none,east=cable,west=block,up=none,down=none,waterlogged=false]",
    "setblock 182 100 177 xnet:netcable[color=blue]",
    "setblock 182 100 179 xnet:netcable[color=blue]",
    'setblock 182 100 178 xnet:facade[color=blue,north=cable,south=cable,east=none,west=none,up=none,down=none,waterlogged=false]{"neoforge:attachments":{"xnet:mimic_data":{state:{Name:"minecraft:bricks"}}}}',
    "setblock 184 100 178 xnet:netcable[color=routing]",
    "setblock 186 100 178 xnet:netcable[color=routing]",
    'setblock 185 100 178 xnet:facade[color=routing,north=none,south=none,east=cable,west=cable,up=none,down=none,waterlogged=false]{"neoforge:attachments":{"xnet:mimic_data":{state:{Name:"minecraft:oak_log",Properties:{axis:"x"}}}}}',
    "setblock 194 101 178 xnet:antenna_base",
    "setblock 194 102 178 xnet:antenna[facing=north]",
)


def git_lines(cwd: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise CompositionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.splitlines()


def git_bytes(cwd: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise CompositionError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or f"git {' '.join(args)} failed"
        )
    return result.stdout


def load_manifest(path: Path) -> dict:
    if sha256_file(DEFAULT_MANIFEST) != EXPECTED_MANIFEST_SHA256:
        raise CompositionError(
            "tracked ATMons 1.2.0 manifest differs from its immutable released-profile digest"
        )
    if sha256_file(VALIDATOR_PATH) != EXPECTED_VALIDATOR_SHA256:
        raise CompositionError(
            "shared manifest validator differs from its reviewed immutable digest"
        )
    spec = importlib.util.spec_from_file_location("bluemap_atmons_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise CompositionError("cannot load the repository manifest validator")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    try:
        errors, value = validator.validate_manifest(path)
    except (OSError, ValueError) as exc:
        raise CompositionError(f"cannot validate manifest {path}: {exc}") from exc
    if errors or value is None:
        raise CompositionError("invalid compatibility manifest: " + "; ".join(errors))
    if value.get("atmons", {}).get("version") != "1.2.0":
        raise CompositionError("this integration profile is exact to All the Mons 1.2.0")
    if path.read_bytes() != DEFAULT_MANIFEST.read_bytes():
        raise CompositionError(
            "gallery composition requires the byte-exact tracked ATMons 1.2.0 manifest"
        )
    return value


def attest_gallery_tree(addon_root: Path, commit: str, component_id: str) -> list[str]:
    indexed = git_lines(
        addon_root,
        "ls-tree",
        "-r",
        "--name-only",
        commit,
        "--",
        "gallery/datapack",
    )
    if not indexed:
        raise CompositionError(f"{component_id}: tracked gallery datapack is missing")
    pack_root = addon_root / "gallery" / "datapack"
    actual = sorted(
        path.relative_to(addon_root).as_posix()
        for path in pack_root.rglob("*")
        if path.is_file()
    )
    if actual != indexed:
        missing = sorted(set(indexed).difference(actual))[:10]
        extra = sorted(set(actual).difference(indexed))[:10]
        raise CompositionError(
            f"{component_id}: gallery filesystem differs from pinned Git tree; "
            f"missing={missing}, extra={extra}"
        )
    for relative in indexed:
        path = addon_root / relative
        if path.is_symlink() or path.read_bytes() != git_bytes(
            addon_root, "show", f"{commit}:{relative}"
        ):
            raise CompositionError(
                f"{component_id}: gallery file differs from pinned commit: {relative}"
            )
    return indexed


def parse_number(value: str) -> float:
    return float(re.sub(r"[dDfF]$", "", value))


def format_shifted(value: str, delta: int) -> str:
    suffix = value[-1] if value[-1:] in "dDfF" else ""
    raw = value[:-1] if suffix else value
    shifted = float(raw) + delta
    if "." not in raw:
        return f"{int(shifted)}{suffix}"
    decimals = len(raw.partition(".")[2])
    return f"{shifted:.{decimals}f}{suffix}"


def command_points(line: str) -> Iterator[tuple[float, float, float]]:
    """Yield explicit absolute command positions from one function line."""
    if not line or line.lstrip().startswith("#"):
        return

    prefix_patterns = (
        rf"\bsetblock\s+{TRIPLE}",
        rf"\bdata\s+(?:merge|get|modify|remove)\s+block\s+{TRIPLE}",
        rf"\bitem\s+(?:replace|modify)\s+block\s+{TRIPLE}",
        rf"\bsummon\s+\S+\s+{TRIPLE}",
        rf"\bplace\s+(?:feature|structure|template)\s+\S+\s+{TRIPLE}",
        rf"\bplace\s+jigsaw\s+\S+\s+\S+\s+\S+\s+{TRIPLE}",
        rf"\b(?:tp|teleport)\s+\S+\s+{TRIPLE}",
        rf"\bpositioned\s+{TRIPLE}",
        rf"\b(?:if|unless)\s+(?:block|data\s+block)\s+{TRIPLE}",
        rf"\bstore\s+(?:result|success)\s+block\s+{TRIPLE}",
        rf"\blogisticsnetworks\s+\S+\s+{TRIPLE}",
    )
    for pattern in prefix_patterns:
        for match in re.finditer(pattern, line):
            values = match.groups()[-3:]
            point = tuple(parse_number(value) for value in values)
            if WORLD_MIN_Y <= point[1] <= WORLD_MAX_Y:
                yield point  # type: ignore[misc]

    for keyword, triples in (("fill", 2), ("clone", 3), ("blocks", 3)):
        pattern = rf"\b{keyword}\s+" + r"\s+".join([TRIPLE] * triples)
        for match in re.finditer(pattern, line):
            values = match.groups()
            for index in range(0, len(values), 3):
                point = tuple(parse_number(value) for value in values[index : index + 3])
                if WORLD_MIN_Y <= point[1] <= WORLD_MAX_Y:
                    yield point  # type: ignore[misc]

    selector_values: dict[str, float] = {}
    for axis, pattern in SELECTOR_AXIS.items():
        match = pattern.search(line)
        if match:
            selector_values[axis] = parse_number(match.group("value"))
    if set(selector_values) == {"x", "y", "z"}:
        yield selector_values["x"], selector_values["y"], selector_values["z"]


def bounds_for(functions: Iterable[Path]) -> Bounds:
    points: list[tuple[float, float, float]] = []
    lines: list[str] = []
    for path in functions:
        file_lines = path.read_text(encoding="utf-8").splitlines()
        lines.extend(file_lines)
        for line in file_lines:
            points.extend(command_points(line))
    if not points:
        raise CompositionError("gallery contains no explicit absolute block positions")

    initial = Bounds(
        math.floor(min(point[0] for point in points)),
        math.floor(min(point[1] for point in points)),
        math.floor(min(point[2] for point in points)),
        math.ceil(max(point[0] for point in points)),
        math.ceil(max(point[1] for point in points)),
        math.ceil(max(point[2] for point in points)),
    )
    # Embedded positions can extend the explicit command bounds. Only accept
    # triples near the explicit fixture; this excludes relative vectors and UUIDs.
    for line in lines:
        for match in INTEGER_TRIPLE.finditer(line):
            point = tuple(int(value) for value in match.groups())
            if initial.contains(*point, margin=128):
                points.append(point)
        for match in DOUBLE_TRIPLE.finditer(line):
            point = tuple(float(match.group(index)) for index in (2, 3, 4))
            if initial.contains(*point, margin=128):
                points.append(point)
        for match in XYZ_OBJECT.finditer(line):
            point = tuple(int(value) for value in match.groups())
            if initial.contains(*point, margin=128):
                points.append(point)

    return Bounds(
        math.floor(min(point[0] for point in points)),
        math.floor(min(point[1] for point in points)),
        math.floor(min(point[2] for point in points)),
        math.ceil(max(point[0] for point in points)),
        math.ceil(max(point[1] for point in points)),
        math.ceil(max(point[2] for point in points)),
    )


def discover_galleries(manifest: dict) -> list[Gallery]:
    galleries: list[Gallery] = []
    for component in manifest["components"]:
        if component["kind"] != "addon":
            continue
        addon_root = ROOT / component["submodule_path"]
        actual_commit = git_lines(addon_root, "rev-parse", "HEAD")[0]
        if actual_commit != component["commit"]:
            raise CompositionError(
                f"{component['id']}: submodule is {actual_commit}, manifest pins {component['commit']}"
            )
        attest_gallery_tree(addon_root, component["commit"], component["id"])
        pack_root = addon_root / "gallery" / "datapack"
        candidates: list[tuple[str, str, Path]] = []
        for directory_name in ("function", "functions"):
            for path in sorted((pack_root / "data").glob(f"*/{directory_name}/build.mcfunction")):
                if path.parts[-3] != "minecraft":
                    candidates.append((path.parts[-3], directory_name, path))
        if len(candidates) != 1:
            raise CompositionError(
                f"{component['id']}: expected one gallery build function, found {len(candidates)}"
            )
        namespace, function_dir_name, _build = candidates[0]
        function_root = pack_root / "data" / namespace / function_dir_name
        functions = sorted(function_root.rglob("*.mcfunction"))
        source_load = function_root / "load.mcfunction"
        objective = None
        objective_pattern = re.compile(r"scoreboard\s+players\s+(?:set|add)\s+#failures\s+(\S+)")
        for path in functions:
            for match in objective_pattern.finditer(path.read_text(encoding="utf-8")):
                objective = match.group(1)
                break
            if objective:
                break
        galleries.append(
            Gallery(
                component_id=component["id"],
                repository=component["repository"],
                commit=component["commit"],
                root=addon_root,
                pack_root=pack_root,
                namespace=namespace,
                function_dir_name=function_dir_name,
                functions=functions,
                source_load_function=f"{namespace}:load" if source_load.is_file() else None,
                source_bounds=bounds_for(functions),
                objective=objective,
            )
        )
    if len(galleries) != manifest["release"]["addon_count"]:
        raise CompositionError("gallery count does not match manifest add-on count")
    return galleries


def translate_triple_match(match: re.Match[str], offsets: tuple[int, int, int]) -> str:
    groups = match.groups()
    prefix_count = len(groups) - 3
    prefix = "".join(group or "" for group in groups[:prefix_count])
    shifted = [format_shifted(value, delta) for value, delta in zip(groups[-3:], offsets)]
    return prefix + " ".join(shifted)


def translate_prefixed_triple(
    line: str, pattern: str, offsets: tuple[int, int, int]
) -> str:
    compiled = re.compile(rf"({pattern}){TRIPLE}")
    return compiled.sub(lambda match: translate_triple_match(match, offsets), line)


def translate_multi_triple(
    line: str, keyword_pattern: str, count: int, offsets: tuple[int, int, int]
) -> str:
    pattern = re.compile(
        rf"(?P<prefix>\b(?:{keyword_pattern})\s+)" + r"\s+".join([TRIPLE] * count)
    )

    def replace(match: re.Match[str]) -> str:
        values = match.groups()[1:]
        result = []
        for index, value in enumerate(values):
            result.append(format_shifted(value, offsets[index % 3]))
        return match.group("prefix") + " ".join(result)

    return pattern.sub(replace, line)


def unpack_block_pos(value: int) -> tuple[int, int, int]:
    unsigned = value & ((1 << 64) - 1)
    x = unsigned >> 38
    z = (unsigned >> 12) & 0x3FFFFFF
    y = unsigned & 0xFFF
    if x >= 1 << 25:
        x -= 1 << 26
    if z >= 1 << 25:
        z -= 1 << 26
    if y >= 1 << 11:
        y -= 1 << 12
    return x, y, z


def pack_block_pos(x: int, y: int, z: int) -> int:
    unsigned = ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF)
    return unsigned - (1 << 64) if unsigned >= 1 << 63 else unsigned


def translate_line(line: str, bounds: Bounds, dx: int, dy: int, dz: int) -> str:
    offsets = (dx, dy, dz)

    # Embedded absolute positions must move with their owning block entities.
    def integer_array(match: re.Match[str]) -> str:
        point = tuple(int(value) for value in match.groups())
        if not bounds.contains(*point, margin=128):
            return match.group(0)
        return f"[I;{point[0] + dx},{point[1] + dy},{point[2] + dz}]"

    line = INTEGER_TRIPLE.sub(integer_array, line)

    def double_array(match: re.Match[str]) -> str:
        point = tuple(float(match.group(index)) for index in (2, 3, 4))
        if not bounds.contains(*point, margin=128):
            return match.group(0)
        values = [f"{value + delta:.1f}d" for value, delta in zip(point, offsets)]
        return match.group("prefix") + ",".join(values) + match.group("suffix")

    line = DOUBLE_TRIPLE.sub(double_array, line)

    def xyz_object(match: re.Match[str]) -> str:
        point = tuple(int(value) for value in match.groups())
        if not bounds.contains(*point, margin=128):
            return match.group(0)
        return f"X:{point[0] + dx},Y:{point[1] + dy},Z:{point[2] + dz}"

    line = XYZ_OBJECT.sub(xyz_object, line)

    def scalar_source_position(match: re.Match[str]) -> str:
        point = tuple(int(match.group(axis)) for axis in "xyz")
        if not bounds.contains(*point, margin=128):
            return match.group(0)
        shifted = tuple(value + delta for value, delta in zip(point, offsets))
        return (
            f"{match.group('x_prefix')}{shifted[0]}"
            f"{match.group('y_prefix')}{shifted[1]}"
            f"{match.group('z_prefix')}{shifted[2]}"
        )

    line = SCALAR_SOURCE_POS.sub(scalar_source_position, line)

    def display_position(match: re.Match[str]) -> str:
        point = tuple(int(value) for value in match.groups())
        if not bounds.contains(*point, margin=128):
            return match.group(0)
        return f"[{point[0] + dx} {point[1] + dy} {point[2] + dz}]"

    line = DISPLAY_TRIPLE.sub(display_position, line)

    def packed_position(match: re.Match[str]) -> str:
        point = unpack_block_pos(int(match.group("value")))
        if not bounds.contains(*point, margin=128):
            return match.group(0)
        shifted = pack_block_pos(point[0] + dx, point[1] + dy, point[2] + dz)
        return f"{match.group('prefix')}{shifted}L"

    line = PACKED_POS.sub(packed_position, line)

    for axis, delta in zip("xyz", offsets):
        line = SELECTOR_AXIS[axis].sub(
            lambda match, d=delta: match.group("prefix")
            + format_shifted(match.group("value"), d),
            line,
        )

    prefixes = (
        r"\bsetblock\s+",
        r"\bdata\s+(?:merge|get|modify|remove)\s+block\s+",
        r"\bitem\s+(?:replace|modify)\s+block\s+",
        r"\bsummon\s+\S+\s+",
        r"\bplace\s+(?:feature|structure|template)\s+\S+\s+",
        r"\bplace\s+jigsaw\s+\S+\s+\S+\s+\S+\s+",
        r"\b(?:tp|teleport)\s+\S+\s+",
        r"\bpositioned\s+",
        r"\b(?:if|unless)\s+(?:block|data\s+block)\s+",
        r"\bstore\s+(?:result|success)\s+block\s+",
        r"\blogisticsnetworks\s+\S+\s+",
    )
    for prefix in prefixes:
        line = translate_prefixed_triple(line, prefix, offsets)
    line = translate_multi_triple(line, "fill", 2, offsets)
    line = translate_multi_triple(line, "clone", 3, offsets)
    line = translate_multi_triple(line, "(?:if|unless)\\s+blocks", 3, offsets)

    pair_pattern = re.compile(
        rf"(?P<prefix>\bforceload\s+(?:add|remove)\s+)"
        rf"({NUMBER})\s+({NUMBER})(?:\s+({NUMBER})\s+({NUMBER}))?"
    )

    def forceload_pair(match: re.Match[str]) -> str:
        values = [match.group(index) for index in range(2, 6)]
        result = [
            format_shifted(values[0], dx),
            format_shifted(values[1], dz),
        ]
        if values[2] is not None:
            result.extend(
                [format_shifted(values[2], dx), format_shifted(values[3], dz)]
            )
        return match.group("prefix") + " ".join(result)

    return pair_pattern.sub(forceload_pair, line)


def layout_galleries(
    galleries: list[Gallery], origin_x: int, origin_z: int, row_width: int, padding: int
) -> list[dict]:
    if row_width < max(gallery.source_bounds.width + 2 * padding for gallery in galleries):
        raise CompositionError("row width is smaller than the widest gallery")
    # Deep fixtures first keeps the resulting plane compact and deterministic.
    ordered = sorted(
        galleries,
        key=lambda gallery: (-gallery.source_bounds.depth, -gallery.source_bounds.width, gallery.component_id),
    )
    cursor_x = origin_x
    cursor_z = origin_z
    row_depth = 0
    result: list[dict] = []
    for gallery in ordered:
        tile_width = gallery.source_bounds.width + 2 * padding
        tile_depth = gallery.source_bounds.depth + 2 * padding
        if cursor_x != origin_x and cursor_x + tile_width > origin_x + row_width:
            cursor_x = origin_x
            cursor_z += row_depth
            row_depth = 0
        tile = Bounds(cursor_x, 0, cursor_z, cursor_x + tile_width - 1, 0, cursor_z + tile_depth - 1)
        content_min_x = cursor_x + padding
        content_min_z = cursor_z + padding
        dx = content_min_x - gallery.source_bounds.min_x
        dz = content_min_z - gallery.source_bounds.min_z
        result.append(
            {
                "gallery": gallery,
                "dx": dx,
                "dz": dz,
                "tile": tile,
            }
        )
        cursor_x += tile_width
        row_depth = max(row_depth, tile_depth)
    return result


def chunked_fill(
    min_x: int,
    min_y: int,
    min_z: int,
    max_x: int,
    max_y: int,
    max_z: int,
    block: str,
    max_volume: int = 30_000,
) -> Iterator[str]:
    height = max_y - min_y + 1
    side = max(1, int(math.sqrt(max_volume / max(1, height))))
    for x in range(min_x, max_x + 1, side):
        for z in range(min_z, max_z + 1, side):
            yield (
                f"fill {x} {min_y} {z} {min(x + side - 1, max_x)} {max_y} "
                f"{min(z + side - 1, max_z)} {block}"
            )


def forceload_commands(bounds: Bounds, operation: str) -> Iterator[str]:
    """Cover a tile with bounded 16x16-chunk force-load operations."""
    if operation not in {"add", "remove"}:
        raise ValueError(f"unsupported force-load operation: {operation}")
    min_chunk_x = bounds.min_x // 16
    max_chunk_x = bounds.max_x // 16
    min_chunk_z = bounds.min_z // 16
    max_chunk_z = bounds.max_z // 16
    # One command may affect at most 256 chunks. Keeping each axis at 16 or
    # fewer makes that bound explicit even for the largest source gallery.
    for chunk_x in range(min_chunk_x, max_chunk_x + 1, 16):
        for chunk_z in range(min_chunk_z, max_chunk_z + 1, 16):
            end_chunk_x = min(chunk_x + 15, max_chunk_x)
            end_chunk_z = min(chunk_z + 15, max_chunk_z)
            yield (
                f"forceload {operation} {chunk_x * 16} {chunk_z * 16} "
                f"{end_chunk_x * 16 + 15} {end_chunk_z * 16 + 15}"
            )


def forceload_add_extent(line: str) -> tuple[int, int, int, int] | None:
    match = re.search(
        rf"\bforceload\s+add\s+({NUMBER})\s+({NUMBER})"
        rf"(?:\s+({NUMBER})\s+({NUMBER}))?",
        line,
    )
    if not match:
        return None
    x1, z1 = (math.floor(parse_number(match.group(index))) for index in (1, 2))
    x2 = math.floor(parse_number(match.group(3))) if match.group(3) else x1
    z2 = math.floor(parse_number(match.group(4))) if match.group(4) else z1
    return min(x1, x2), min(z1, z2), max(x1, x2), max(z1, z2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_settled_verifier_line(
    gallery: Gallery,
    source: Path,
    line: str,
    hits: list[int],
) -> str:
    """Normalize only exact synthetic predicates that cannot survive one tick."""
    relative = source.relative_to(gallery.pack_root).as_posix()
    for index, rule in enumerate(SETTLED_VERIFIER_NORMALIZATIONS):
        if (
            gallery.component_id == rule.component_id
            and gallery.commit == rule.commit
            and relative == rule.relative_path
            and line == rule.original
        ):
            hits[index] += 1
            return rule.replacement
    return line


def settled_build_lines(
    gallery: Gallery,
    source: Path,
    line: str,
) -> tuple[tuple[str, ...], bool]:
    """Add exact valid XNet neighbors before its aggregate terminal verifier."""
    relative = source.relative_to(gallery.pack_root).as_posix()
    if (
        gallery.component_id == "xnet"
        and gallery.commit == XNET_SETTLED_TOPOLOGY_COMMIT
        and relative == "data/xnet_gallery/function/build.mcfunction"
        and line == XNET_SETTLED_TOPOLOGY_ANCHOR
    ):
        return (*XNET_SETTLED_TOPOLOGY, line), True
    return (line,), False


def cumulative_score_reset_lines(gallery: Gallery) -> list[str]:
    """Reset exact native invocation counters before an aggregate rerun."""
    matches = [
        rule
        for rule in CUMULATIVE_SCORE_RESET_RULES
        if rule.component_id == gallery.component_id
    ]
    if not matches:
        return []
    if len(matches) != 1:
        raise CompositionError(
            f"{gallery.component_id}: cumulative score reset rule is ambiguous"
        )
    rule = matches[0]
    if gallery.commit != rule.commit:
        raise CompositionError(
            f"{gallery.component_id}: cumulative score reset requires a fresh "
            "exact-source review"
        )

    build_path = gallery.pack_root / rule.relative_path
    build_text = build_path.read_text(encoding="utf-8")
    for player, objective in rule.counters:
        increment = f"scoreboard players add {player} {objective} 1"
        hits = build_text.count(increment)
        if hits != 1:
            raise CompositionError(
                f"{gallery.component_id}: expected one native cumulative counter "
                f"increment for "
                f"{player} {objective}, found {hits}"
            )

    lines = ["# Reset exact native invocation counters for repeatable aggregate runs."]
    for objective in dict.fromkeys(
        objective for _player, objective in rule.counters
    ):
        lines.append(f"scoreboard objectives add {objective} dummy")
    lines.extend(
        f"scoreboard players set {player} {objective} 0"
        for player, objective in rule.counters
    )
    return lines


def composition_identity(
    manifest_path: Path,
    galleries: list[Gallery],
    options: dict[str, int],
) -> str:
    digest = hashlib.sha256()
    digest.update(f"bluemap-atmons-gallery-composer:{COMPOSER_VERSION}\0".encode())
    digest.update(hashlib.sha256(manifest_path.read_bytes()).digest())
    digest.update(json.dumps(options, sort_keys=True, separators=(",", ":")).encode())
    for gallery in sorted(galleries, key=lambda value: value.component_id):
        digest.update(f"\0{gallery.component_id}\0{gallery.commit}\0".encode())
        for path in sorted(gallery.functions):
            relative = path.relative_to(gallery.root).as_posix()
            digest.update(relative.encode())
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def write_owned_sibling(path: Path, content: str, replacing_owned: bool) -> None:
    ownership = path.with_name(path.name + ".bluemap-atmons-owned")
    if path.exists() and (
        not replacing_owned
        or not ownership.is_file()
        or ownership.read_text(encoding="utf-8") != OUTPUT_MARKER_CONTENT
    ):
        raise CompositionError(f"refusing to replace unowned generated file: {path}")
    write_text(path, content)
    write_text(ownership, OUTPUT_MARKER_CONTENT)


def mirrored_failure_command(line: str, player: str) -> str | None:
    """Mirror a source gallery failure branch into the integration scoreboard."""
    branch, separator, tail = line.rpartition(" run ")
    if not separator or not re.search(r"^\s*execute\b.*\b(?:if|unless)\b", branch):
        return None
    lower = tail.lower()
    native_failure = re.search(
        r"^scoreboard\s+players\s+add\s+#failures\s+\S+\s+[1-9]\d*\s*$", tail
    )
    visible_failure = (
        bool(re.match(r"\s*(?:tellraw|say)\b", lower))
        and ("fail" in lower or "mismatch" in lower or "missing" in lower or '"color":"red"' in lower)
    )
    if not native_failure and not visible_failure:
        return None
    command = f"scoreboard players add {player} bma_test 1"
    return f"{branch}{separator}{command}"


def mirrored_positive_commands(line: str, player: str) -> list[str]:
    """Turn positive-only gallery assertions into explicit failure branches."""
    lower = line.lower()
    if "tellraw" not in lower or '"color":"green"' not in lower:
        return []
    predicate = re.compile(
        rf"\bif\s+(?P<kind>block|data\s+block)\s+{TRIPLE}\s+"
        rf"(?P<expected>.+?)(?=\s+if\s+(?:block|data\s+block)\s+|\s+run\s+)"
    )
    result = []
    for match in predicate.finditer(line):
        x, y, z = match.group(2), match.group(3), match.group(4)
        result.append(
            f"execute unless {match.group('kind')} {x} {y} {z} {match.group('expected')} "
            f"run scoreboard players add {player} bma_test 1"
        )
    return result


def expected_setblock_check(line: str, player: str) -> str | None:
    """Return a lightweight final block/state check for a build placement."""
    match = re.search(rf"\bsetblock\s+{TRIPLE}\s+(\S+)", line)
    if not match:
        return None
    block = match.group(4).split("{", 1)[0]
    block_id = block.split("[", 1)[0]
    if block_id in {"air", "minecraft:air", "cave_air", "minecraft:cave_air"}:
        return None
    return (
        f"execute unless block {match.group(1)} {match.group(2)} {match.group(3)} {block} "
        f"run scoreboard players add {player} bma_test 1"
    )


def fixed_completion_delay_ticks(gallery: Gallery) -> int | None:
    """Return a game-tick completion barrier for an acyclic gallery build.

    AE2 deliberately retries a settle function until its live state stabilizes,
    so its terminal predicates are instrumented instead of guessed here.
    """
    if gallery.component_id == "ae2":
        return None
    function_root = gallery.pack_root / "data" / gallery.namespace / gallery.function_dir_name
    sources = {
        f"{gallery.namespace}:{path.relative_to(function_root).with_suffix('').as_posix()}": path
        for path in gallery.functions
    }
    root = f"{gallery.namespace}:build"
    if root not in sources:
        raise CompositionError(f"{gallery.component_id}: build function is absent")

    memo: dict[str, int] = {}

    def visit(identifier: str, stack: tuple[str, ...]) -> int:
        if identifier in memo:
            return memo[identifier]
        if identifier in stack:
            chain = " -> ".join((*stack, identifier))
            raise CompositionError(
                f"{gallery.component_id}: scheduled completion graph has a cycle: {chain}"
            )
        maximum = 0
        for line in sources[identifier].read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            for match in FUNCTION_REFERENCE.finditer(line):
                target = match.group("identifier")
                if target not in sources:
                    continue
                delay = 0
                if match.group("scheduled"):
                    value = int(match.group("delay") or "0")
                    delay = value * {"t": 1, "s": 20, "d": 24_000}[
                        match.group("unit") or "t"
                    ]
                maximum = max(maximum, delay + visit(target, (*stack, identifier)))
        memo[identifier] = maximum
        return maximum

    # One extra tick ensures the barrier runs after a terminal function that
    # was scheduled for the same tick.
    return max(1, visit(root, ()) + 1)


def ae2_completion_command(line: str, player: str) -> str | None:
    """Mirror either terminal AE2 settle predicate into the done objective."""
    branch, separator, tail = line.rpartition(" run ")
    if not separator:
        return None
    stable = (
        "if score #stable ae2m3s matches 2.." in branch
        and tail.strip() == "function ae2_m3:verify"
    )
    exhausted = (
        "if score #attempts ae2m3s matches 60.." in branch
        and tail.lstrip().startswith("tellraw ")
    )
    if not stable and not exhausted:
        return None
    return f"{branch}{separator}scoreboard players set {player} bma_done 1"


def compose(
    manifest_path: Path,
    output: Path,
    origin_x: int,
    origin_z: int,
    row_width: int,
    padding: int,
    minimum_y: int,
) -> tuple[Path, Path]:
    manifest = load_manifest(manifest_path)
    galleries = discover_galleries(manifest)
    options = {
        "originX": origin_x,
        "originZ": origin_z,
        "rowWidth": row_width,
        "padding": padding,
        "minimumY": minimum_y,
    }
    composition_id = composition_identity(manifest_path, galleries, options)
    layout = layout_galleries(galleries, origin_x, origin_z, row_width, padding)
    output = output.resolve()
    forbidden = {Path("/"), Path.home().resolve(), ROOT.resolve()}
    if output in forbidden or output in ROOT.resolve().parents:
        raise CompositionError(
            "output must be a dedicated directory outside the repository and home/root targets"
        )
    marker = output / OUTPUT_MARKER
    previously_owned = output.exists()
    if output.exists():
        if not marker.is_file() or marker.read_text(encoding="utf-8") != OUTPUT_MARKER_CONTENT:
            raise CompositionError(f"refusing to replace unowned output directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    write_text(marker, OUTPUT_MARKER_CONTENT)
    write_text(
        output / "pack.mcmeta",
        json.dumps(
            {
                "pack": {
                    "pack_format": 48,
                    "description": "BlueMap ATMons 1.2.0 combined integration galleries",
                }
            },
            indent=2,
        )
        + "\n",
    )

    records: list[dict] = []
    prepare_lines = [
        "# Generated by integration/galleries/compose.py; do not edit.",
        "gamerule doDaylightCycle false",
        "gamerule doWeatherCycle false",
        "gamerule randomTickSpeed 0",
        "gamerule doMobSpawning false",
        "gamerule doPatrolSpawning false",
        "gamerule doTraderSpawning false",
        "gamerule doWardenSpawning false",
        "gamerule doInsomnia false",
        "gamerule disableRaids true",
        "gamerule doFireTick false",
        "gamerule fallDamage false",
        "gamerule drowningDamage false",
        "gamerule freezeDamage false",
        "gamerule globalSoundEvents false",
        "scoreboard objectives add bma_test dummy",
        "scoreboard objectives add bma_done dummy",
        "weather clear",
        "time set noon",
    ]
    build_all: list[str] = ["# Run individual wrappers with the external test runner."]
    verify_all: list[str] = ["# Run individual wrappers with the external test runner."]
    prepare_all: list[str] = ["function bluemap_atmons:prepare"]
    normalization_hits = [0] * len(SETTLED_VERIFIER_NORMALIZATIONS)
    xnet_topology_hits = 0

    for index, entry in enumerate(layout):
        gallery: Gallery = entry["gallery"]
        safe_id = gallery.component_id.replace("-", "_")
        failure_player = f"#{safe_id}"
        completion_player = f"#{safe_id}"
        completion_delay_ticks = fixed_completion_delay_ticks(gallery)
        mirrored_checks = 0
        fallback_checks: list[str] = []
        dx, dz = entry["dx"], entry["dz"]
        dy = minimum_y - gallery.source_bounds.min_y
        translated = gallery.source_bounds.shifted(dx, dy, dz)
        tile: Bounds = entry["tile"]
        tile_3d = Bounds(
            tile.min_x,
            minimum_y - 1,
            tile.min_z,
            tile.max_x,
            translated.max_y,
            tile.max_z,
        )
        palette = PALETTE[index % len(PALETTE)]
        source_force_extents: list[tuple[int, int, int, int]] = []

        for source in gallery.functions:
            relative = source.relative_to(gallery.pack_root / "data")
            destination = output / "data" / relative
            translated_lines: list[str] = []
            for line_number, line in enumerate(
                source.read_text(encoding="utf-8").splitlines(), start=1
            ):
                normalized_line = normalize_settled_verifier_line(
                    gallery, source, line, normalization_hits
                )
                effective_lines, topology_added = settled_build_lines(
                    gallery, source, normalized_line
                )
                if topology_added:
                    xnet_topology_hits += 1
                for effective_line in effective_lines:
                    translated_line = translate_line(
                        effective_line, gallery.source_bounds, dx, dy, dz
                    )
                    source_points = list(command_points(effective_line))
                    translated_points = list(command_points(translated_line))
                    expected_points = [
                        (point[0] + dx, point[1] + dy, point[2] + dz)
                        for point in source_points
                    ]
                    if translated_points != expected_points:
                        raise CompositionError(
                            f"{gallery.component_id}: coordinate translation mismatch in "
                            f"{source.relative_to(gallery.root)}:{line_number}"
                        )
                    translated_lines.append(translated_line)
                    extent = forceload_add_extent(translated_line)
                    if extent:
                        source_force_extents.append(extent)
                    mirror = mirrored_failure_command(translated_line, failure_player)
                    if mirror:
                        translated_lines.append(mirror)
                        mirrored_checks += 1
                    positive_mirrors = mirrored_positive_commands(
                        translated_line, failure_player
                    )
                    translated_lines.extend(positive_mirrors)
                    mirrored_checks += len(positive_mirrors)
                    if source.name.startswith("build"):
                        fallback = expected_setblock_check(
                            translated_line, failure_player
                        )
                        if fallback:
                            fallback_checks.append(fallback)
                    if gallery.component_id == "ae2":
                        completion = ae2_completion_command(
                            translated_line, completion_player
                        )
                        if completion:
                            translated_lines.append(completion)
            translated_text = "\n".join(translated_lines)
            write_text(destination, translated_text + "\n")

        if source_force_extents:
            tile_3d = Bounds(
                min(tile_3d.min_x, *(extent[0] for extent in source_force_extents)),
                tile_3d.min_y,
                min(tile_3d.min_z, *(extent[1] for extent in source_force_extents)),
                max(tile_3d.max_x, *(extent[2] for extent in source_force_extents)),
                tile_3d.max_y,
                max(tile_3d.max_z, *(extent[3] for extent in source_force_extents)),
            )

        # Clearing is bounded to the fixture plus padding. A high floating plane
        # avoids generating or replacing millions of ordinary terrain blocks.
        wrapper_dir = output / "data" / "bluemap_atmons" / "function" / "gallery"
        load_wrapper = f"bluemap_atmons:gallery/load_{safe_id}"
        release_wrapper = f"bluemap_atmons:gallery/release_{safe_id}"
        write_text(
            wrapper_dir / f"load_{safe_id}.mcfunction",
            "# Generated bounded integration force-loads.\n"
            + "\n".join(forceload_commands(tile_3d, "add"))
            + "\n",
        )
        write_text(
            wrapper_dir / f"release_{safe_id}.mcfunction",
            "# Release only force-loads owned by this gallery tile.\n"
            + "\n".join(forceload_commands(tile_3d, "remove"))
            + "\n",
        )
        tile_prepare = [
            "# Generated by integration/galleries/compose.py; do not edit.",
            f"function {load_wrapper}",
        ]
        tile_prepare.extend(
            chunked_fill(
                tile.min_x,
                minimum_y,
                tile.min_z,
                tile.max_x,
                min(WORLD_MAX_Y, max(210, translated.max_y + 8)),
                tile.max_z,
                "minecraft:air replace",
            )
        )
        tile_prepare.extend(
            chunked_fill(
                tile.min_x,
                minimum_y - 1,
                tile.min_z,
                tile.max_x,
                minimum_y - 1,
                tile.max_z,
                palette,
            )
        )
        # Source load tags are deliberately not copied into the aggregate pack.
        # Initialize this gallery once, after its tile is clear and force-loaded,
        # before the runner invokes its build wrapper.
        if gallery.source_load_function:
            tile_prepare.append(f"function {gallery.source_load_function}")
        tile_prepare.extend(cumulative_score_reset_lines(gallery))

        write_text(wrapper_dir / f"prepare_{safe_id}.mcfunction", "\n".join(tile_prepare) + "\n")
        prepare_wrapper = f"bluemap_atmons:gallery/prepare_{safe_id}"
        prepare_all.append(f"function {prepare_wrapper}")
        build_function = f"{gallery.namespace}:build"
        verify_function = (
            f"{gallery.namespace}:verify"
            if (gallery.pack_root / "data" / gallery.namespace / gallery.function_dir_name / "verify.mcfunction").is_file()
            else None
        )
        clear_function = (
            f"{gallery.namespace}:clear"
            if (gallery.pack_root / "data" / gallery.namespace / gallery.function_dir_name / "clear.mcfunction").is_file()
            else None
        )
        build_lines = [
            f"scoreboard players set {failure_player} bma_test 0",
            f"scoreboard players set {completion_player} bma_done 0",
            f"function {build_function}",
        ]
        completion_mode = "terminal-predicate"
        if completion_delay_ticks is not None:
            completion_function = f"bluemap_atmons:gallery/complete_{safe_id}"
            write_text(
                wrapper_dir / f"complete_{safe_id}.mcfunction",
                f"scoreboard players set {completion_player} bma_done 1\n",
            )
            build_lines.append(
                f"schedule function {completion_function} {completion_delay_ticks}t replace"
            )
            completion_mode = "scheduled-game-tick-barrier"
        write_text(
            wrapper_dir / f"build_{safe_id}.mcfunction",
            "\n".join(build_lines) + "\n",
        )
        build_wrapper = f"bluemap_atmons:gallery/build_{safe_id}"
        build_all.append(f"function {build_wrapper}")
        verify_wrapper = None
        if not mirrored_checks and fallback_checks:
            deduplicated_fallbacks = list(dict.fromkeys(fallback_checks))
            write_text(
                wrapper_dir / f"auto_verify_{safe_id}.mcfunction",
                "# Generated fallback block/state presence checks.\n"
                + "\n".join(deduplicated_fallbacks)
                + "\n",
            )
            mirrored_checks = len(deduplicated_fallbacks)
            auto_verify = f"bluemap_atmons:gallery/auto_verify_{safe_id}"
        else:
            auto_verify = None
        if verify_function:
            verify_body = f"function {verify_function}\n"
            if auto_verify:
                verify_body += f"function {auto_verify}\n"
            write_text(
                wrapper_dir / f"verify_{safe_id}.mcfunction",
                verify_body,
            )
            verify_wrapper = f"bluemap_atmons:gallery/verify_{safe_id}"
            verify_all.append(f"function {verify_wrapper}")
        elif auto_verify:
            write_text(
                wrapper_dir / f"verify_{safe_id}.mcfunction",
                f"function {auto_verify}\n",
            )
            verify_wrapper = f"bluemap_atmons:gallery/verify_{safe_id}"
            verify_all.append(f"function {verify_wrapper}")

        records.append(
            {
                "id": gallery.component_id,
                "repository": gallery.repository,
                "commit": gallery.commit,
                "namespace": gallery.namespace,
                "sourceBounds": gallery.source_bounds.as_json(),
                "offset": {"x": dx, "y": dy, "z": dz},
                "bounds": translated.as_json(),
                "tileBounds": tile_3d.as_json(),
                "surface": palette,
                "functions": {
                    "load": load_wrapper,
                    "prepare": prepare_wrapper,
                    "build": build_wrapper,
                    "verify": verify_wrapper,
                    "release": release_wrapper,
                    "clear": clear_function,
                },
                "verification": {
                    "mode": (
                        "external-harness-scoreboard"
                        if gallery.component_id == "immersive-engineering"
                        else "instrumented-scoreboard" if mirrored_checks else "command-only"
                    ),
                    "objective": (
                        "bma_test"
                        if mirrored_checks or gallery.component_id == "immersive-engineering"
                        else None
                    ),
                    "failurePlayer": (
                        failure_player
                        if mirrored_checks or gallery.component_id == "immersive-engineering"
                        else None
                    ),
                    "mirroredChecks": (
                        47 if gallery.component_id == "immersive-engineering" else mirrored_checks
                    ),
                    "nativeObjective": gallery.objective,
                },
                "completion": {
                    "mode": completion_mode,
                    "objective": "bma_done",
                    "player": completion_player,
                    "delayTicks": completion_delay_ticks,
                    "timeoutTicks": 1_240 if gallery.component_id == "ae2" else None,
                },
                "marker": {
                    "id": gallery.component_id.replace("-", "_"),
                    "label": gallery.component_id,
                    "position": {
                        "x": (tile.min_x + tile.max_x + 1) / 2,
                        "y": minimum_y,
                        "z": (tile.min_z + tile.max_z + 1) / 2,
                    },
                },
            }
        )

    for rule, hits in zip(SETTLED_VERIFIER_NORMALIZATIONS, normalization_hits):
        if hits != 1:
            raise CompositionError(
                f"{rule.component_id}: settled verifier normalization matched {hits} "
                f"times in {rule.relative_path}; expected exactly 1"
            )
    if xnet_topology_hits != 1:
        raise CompositionError(
            "xnet: settled topology anchor matched "
            f"{xnet_topology_hits} times; expected exactly 1"
        )

    function_root = output / "data" / "bluemap_atmons" / "function"
    write_text(function_root / "prepare.mcfunction", "\n".join(prepare_lines) + "\n")
    write_text(function_root / "prepare_all.mcfunction", "\n".join(prepare_all) + "\n")
    write_text(function_root / "build_all.mcfunction", "\n".join(build_all) + "\n")
    write_text(function_root / "verify_all.mcfunction", "\n".join(verify_all) + "\n")
    write_text(
        function_root / "identity.mcfunction",
        "data modify storage bluemap_atmons:identity composition set value "
        + json.dumps(composition_id)
        + "\n",
    )

    max_x = max(record["tileBounds"]["maxX"] for record in records)
    max_z = max(record["tileBounds"]["maxZ"] for record in records)
    layout_data = {
        "schemaVersion": 1,
        "compositionId": composition_id,
        "composerVersion": COMPOSER_VERSION,
        "runtime": {
            "atmons": manifest["atmons"]["version"],
            "minecraft": manifest["runtime"]["minecraft"],
            "neoforge": manifest["runtime"]["neoforge"],
            "packCommit": manifest["atmons"]["pack_commit"],
        },
        "dimension": "minecraft:overworld",
        "mapId": "atmons_integration",
        "surfaceY": minimum_y - 1,
        "bounds": {
            "minX": origin_x,
            "minY": minimum_y - 1,
            "minZ": origin_z,
            "maxX": max_x,
            "maxY": max(record["bounds"]["maxY"] for record in records),
            "maxZ": max_z,
        },
        "galleries": records,
        "summary": {"galleryCount": len(records)},
    }
    layout_path = output.parent / "gallery-layout.json"
    write_owned_sibling(
        layout_path,
        json.dumps(layout_data, indent=2, sort_keys=True) + "\n",
        previously_owned,
    )

    zip_path = output.with_suffix(".zip")
    zip_marker = zip_path.with_name(zip_path.name + ".bluemap-atmons-owned")
    if zip_path.exists():
        if (
            not previously_owned
            or not zip_marker.is_file()
            or zip_marker.read_text(encoding="utf-8") != OUTPUT_MARKER_CONTENT
        ):
            raise CompositionError(f"refusing to replace unowned archive: {zip_path}")
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file() and path.name != OUTPUT_MARKER:
                info = zipfile.ZipInfo(path.relative_to(output).as_posix(), (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
    write_text(zip_marker, OUTPUT_MARKER_CONTENT)
    composition_manifest = {
        "schemaVersion": 1,
        "compositionId": composition_id,
        "composerVersion": COMPOSER_VERSION,
        "sourceManifestSha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "options": options,
        "layout": {
            "filename": layout_path.name,
            "sizeBytes": layout_path.stat().st_size,
            "sha256": sha256(layout_path),
        },
        "datapack": {
            "filename": zip_path.name,
            "sizeBytes": zip_path.stat().st_size,
            "sha256": sha256(zip_path),
        },
    }
    write_owned_sibling(
        output.parent / "gallery-composition-manifest.json",
        json.dumps(composition_manifest, indent=2, sort_keys=True) + "\n",
        previously_owned,
    )
    return layout_path, zip_path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--origin-x", type=int, default=8192)
    parser.add_argument("--origin-z", type=int, default=8192)
    parser.add_argument("--row-width", type=int, default=1024)
    parser.add_argument("--padding", type=int, default=8)
    parser.add_argument(
        "--minimum-y",
        type=int,
        default=195,
        help="normalize every gallery's lowest referenced block to this Y level",
    )
    args = parser.parse_args()
    try:
        layout, archive = compose(
            args.manifest.resolve(),
            args.output.resolve(),
            args.origin_x,
            args.origin_z,
            args.row_width,
            args.padding,
            args.minimum_y,
        )
    except CompositionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Composed 51 galleries: {archive}")
    print(f"SHA-256: {sha256(archive)}")
    print(f"Layout: {layout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
