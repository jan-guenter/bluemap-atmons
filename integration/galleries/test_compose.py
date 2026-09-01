#!/usr/bin/env python3
"""Focused tests for gallery coordinate translation and layout math."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("compose.py")
SPEC = importlib.util.spec_from_file_location("gallery_compose", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def check(actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(f"expected {expected!r}, got {actual!r}")


def main() -> int:
    check_pinned_gallery_tree_rejects_ignored_inputs()
    bounds = MODULE.Bounds(160, 95, 160, 220, 160, 220)
    check(
        MODULE.translate_line("setblock 164 100 171 minecraft:stone", bounds, 1000, 96, 2000),
        "setblock 1164 196 2171 minecraft:stone",
    )
    check(
        MODULE.translate_line(
            "execute if block 221 107 254 minecraft:stone_bricks run teleport @s 221.5 108 254.5 180 14",
            MODULE.Bounds(160, 95, 160, 269, 140, 269),
            1000,
            96,
            2000,
        ),
        "execute if block 1221 203 2254 minecraft:stone_bricks run teleport @s 1221.5 204 2254.5 180 14",
    )
    check(
        MODULE.translate_line("fill 160 99 160 191 108 191 minecraft:air", bounds, 1000, 96, 2000),
        "fill 1160 195 2160 1191 204 2191 minecraft:air",
    )
    check(
        MODULE.translate_line(
            "execute unless data block 164 100 164 {myWorldPos:[I;164,100,164],connections:[{pos:[I;4,0,0]}]} run say fail",
            bounds,
            1000,
            96,
            2000,
        ),
        "execute unless data block 1164 196 2164 {myWorldPos:[I;1164,196,2164],connections:[{pos:[I;4,0,0]}]} run say fail",
    )
    check(
        MODULE.translate_line(
            "setblock 164 100 171 demo:shield{sx:164,sy:100,sz:164}",
            bounds,
            1000,
            96,
            2000,
        ),
        "setblock 1164 196 2171 demo:shield{sx:1164,sy:196,sz:2164}",
    )
    check(
        MODULE.translate_line(
            "setblock 164 100 171 demo:shield{sx:4096,sy:100,sz:4096}",
            bounds,
            1000,
            96,
            2000,
        ),
        "setblock 1164 196 2171 demo:shield{sx:4096,sy:100,sz:4096}",
    )
    check(
        MODULE.translate_line(
            "execute unless entity @e[x=160,y=99,z=160,dx=31,dy=9,dz=31] run say fail",
            bounds,
            1000,
            96,
            2000,
        ),
        "execute unless entity @e[x=1160,y=195,z=2160,dx=31,dy=9,dz=31] run say fail",
    )
    packed = MODULE.pack_block_pos(164, 100, 171)
    line = f"summon minecraft:pig 164.5 100.5 171.5 {{AttachedPos:{packed}L,Pos:[164.5d,100.5d,171.5d]}}"
    translated = MODULE.translate_line(line, bounds, 1000, 96, 2000)
    expected_packed = MODULE.pack_block_pos(1164, 196, 2171)
    check(
        translated,
        f"summon minecraft:pig 1164.5 196.5 2171.5 {{AttachedPos:{expected_packed}L,Pos:[1164.5d,196.5d,2171.5d]}}",
    )
    check(
        MODULE.translate_line(
            'tellraw @s {"text":"wire [176 101 190] -> [188 101 190]"}',
            bounds,
            1000,
            96,
            2000,
        ),
        'tellraw @s {"text":"wire [1176 197 2190] -> [1188 197 2190]"}',
    )
    check(
        MODULE.mirrored_failure_command(
            'execute unless block 1 2 3 minecraft:stone run tellraw @a {"color":"red","text":"FAIL"}',
            "#demo",
        ),
        "execute unless block 1 2 3 minecraft:stone run scoreboard players add #demo bma_test 1",
    )
    check(
        MODULE.mirrored_failure_command(
            "execute unless data block 1 2 3 {} run scoreboard players add #failures demo 1",
            "#demo",
        ),
        "execute unless data block 1 2 3 {} run scoreboard players add #demo bma_test 1",
    )
    check(
        MODULE.mirrored_failure_command(
            'tellraw @a [{"text":"Gallery: "},{"score":{"name":"#failures","objective":"demo"}},{"text":" failures"}]',
            "#demo",
        ),
        None,
    )
    check(
        MODULE.mirrored_failure_command(
            'tellraw @a {"text":"Verification finished; inspect any mismatch above"}',
            "#demo",
        ),
        None,
    )
    check(
        MODULE.mirrored_failure_command(
            "scoreboard players add #failures demo 1",
            "#demo",
        ),
        None,
    )
    check(
        MODULE.mirrored_positive_commands(
            'execute if block 1 2 3 minecraft:stone if data block 4 5 6 {ready:1b} run tellraw @s {"color":"green","text":"ok"}',
            "#demo",
        ),
        [
            "execute unless block 1 2 3 minecraft:stone run scoreboard players add #demo bma_test 1",
            "execute unless data block 4 5 6 {ready:1b} run scoreboard players add #demo bma_test 1",
        ],
    )
    check(
        MODULE.expected_setblock_check(
            "setblock 1 2 3 demo:block[facing=north]{payload:1b}", "#demo"
        ),
        "execute unless block 1 2 3 demo:block[facing=north] run scoreboard players add #demo bma_test 1",
    )
    fills = list(MODULE.chunked_fill(0, 0, 0, 399, 9, 399, "minecraft:air"))
    if len(fills) <= 1:
        raise AssertionError("large fills were not split")
    force_bounds = MODULE.Bounds(0, 0, 0, 511, 0, 511)
    force_loads = list(MODULE.forceload_commands(force_bounds, "add"))
    check(
        force_loads,
        [
            "forceload add 0 0 255 255",
            "forceload add 0 256 255 511",
            "forceload add 256 0 511 255",
            "forceload add 256 256 511 511",
        ],
    )

    with tempfile.TemporaryDirectory(prefix="bluemap-atmons-compose-test-") as temporary:
        output = Path(temporary) / "datapack"
        layout_path, _archive = MODULE.compose(
            MODULE.DEFAULT_MANIFEST,
            output,
            origin_x=8192,
            origin_z=8192,
            row_width=1024,
            padding=8,
            minimum_y=195,
        )
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        check(len(layout["galleries"]), 51)
        check(sum(gallery["functions"]["verify"] is not None for gallery in layout["galleries"]), 51)
        check(
            sum(
                gallery["verification"]["objective"] is not None
                and gallery["verification"]["failurePlayer"] is not None
                for gallery in layout["galleries"]
            ),
            51,
        )
        check(
            sum(
                gallery["completion"]["objective"] == "bma_done"
                and bool(gallery["completion"]["player"])
                for gallery in layout["galleries"]
            ),
            51,
        )
        galleries_by_id = {gallery["id"]: gallery for gallery in layout["galleries"]}
        check(galleries_by_id["ae2"]["completion"]["mode"], "terminal-predicate")
        check(galleries_by_id["ae2"]["completion"]["delayTicks"], None)
        check(
            galleries_by_id["logistics-networks"]["completion"]["delayTicks"],
            121,
        )
        rftools = galleries_by_id["rftools-builder"]
        rftools_projector = (
            164 + rftools["offset"]["x"],
            100 + rftools["offset"]["y"],
            164 + rftools["offset"]["z"],
        )
        shifted_projector = (
            f"sx:{rftools_projector[0]},sy:{rftools_projector[1]},"
            f"sz:{rftools_projector[2]}"
        )
        for function_name in ("build", "verify"):
            rftools_function = (
                output
                / "data/rftools_builder_gallery/function"
                / f"{function_name}.mcfunction"
            ).read_text(encoding="utf-8")
            if shifted_projector not in rftools_function:
                raise AssertionError(
                    f"RFTools {function_name} omitted translated projector coordinates"
                )
            if "sx:164,sy:100,sz:164" in rftools_function:
                raise AssertionError(
                    f"RFTools {function_name} retained stale projector coordinates"
                )
        ae2_settle = (
            output
            / "data/ae2_m3/function/settle_check.mcfunction"
        ).read_text(encoding="utf-8")
        check(ae2_settle.count("scoreboard players set #ae2 bma_done 1"), 2)
        manifest = MODULE.load_manifest(MODULE.DEFAULT_MANIFEST)
        component_roots = {
            component["id"]: MODULE.ROOT / component["submodule_path"]
            for component in manifest["components"]
            if component["kind"] == "addon"
        }
        rerun_reset_objectives = {
            "ae2": None,
            "factory-blocks": "fb_gallery",
            "laserio": "laserio_glr",
            "rftools-builder": "rftb_gallery",
            "enderio": "enderio_gallery",
            "modular-routers": "mr_gallery",
            "securitycraft": "sc_gallery",
            "functional-storage": "fs_gallery",
            "logistics-networks": "ln_gallery",
        }
        source_load_calls = 0
        for gallery in layout["galleries"]:
            safe_id = gallery["id"].replace("-", "_")
            prepare = (
                output
                / "data"
                / "bluemap_atmons"
                / "function"
                / "gallery"
                / f"prepare_{safe_id}.mcfunction"
            ).read_text(encoding="utf-8").splitlines()
            source_load = f"function {gallery['namespace']}:load"
            source_load_path = (
                component_roots[gallery["id"]]
                / "gallery"
                / "datapack"
                / "data"
                / gallery["namespace"]
                / "function"
                / "load.mcfunction"
            )
            expected_calls = 1 if source_load_path.is_file() else 0
            check(prepare.count(source_load), expected_calls)
            if expected_calls:
                if gallery["id"] not in rerun_reset_objectives:
                    check(prepare[-1], source_load)
                source_load_calls += 1
            load_commands = [
                line.replace("forceload add", "forceload OP", 1)
                for line in (
                    output
                    / "data/bluemap_atmons/function/gallery"
                    / f"load_{safe_id}.mcfunction"
                ).read_text(encoding="utf-8").splitlines()
                if line.startswith("forceload add")
            ]
            release_commands = [
                line.replace("forceload remove", "forceload OP", 1)
                for line in (
                    output
                    / "data/bluemap_atmons/function/gallery"
                    / f"release_{safe_id}.mcfunction"
                ).read_text(encoding="utf-8").splitlines()
                if line.startswith("forceload remove")
            ]
            check(load_commands, release_commands)
        check(source_load_calls, 50)
        ae2_prepare = (
            output
            / "data/bluemap_atmons/function/gallery/prepare_ae2.mcfunction"
        ).read_text(encoding="utf-8").splitlines()
        ae2_reset_lines = [
            "# Reset exact native invocation counters for repeatable aggregate runs.",
            "scoreboard objectives add ae2m3run dummy",
            "scoreboard objectives add ae2s1run dummy",
            "scoreboard objectives add ae2m45run dummy",
            "scoreboard objectives add ae2amrun dummy",
            "scoreboard players set #m3f_builds ae2m3run 0",
            "scoreboard players set #s1_builds ae2s1run 0",
            "scoreboard players set #m45_builds ae2m45run 0",
            "scoreboard players set #appmek_builds ae2amrun 0",
        ]
        check(ae2_prepare[-len(ae2_reset_lines) :], ae2_reset_lines)
        check(ae2_prepare[-len(ae2_reset_lines) - 1], "function ae2_m3:load")
        for component_id, objective in rerun_reset_objectives.items():
            if component_id == "ae2":
                continue
            safe_id = component_id.replace("-", "_")
            prepare = (
                output
                / "data/bluemap_atmons/function/gallery"
                / f"prepare_{safe_id}.mcfunction"
            ).read_text(encoding="utf-8").splitlines()
            expected_suffix = [
                "# Reset exact native invocation counters for repeatable aggregate runs.",
                f"scoreboard objectives add {objective} dummy",
                f"scoreboard players set #builds {objective} 0",
            ]
            check(prepare[-len(expected_suffix) :], expected_suffix)
        pneumaticcraft_build = (
            output / "data/pneumaticcraft_gallery/function/build.mcfunction"
        ).read_text(encoding="utf-8")
        pneumaticcraft_verify = (
            output / "data/pneumaticcraft_gallery/function/verify.mcfunction"
        ).read_text(encoding="utf-8")
        if "pneumaticcraft:heat_pipe[east=true,west=true]" not in pneumaticcraft_build:
            raise AssertionError("PneumaticCraft source placement was changed")
        if "pneumaticcraft:heat_pipe[east=true,west=true]" in pneumaticcraft_verify:
            raise AssertionError("PneumaticCraft settled verifier retained volatile arms")
        check(pneumaticcraft_verify.count("pneumaticcraft:heat_pipe run"), 2)
        pressure_tube_checks = sum(
            1
            for line in pneumaticcraft_verify.splitlines()
            if "run scoreboard players add #pneumaticcraft bma_test 1" in line
            and any(
                block in line
                for block in (
                    "pneumaticcraft:pressure_tube",
                    "pneumaticcraft:reinforced_pressure_tube",
                    "pneumaticcraft:advanced_pressure_tube",
                )
            )
        )
        check(pressure_tube_checks, 27)

        morered_verify = (
            output / "data/morered_gallery/function/verify.mcfunction"
        ).read_text(encoding="utf-8")
        if "hexidecrubrometer[face=floor,facing=north,power=15]" in morered_verify:
            raise AssertionError("More Red settled verifier retained volatile power")
        check(
            morered_verify.count(
                "morered:hexidecrubrometer[face=floor,facing=north]"
            ),
            2,
        )
        check(
            sum(
                1
                for line in morered_verify.splitlines()
                if "run scoreboard players add #morered bma_test 1" in line
            ),
            86,
        )

        xnet_build = (
            output / "data/xnet_gallery/function/build.mcfunction"
        ).read_text(encoding="utf-8")
        xnet_verify = (
            output / "data/xnet_gallery/function/verify.mcfunction"
        ).read_text(encoding="utf-8")
        check(xnet_build.count("# Integration-only stable XNet topology"), 1)
        if "xnet:antenna_base" not in xnet_build or "xnet:antenna[facing=north]" not in xnet_build:
            raise AssertionError("XNet wireless router lacks a stable antenna stack")
        impossible_netcable = (
            "xnet:netcable[color=red,north=none,south=none,east=block,"
            "west=cable,up=none,down=none,waterlogged=false]"
        )
        if impossible_netcable in xnet_verify:
            raise AssertionError("XNet settled verifier retained impossible netcable block arm")
        settled_netcable = (
            "xnet:netcable[color=red,north=none,south=none,east=none,"
            "west=cable,up=none,down=none,waterlogged=false]"
        )
        check(xnet_verify.count(settled_netcable), 2)
        check(xnet_verify.count("xnet:controller[error=false,facing=north]"), 2)
        check(xnet_verify.count("xnet:wireless_router[error=false,facing=west]"), 2)
        check(xnet_verify.count('"xnet:mimic_data"'), 4)
        check(
            sum(
                1
                for line in xnet_verify.splitlines()
                if "run scoreboard players add #xnet bma_test 1" in line
            ),
            22,
        )

        source_pneumaticcraft_verify = (
            component_roots["pneumaticcraft"]
            / "gallery/datapack/data/pneumaticcraft_gallery/function/verify.mcfunction"
        ).read_text(encoding="utf-8")
        source_morered_verify = (
            component_roots["morered"]
            / "gallery/datapack/data/morered_gallery/function/verify.mcfunction"
        ).read_text(encoding="utf-8")
        source_xnet_verify = (
            component_roots["xnet"]
            / "gallery/datapack/data/xnet_gallery/function/verify.mcfunction"
        ).read_text(encoding="utf-8")
        if "pneumaticcraft:heat_pipe[east=true,west=true]" not in source_pneumaticcraft_verify:
            raise AssertionError("PneumaticCraft child verifier was changed")
        if "hexidecrubrometer[face=floor,facing=north,power=15]" not in source_morered_verify:
            raise AssertionError("More Red child verifier was changed")
        if impossible_netcable not in source_xnet_verify:
            raise AssertionError("XNet child verifier was changed")
        chisel = galleries_by_id["chisel"]
        chisel_source_max_x = 48 + chisel["offset"]["x"]
        if chisel["tileBounds"]["maxX"] < chisel_source_max_x:
            raise AssertionError("Chisel source force-load extent is not owned by its wrapper")
        wire_kit = (
            output / "data/immeng_gallery/function/wire_kit.mcfunction"
        ).read_text(encoding="utf-8")
        if "[176 101 190]" in wire_kit or "[204 101 202]" in wire_kit:
            raise AssertionError("Immersive Energistics wire instructions were not translated")
        if list(output.glob("data/minecraft/tags/**/load.json")):
            raise AssertionError("aggregate datapack unexpectedly contains an automatic load tag")
        bare_increment = re.compile(
            r"^\s*scoreboard\s+players\s+add\s+#[^ ]+\s+bma_test\s+[1-9]\d*\b"
        )
        for function in output.rglob("*.mcfunction"):
            for line in function.read_text(encoding="utf-8").splitlines():
                if bare_increment.search(line):
                    raise AssertionError(f"unconditional integration failure increment: {line}")
    print("PASS: gallery composer translation tests")
    return 0


def check_pinned_gallery_tree_rejects_ignored_inputs() -> None:
    with tempfile.TemporaryDirectory(prefix="bluemap-atmons-gallery-tree-") as temporary:
        root = Path(temporary)
        function = root / "gallery/datapack/data/demo/function/build.mcfunction"
        function.parent.mkdir(parents=True)
        function.write_text("setblock 0 64 0 minecraft:stone\n", encoding="utf-8")
        (root / ".gitignore").write_text(
            "gallery/datapack/data/demo/function/ignored.mcfunction\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "test"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        MODULE.attest_gallery_tree(root, commit, "fixture")
        ignored = function.with_name("ignored.mcfunction")
        ignored.write_text("say injected\n", encoding="utf-8")
        try:
            MODULE.attest_gallery_tree(root, commit, "fixture")
        except MODULE.CompositionError as exc:
            if "extra=" not in str(exc):
                raise
        else:
            raise AssertionError("ignored untracked gallery function was accepted")


if __name__ == "__main__":
    raise SystemExit(main())
