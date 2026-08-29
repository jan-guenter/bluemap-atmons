package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

import com.flowpowered.math.vector.Vector2i;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;

class StructureRenderScheduleTest {
    @Test
    void regionDigestIsOrderedAndCoordinateSensitive() {
        Map<String, Set<Vector2i>> first = Map.of(
                "minecraft:overworld",
                new LinkedHashSet<>(Set.of(new Vector2i(2, -1), new Vector2i(1, 3)))
        );
        Map<String, Set<Vector2i>> reordered = Map.of(
                "minecraft:overworld",
                new LinkedHashSet<>(Set.of(new Vector2i(1, 3), new Vector2i(2, -1)))
        );
        Map<String, Set<Vector2i>> changed = Map.of(
                "minecraft:overworld", Set.of(new Vector2i(1, 3))
        );

        assertEquals(
                StructureRenderSchedule.regionDigest(first),
                StructureRenderSchedule.regionDigest(reordered)
        );
        assertNotEquals(
                StructureRenderSchedule.regionDigest(first),
                StructureRenderSchedule.regionDigest(changed)
        );
    }
}
