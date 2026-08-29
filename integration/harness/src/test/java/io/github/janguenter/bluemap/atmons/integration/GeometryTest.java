package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.Set;
import org.junit.jupiter.api.Test;

class GeometryTest {
    @Test
    void inflatesFourBlocksAndClampsVerticalWorldBounds() {
        Geometry.BlockBounds bounds = new Geometry.BlockBounds(-16, -63, 15, 31, 318, 32);

        assertEquals(
                new Geometry.BlockBounds(-20, -64, 11, 35, 319, 36),
                bounds.inflate(4, -64, 319)
        );
    }

    @Test
    void clampsRecordedStructureBoundsBeforeBorderInflation() {
        Geometry.BlockBounds source = new Geometry.BlockBounds(
                -10, -35, -20, 30, 320, 40
        );

        Geometry.BlockBounds clamped = source.clampY(-64, 319);

        assertEquals(
                new Geometry.BlockBounds(-10, -35, -20, 30, 319, 40),
                clamped
        );
        assertEquals(
                new Geometry.BlockBounds(-14, -39, -24, 34, 319, 44),
                clamped.inflate(4, -64, 319)
        );
    }

    @Test
    void rejectsStructureBoundsFullyOutsideBuildHeight() {
        Geometry.BlockBounds above = new Geometry.BlockBounds(
                0, 320, 0, 1, 340, 1
        );
        Geometry.BlockBounds below = new Geometry.BlockBounds(
                0, -100, 0, 1, -65, 1
        );

        assertThrows(IllegalArgumentException.class, () -> above.clampY(-64, 319));
        assertThrows(IllegalArgumentException.class, () -> below.clampY(-64, 319));
    }

    @Test
    void convertsInclusiveNegativeBlockBoundsToChunks() {
        Geometry.BlockBounds bounds = new Geometry.BlockBounds(-17, 0, -16, 16, 1, 31);

        assertEquals(new Geometry.ChunkBounds(-2, -1, 1, 1), bounds.chunks());
        assertEquals(12L, bounds.chunks().count());
    }

    @Test
    void convertsChunksAcrossNegativeRegionBoundary() {
        Geometry.ChunkBounds chunks = new Geometry.ChunkBounds(-33, -32, 32, 31);

        assertEquals(
                Set.of(
                        new Geometry.RegionCoordinate(-2, -1),
                        new Geometry.RegionCoordinate(-2, 0),
                        new Geometry.RegionCoordinate(-1, -1),
                        new Geometry.RegionCoordinate(-1, 0),
                        new Geometry.RegionCoordinate(0, -1),
                        new Geometry.RegionCoordinate(0, 0),
                        new Geometry.RegionCoordinate(1, -1),
                        new Geometry.RegionCoordinate(1, 0)
                ),
                chunks.regions()
        );
    }

    @Test
    void rejectsInvertedBoundsAndNegativeBorders() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new Geometry.BlockBounds(1, 0, 0, 0, 0, 0)
        );
        Geometry.BlockBounds bounds = new Geometry.BlockBounds(0, 0, 0, 0, 0, 0);
        assertThrows(IllegalArgumentException.class, () -> bounds.inflate(-1, -64, 319));
    }
}
