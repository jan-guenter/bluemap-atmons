#!/usr/bin/env python3
"""Focused checks for exact structure generation/render evidence."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_structure_suite.py")
SPEC = importlib.util.spec_from_file_location("structure_suite", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC.loader.exec_module(MODULE)


class ScriptedTransport:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.commands: list[str] = []

    def command(self, command: str) -> str:
        self.commands.append(command)
        if not self.responses:
            raise AssertionError("unexpected command")
        return self.responses.pop(0)

    def close(self) -> None:
        pass


def main() -> int:
    targets = [
        {"dimension": "minecraft:overworld", "x": -1, "z": 2},
        {"dimension": "minecraft:overworld", "x": 0, "z": 2},
    ]
    assert MODULE.target_digest(targets) != MODULE.target_digest(list(reversed(targets)))
    assert MODULE.safe_map_id("minecraft:overworld") == (
        "atmons_minecraft_overworld_3f60de212b48"
    )
    assert MODULE.region_state_cells([(5, -3), (63, 63), (64, -65)]) == {
        (0, -1), (0, 0), (1, -2)
    }

    exact = (
        "Verified 17 freshly rendered structure tiles across 2 maps; "
        f"evidenceSha256={'a' * 64}"
    )
    successful = ScriptedTransport([
        MODULE.RENDER_BUSY_RESPONSE,
        MODULE.RENDER_BUSY_RESPONSE,
        exact,
    ])
    response, match = MODULE.wait_render_verification(
        successful, expected_maps=2, timeout=1, poll_interval=0
    )
    assert response == exact
    assert match.group(1) == "17"
    assert successful.commands == [
        "bluemapatmons structures verify-render",
        "bluemapatmons structures verify-render",
        "bluemapatmons structures verify-render",
    ]

    for invalid in ("", "unexpected response", exact.replace("2 maps", "3 maps")):
        try:
            MODULE.wait_render_verification(
                ScriptedTransport([invalid]), expected_maps=2, timeout=1
            )
        except MODULE.runtime.SuiteError:
            pass
        else:
            raise AssertionError(f"accepted invalid verification response: {invalid!r}")

    try:
        MODULE.wait_render_verification(
            ScriptedTransport([MODULE.RENDER_BUSY_RESPONSE]),
            expected_maps=2,
            timeout=0,
            poll_interval=0,
        )
    except MODULE.runtime.SuiteError:
        pass
    else:
        raise AssertionError("busy renderer did not time out")

    print("PASS: structure suite unit checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
