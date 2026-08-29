from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "generate_bluemap_map_configs.py"
SPEC = importlib.util.spec_from_file_location("map_configs", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MAP_CONFIGS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MAP_CONFIGS)


class MapConfigGeneratorTest(unittest.TestCase):
    def test_writes_only_selected_dimensions_with_exact_ids(self) -> None:
        self.assertEqual(
            "atmons_minecraft_overworld_3f60de212b48",
            MAP_CONFIGS.safe_map_id("minecraft:overworld"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self._catalog()
            masks = {
                "schemaVersion": 1,
                "worldIdentity": catalog["worldIdentity"],
                "planFingerprint": catalog["planFingerprint"],
                "runtimeAttestationSha256": catalog["runtimeAttestationSha256"],
                "dimensions": [
                    {
                        "dimension": "minecraft:overworld",
                        "renderMask": [
                            {
                                "minX": -4,
                                "maxX": 35,
                                "minZ": -4,
                                "maxZ": 35,
                                "minY": 56,
                                "maxY": 84,
                            }
                        ],
                    }
                ],
            }
            catalog_path = root / "catalog.json"
            masks_path = root / "masks.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            masks_path.write_text(json.dumps(masks), encoding="utf-8")

            manifest = MAP_CONFIGS.generate(
                catalog_path,
                masks_path,
                root / "bluemap",
                Path("/srv/minecraft/world"),
                "file",
            )

            self.assertEqual(1, len(manifest["maps"]))
            entry = manifest["maps"][0]
            self.assertEqual(
                MAP_CONFIGS.safe_map_id("minecraft:overworld"), entry["mapId"]
            )
            config = root / "bluemap" / entry["configFile"]
            self.assertTrue(config.is_file())
            self.assertEqual(config.stat().st_size, entry["sizeBytes"])
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            text = config.read_text(encoding="utf-8")
            self.assertIn('world: "/srv/minecraft/world"', text)
            self.assertIn('dimension: "minecraft:overworld"', text)
            self.assertIn("min-x: -4, max-x: 35", text)
            self.assertIn("start-pos: { x: 16, z: 16 }", text)
            self.assertIn("render-edges: false", text)
            self.assertNotIn("render-edges: true", text)

    def test_rejects_catalog_map_id_drift(self) -> None:
        catalog = self._catalog()
        catalog["dimensions"][0]["safeMapId"] = "wrong"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "safeMapId mismatch"):
                MAP_CONFIGS._dimensions(MAP_CONFIGS._read_json(path))

    def test_rejects_in_progress_catalog(self) -> None:
        catalog = self._catalog()
        catalog["structures"][0]["selection"] = {"status": "pending"}
        with self.assertRaisesRegex(ValueError, "eligible unlocated"):
            MAP_CONFIGS._selected_dimensions(catalog)

    @staticmethod
    def _catalog() -> dict:
        dimension = "minecraft:overworld"
        map_id = MAP_CONFIGS.safe_map_id(dimension)
        return {
            "schemaVersion": 1,
            "worldIdentity": "123e4567-e89b-12d3-a456-426614174000",
            "planFingerprint": "a" * 64,
            "runtimeAttestationSha256": "b" * 64,
            "runtime": {
                **MAP_CONFIGS.BASELINE,
                "packCommit": "c7bb230f21d14d26859d0b92548f089b3a493ad9",
                "bluemapVersion": "candidate",
                "bluemapCommit": "c" * 40,
                "bluemapJarSha256": "d" * 64,
            },
            "dimensions": [
                {
                    "id": dimension,
                    "safeMapId": map_id,
                    "mapConfigFile": f"maps/{map_id}.conf",
                    "anchor": {"x": 0, "y": 64, "z": 0},
                    "mapIds": [],
                }
            ],
            "structures": [
                {
                    "id": "minecraft:village_plains",
                    "eligibility": [
                        {
                            "dimension": dimension,
                            "structureSets": ["minecraft:villages"],
                            "placementTypes": ["minecraft:random_spread"],
                        }
                    ],
                    "selection": {
                        "status": "located",
                        "dimension": dimension,
                        "borderedBounds": {
                            "minX": -4,
                            "maxX": 35,
                            "minZ": -4,
                            "maxZ": 35,
                            "minY": 56,
                            "maxY": 84,
                        },
                    },
                }
            ],
            "summary": {
                "registered": 1,
                "placed": 1,
                "located": 1,
                "unlocated": 0,
                "markers": 1,
                "uniqueChunks": 16,
                "uniqueRegions": 4,
            },
        }


if __name__ == "__main__":
    unittest.main()
