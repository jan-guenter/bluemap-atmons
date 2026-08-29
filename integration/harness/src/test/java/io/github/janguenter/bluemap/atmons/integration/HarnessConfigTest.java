package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.io.StringReader;
import org.junit.jupiter.api.Test;

class HarnessConfigTest {
    @Test
    void bundledDefaultPinsExactBaselineAndFourBlockBorder() throws IOException {
        HarnessConfig config = HarnessConfig.bundledDefault();

        assertEquals("1.2.0", config.baseline.atmons());
        assertEquals("1.21.1", config.baseline.minecraft());
        assertEquals("21.1.248", config.baseline.neoforge());
        assertEquals("2.8.0", config.baseline.bluemapApi());
        assertEquals(4, config.borderBlocks);
        assertEquals(2048, config.fallbackLocateRadiusPlacementRings);
        assertEquals("structure-catalog.json", config.catalogFile);
    }

    @Test
    void rejectsWrongBaseline() throws IOException {
        String json = JsonFiles.GSON.toJson(HarnessConfig.bundledDefault())
                .replace("\"1.2.0\"", "\"1.2.1\"");

        assertThrows(
                IllegalArgumentException.class,
                () -> HarnessConfig.fromReader(new StringReader(json))
        );
    }

    @Test
    void rejectsTraversalAndDuplicateDimensions() throws IOException {
        HarnessConfig traversal = HarnessConfig.bundledDefault();
        traversal.catalogFile = "../structure-catalog.json";
        assertThrows(IllegalArgumentException.class, traversal::validate);

        HarnessConfig duplicate = HarnessConfig.bundledDefault();
        duplicate.dimensionPriority = java.util.List.of(
                "minecraft:overworld", "minecraft:overworld"
        );
        assertThrows(IllegalArgumentException.class, duplicate::validate);
    }

    @Test
    void rejectsMalformedJson() {
        assertThrows(
                IllegalArgumentException.class,
                () -> HarnessConfig.fromReader(new StringReader("{"))
        );
    }
}
