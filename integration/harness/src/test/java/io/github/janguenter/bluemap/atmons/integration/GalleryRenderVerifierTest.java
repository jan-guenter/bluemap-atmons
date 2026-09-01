package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.flowpowered.math.vector.Vector2i;
import de.bluecolored.bluemap.api.AssetStorage;
import de.bluecolored.bluemap.api.BlueMapMap;
import de.bluecolored.bluemap.api.BlueMapWorld;
import de.bluecolored.bluemap.api.markers.MarkerSet;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.function.Predicate;
import org.junit.jupiter.api.Test;

class GalleryRenderVerifierTest {
    @Test
    void campusBoundsProduceOnlyTheFourExactMapMaskRegions() {
        GalleryLayout layout = layout(
                new Geometry.BlockBounds(8192, 194, 8192, 9203, 256, 8985)
        );
        layout.galleries.getFirst().tileBounds = new Geometry.BlockBounds(
                8192, 194, 8185, 8223, 220, 8216
        );

        Set<Vector2i> regions = GalleryRenderVerifier.exactRegions(layout)
                .get(GalleryRenderVerifier.MAP_ID);

        assertEquals(Set.of(
                new Vector2i(16, 16),
                new Vector2i(16, 17),
                new Vector2i(17, 16),
                new Vector2i(17, 17)
        ), regions);
        assertFalse(regions.contains(new Vector2i(16, 15)));
        assertEquals(
                4,
                GalleryRenderVerifier.expectedTiles(
                        layout,
                        new FakeMap(new Vector2i(32, 32), new Vector2i(2, 2))
                ).get(GalleryRenderVerifier.MAP_ID).size()
        );
    }

    @Test
    void expectedTilesExcludeCampusGapsAndDeduplicateGalleryOverlap() {
        GalleryLayout layout = layout(
                new Geometry.BlockBounds(0, 0, 0, 95, 1, 15)
        );
        layout.galleries = java.util.List.of(
                gallery("first", new Geometry.BlockBounds(0, 0, 0, 31, 1, 15)),
                gallery("second", new Geometry.BlockBounds(16, 0, 0, 47, 1, 15))
        );
        layout.validate();

        assertEquals(
                3,
                GalleryRenderVerifier.expectedTiles(layout, new FakeMap())
                        .get(GalleryRenderVerifier.MAP_ID).size()
        );
    }

    @Test
    void regionPlanUsesFloorDivisionAtNegativeAndPositiveBoundaries() {
        GalleryLayout layout = layout(
                new Geometry.BlockBounds(-1, 0, 0, 512, 1, 0)
        );

        assertEquals(
                Set.of(new Vector2i(-1, 0), Vector2i.ZERO, new Vector2i(1, 0)),
                GalleryRenderVerifier.exactRegions(layout)
                        .get(GalleryRenderVerifier.MAP_ID)
        );
    }

    @Test
    void requiresEveryCampusTileAndRegionToHaveFreshStoredEvidence() throws Exception {
        GalleryLayout layout = layout(
                new Geometry.BlockBounds(0, 0, 0, 31, 1, 31)
        );
        FakeMap map = new FakeMap();
        GalleryRenderSchedule schedule = new GalleryRenderSchedule();
        schedule.mapCount = 1;
        schedule.scheduledAtEpochMillis = 1_000_000L;
        Map<String, Set<Vector2i>> regions = GalleryRenderVerifier.exactRegions(layout);

        StructureRenderVerifier.Result result = GalleryRenderVerifier.verify(
                layout, map, schedule, regions
        );
        assertEquals(4, result.tileCount());
        assertEquals(1, result.regionCount());
        assertEquals(4, result.stateCounts().get("bluemap:rendered"));

        map.internal.tileState.state = "bluemap:render-error";
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.tileState.state = "bluemap:rendered";

        map.internal.tileState.renderTime = 999L;
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.tileState.renderTime = 1000L;

        map.internal.storage.hires.updatedAt = 999_999L;
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.storage.hires.updatedAt = 1_000_001L;

        map.internal.regionState.updatedAt = 999L;
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
    }

    @Test
    void rejectsMissingEmptyAndInvalidGalleryStorage() {
        GalleryLayout layout = layout(
                new Geometry.BlockBounds(0, 0, 0, 15, 1, 15)
        );
        FakeMap map = new FakeMap();
        GalleryRenderSchedule schedule = new GalleryRenderSchedule();
        schedule.mapCount = 1;
        schedule.scheduledAtEpochMillis = 1_000_000L;
        Map<String, Set<Vector2i>> regions = GalleryRenderVerifier.exactRegions(layout);

        map.internal.storage.hires.metadataPresent = false;
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.storage.hires.metadataPresent = true;
        map.internal.storage.hires.readable = false;
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.storage.hires.readable = true;
        map.internal.storage.hires.contentLength = 0L;
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.storage.hires.contentLength = 128L;
        map.internal.storage.hires.payload = new byte[]{1, 6, 0, 0, 0, 0, 0, 0};
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
        map.internal.storage.hires.payload = new byte[]{1, 7, 0};
        assertThrows(
                IllegalArgumentException.class,
                () -> GalleryRenderVerifier.verify(layout, map, schedule, regions)
        );
    }

