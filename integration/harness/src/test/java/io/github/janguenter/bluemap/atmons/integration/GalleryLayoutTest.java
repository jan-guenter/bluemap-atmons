package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class GalleryLayoutTest {
    @Test
    void acceptsComposerGalleryWithLoadAndReleaseFunctions() {
        GalleryLayout layout = JsonFiles.GSON.fromJson("""
                {
                  "schemaVersion": 1,
                  "compositionId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                  "composerVersion": "2.4.1",
                  "dimension": "minecraft:overworld",
                  "mapId": "atmons_integration",
                  "bounds": {
                    "minX": 0, "minY": 64, "minZ": 0,
                    "maxX": 31, "maxY": 96, "maxZ": 31
                  },
                  "galleries": [{
                    "id": "ae2",
                    "repository": "jan-guenter/bluemap-ae2-addon",
                    "commit": "575c05222c7322421c30cb1158a2054dc04aa564",
                    "namespace": "ae2_m3",
                    "surface": "minecraft:orange_terracotta",
                    "bounds": {
                      "minX": 4, "minY": 65, "minZ": 4,
                      "maxX": 27, "maxY": 90, "maxZ": 27
                    },
                    "tileBounds": {
                      "minX": 0, "minY": 64, "minZ": 0,
                      "maxX": 31, "maxY": 90, "maxZ": 31
                    },
                    "marker": {
                      "id": "ae2",
                      "label": "AE2",
                      "position": {"x": 16.5, "y": 65, "z": 16.5}
                    },
                    "functions": {
                      "load": "bluemap_atmons:gallery/load_ae2",
                      "prepare": "bluemap_atmons:gallery/prepare_ae2",
                      "build": "bluemap_atmons:gallery/build_ae2",
                      "verify": "bluemap_atmons:gallery/verify_ae2",
                      "release": "bluemap_atmons:gallery/release_ae2",
                      "clear": "ae2_m3:clear"
                    },
                    "completion": {
                      "mode": "terminal-predicate",
                      "objective": "bma_done",
                      "player": "#ae2",
                      "delayTicks": null,
                      "timeoutTicks": 1240
                    }
                  }]
                }
                """, GalleryLayout.class);

        layout.validate();
        assertEquals("atmons_integration", layout.preferredMapId("minecraft:overworld"));

        layout.composerVersion = "2.4.0";
        assertThrows(IllegalArgumentException.class, layout::validate);
    }

    @Test
    void acceptsNamedAreaAndPoint() {
        GalleryLayout layout = JsonFiles.GSON.fromJson("""
                {
                  "schemaVersion": 1,
                  "areas": [{
                    "id": "ie",
                    "addonId": "immersive-engineering",
                    "label": "Immersive Engineering",
                    "dimension": "minecraft:overworld",
                    "color": "#12aBcF",
                    "bounds": {
                      "minX": -4, "minY": 99, "minZ": -4,
                      "maxX": 40, "maxY": 120, "maxZ": 40
                    }
                  }],
                  "points": [{
                    "id": "ie-entry",
                    "addonId": "immersive-engineering",
                    "label": "IE gallery",
                    "dimension": "minecraft:overworld",
                    "position": {"x": 0.5, "y": 100, "z": 0.5}
                  }]
                }
                """, GalleryLayout.class);

        layout.validate();
        assertEquals(0x12ABCF, GalleryLayout.parseColor(layout.areas.getFirst().color));
    }

    @Test
    void rejectsDuplicateIdsAndInvertedBounds() {
        GalleryLayout layout = new GalleryLayout();
        layout.schemaVersion = 1;
        GalleryLayout.Area area = new GalleryLayout.Area();
        area.id = "same";
        area.addonId = "demo";
        area.label = "Area";
        area.dimension = "minecraft:overworld";
        area.bounds = new Geometry.BlockBounds(0, 0, 0, 1, 1, 1);
        GalleryLayout.Point point = new GalleryLayout.Point();
        point.id = "same";
        point.addonId = "demo";
        point.label = "Point";
        point.dimension = "minecraft:overworld";
        point.position = new GalleryLayout.Position(0, 0, 0);
        layout.areas = java.util.List.of(area);
        layout.points = java.util.List.of(point);

        assertThrows(IllegalArgumentException.class, layout::validate);
        assertThrows(
                IllegalArgumentException.class,
                () -> new Geometry.BlockBounds(2, 0, 0, 1, 1, 1)
        );
    }

    @Test
    void rejectsInvalidColorAndDimension() {
        assertThrows(IllegalArgumentException.class, () -> GalleryLayout.parseColor("blue"));

        GalleryLayout layout = new GalleryLayout();
        layout.schemaVersion = 1;
        GalleryLayout.Point point = new GalleryLayout.Point();
        point.id = "point";
        point.addonId = "demo";
        point.label = "Point";
        point.dimension = "not a dimension";
        point.position = new GalleryLayout.Position(0, 0, 0);
        layout.points = java.util.List.of(point);
        assertThrows(IllegalArgumentException.class, layout::validate);
    }
}
