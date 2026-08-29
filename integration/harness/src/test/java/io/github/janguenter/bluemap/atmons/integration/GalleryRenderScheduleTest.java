package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.flowpowered.math.vector.Vector2i;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class GalleryRenderScheduleTest {
    @Test
    void roundTripRejectsChangedLayoutBootRegionsAndTileGrid(@TempDir Path directory)
            throws Exception {
        GalleryLayout layout = GalleryRenderVerifierTest.layout(
                new Geometry.BlockBounds(0, 0, 0, 31, 1, 31)
        );
        Path layoutPath = directory.resolve("gallery-layout.json");
        JsonFiles.writeAtomic(layoutPath, layout);
        byte[] exactLayout = Files.readAllBytes(layoutPath);
        RuntimeIdentity identity = identity();
        Map<String, Set<Vector2i>> regions = GalleryRenderVerifier.exactRegions(layout);
        Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles =
                GalleryRenderVerifier.expectedTiles(
                        layout, new GalleryRenderVerifierTest.FakeMap()
                );
        Map<String, Long> previousRegionStates = Map.of(
                GalleryRenderVerifier.MAP_ID + ":0:0", 1L
        );
        GalleryRenderSchedule schedule = GalleryRenderSchedule.create(
                2_000L,
                layoutPath,
                layout,
                identity,
                regions,
                tiles,
                previousRegionStates
        );
        JsonFiles.writeAtomic(
                directory.resolve(GalleryRenderSchedule.FILE_NAME), schedule
        );

        GalleryRenderSchedule loaded = GalleryRenderSchedule.loadAndValidate(
                directory, layoutPath, layout, identity, regions, tiles
        );
        assertEquals(4, loaded.tileCount);
        assertEquals(1, loaded.regionCount);
        assertEquals(GalleryRenderVerifier.MAP_ID, loaded.mapId);

        Files.write(layoutPath, java.util.Arrays.copyOf(exactLayout, exactLayout.length + 1));
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderSchedule.loadAndValidate(
                        directory, layoutPath, layout, identity, regions, tiles
                )
        );
        Files.write(layoutPath, exactLayout);

        String bootId = identity.bootId;
        identity.bootId = UUID.randomUUID().toString();
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderSchedule.loadAndValidate(
                        directory, layoutPath, layout, identity, regions, tiles
                )
        );
        identity.bootId = bootId;

        Map<String, Set<Vector2i>> changedRegions = Map.of(
                GalleryRenderVerifier.MAP_ID, Set.of(new Vector2i(1, 0))
        );
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderSchedule.loadAndValidate(
                        directory, layoutPath, layout, identity, changedRegions, tiles
                )
        );

        TreeSet<StructureRenderVerifier.TileCoordinate> changedTileSet = new TreeSet<>(
                tiles.get(GalleryRenderVerifier.MAP_ID)
        );
        changedTileSet.remove(changedTileSet.getFirst());
        Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> changedTiles = Map.of(
                GalleryRenderVerifier.MAP_ID, changedTileSet
        );
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderSchedule.loadAndValidate(
                        directory, layoutPath, layout, identity, regions, changedTiles
                )
        );
    }

    private static RuntimeIdentity identity() {
        RuntimeIdentity identity = new RuntimeIdentity();
        identity.schemaVersion = 1;
        identity.bootId = UUID.randomUUID().toString();
        identity.runtimeAttestationSha256 = "b".repeat(64);
        identity.startedAt = Instant.ofEpochMilli(1_000L).toString();
        identity.validate();
        return identity;
    }
}