    static GalleryLayout layout(Geometry.BlockBounds bounds) {
        GalleryLayout layout = new GalleryLayout();
        layout.schemaVersion = 1;
        layout.compositionId = "a".repeat(64);
        layout.composerVersion = "2.4.1";
        layout.dimension = GalleryRenderVerifier.DIMENSION;
        layout.mapId = GalleryRenderVerifier.MAP_ID;
        layout.bounds = bounds;
        layout.galleries = java.util.List.of(gallery("test", bounds));
        layout.validate();
        return layout;
    }

    private static GalleryLayout.Gallery gallery(
            String id,
            Geometry.BlockBounds bounds
    ) {
        GalleryLayout.Gallery gallery = new GalleryLayout.Gallery();
        gallery.id = id;
        gallery.bounds = bounds;
        gallery.tileBounds = bounds;
        gallery.marker = new GalleryLayout.Marker();
        gallery.marker.id = id;
        gallery.marker.label = id;
        gallery.marker.position = new GalleryLayout.Position(
                bounds.minX(), bounds.minY(), bounds.minZ()
        );
        gallery.functions = new GalleryLayout.Functions();
        gallery.functions.load = "test:load";
        gallery.functions.prepare = "test:prepare";
        gallery.functions.build = "test:build";
        gallery.functions.verify = "test:verify";
        gallery.functions.release = "test:release";
        gallery.functions.clear = "test:clear";
        gallery.completion = new GalleryLayout.Completion();
        gallery.completion.mode = "terminal-predicate";
        gallery.completion.objective = "bma_done";
        gallery.completion.player = "#" + id;
        gallery.completion.timeoutTicks = 20;
        return gallery;
    }

    public static final class FakeMap implements BlueMapMap {
        final FakeInternalMap internal = new FakeInternalMap();
        private final Vector2i tileSize;
        private final Vector2i tileOffset;

        FakeMap() {
            this(new Vector2i(16, 16), Vector2i.ZERO);
        }

        FakeMap(Vector2i tileSize, Vector2i tileOffset) {
            this.tileSize = tileSize;
            this.tileOffset = tileOffset;
        }

        public FakeInternalMap map() {
            return internal;
        }

        @Override public String getId() { return GalleryRenderVerifier.MAP_ID; }
        @Override public String getName() { return getId(); }
        @Override public BlueMapWorld getWorld() { return null; }
        @Override public AssetStorage getAssetStorage() { return null; }
        @Override public Map<String, MarkerSet> getMarkerSets() { return new HashMap<>(); }
        @Override public Vector2i getTileSize() { return tileSize; }
        @Override public Vector2i getTileOffset() { return tileOffset; }
        @Override public void setFrozen(boolean frozen) { }
        @Override public boolean isFrozen() { return false; }
        @Override @SuppressWarnings("removal")
        public void setTileFilter(Predicate<Vector2i> filter) { }
        @Override @SuppressWarnings("removal")
        public Predicate<Vector2i> getTileFilter() { return ignored -> true; }
    }

    public static final class FakeInternalMap {
        final FakeTileState tileState = new FakeTileState();
        final FakeRegionState regionState = new FakeRegionState();
        final FakeStorage storage = new FakeStorage();

        public FakeTileState getMapTileState() { return tileState; }
        public FakeRegionState getMapRegionState() { return regionState; }
        public FakeStorage getStorage() { return storage; }
    }

    public static final class FakeRegionState {
        long updatedAt = 1000L;
        public long get(int x, int z) { return updatedAt; }
    }

    public static final class FakeTileState {
        String state = "bluemap:rendered";
        long renderTime = 1000L;
        public FakeInfo get(int x, int z) { return new FakeInfo(state, renderTime); }
    }

    public record FakeInfo(String state, long renderTime) {
        public String getState() { return state; }
        public long getRenderTime() { return renderTime; }
    }

    public static final class FakeStorage {
        final FakeGrid hires = new FakeGrid();
        public FakeGrid hiresTiles() { return hires; }
    }

    public static final class FakeGrid {
        boolean metadataPresent = true;
        boolean readable = true;
        long updatedAt = 1_000_001L;
        long contentLength = 128L;
        byte[] payload = new byte[]{1, 7, 0, 0, 0, 0, 0, 0};

        public FakeMetadata readMetadata(int x, int z) {
            return metadataPresent
                    ? new FakeMetadata(new FakeCacheMetadata(updatedAt), contentLength)
                    : null;
        }

        public FakeCompressedInput read(int x, int z) {
            return readable ? new FakeCompressedInput(payload) : null;
        }
    }

    public static final class FakeCompressedInput extends InputStream {
        private final byte[] payload;

        FakeCompressedInput(byte[] payload) {
            this.payload = payload.clone();
        }

        @Override public int read() { return -1; }

        public InputStream decompress() {
            return new ByteArrayInputStream(payload);
        }
    }

    public record FakeMetadata(FakeCacheMetadata cacheMetadata, long contentLength) { }
    public record FakeCacheMetadata(long updatedAt) { }
}
