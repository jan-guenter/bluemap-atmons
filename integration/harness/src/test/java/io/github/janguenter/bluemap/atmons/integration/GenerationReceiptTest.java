package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertNotEquals;

import java.util.List;
import org.junit.jupiter.api.Test;

class GenerationReceiptTest {
    @Test
    void targetDigestBindsOrderDimensionAndCoordinates() {
        List<Geometry.ChunkCoordinate> first = List.of(
                new Geometry.ChunkCoordinate("minecraft:overworld", 1, 2),
                new Geometry.ChunkCoordinate("minecraft:the_nether", 3, 4)
        );
        List<Geometry.ChunkCoordinate> reordered = List.of(first.get(1), first.get(0));
        List<Geometry.ChunkCoordinate> changed = List.of(
                first.get(0),
                new Geometry.ChunkCoordinate("minecraft:the_nether", 3, 5)
        );

        assertNotEquals(
                GenerationReceipt.targetDigest(first),
                GenerationReceipt.targetDigest(reordered)
        );
        assertNotEquals(
                GenerationReceipt.targetDigest(first),
                GenerationReceipt.targetDigest(changed)
        );
    }
}
