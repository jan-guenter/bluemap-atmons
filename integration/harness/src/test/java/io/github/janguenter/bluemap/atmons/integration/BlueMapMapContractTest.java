package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class BlueMapMapContractTest {
    @Test
    void createsStableSafeMapAndConfigIds() {
        String mapId = BlueMapMapContract.safeMapId("minecraft:overworld");

        assertEquals("atmons_minecraft_overworld_3f60de212b48", mapId);
        assertEquals(mapId, BlueMapMapContract.safeMapId("minecraft:overworld"));
        assertTrue(mapId.matches("atmons_[a-z0-9_]+_[0-9a-f]{12}"));
        assertEquals("maps/" + mapId + ".conf", BlueMapMapContract.configFile(
                "minecraft:overworld"
        ));
    }

    @Test
    void hashSuffixPreventsSanitizationCollisions() {
        assertNotEquals(
                BlueMapMapContract.safeMapId("example:a-b"),
                BlueMapMapContract.safeMapId("example:a_b")
        );
    }
}
