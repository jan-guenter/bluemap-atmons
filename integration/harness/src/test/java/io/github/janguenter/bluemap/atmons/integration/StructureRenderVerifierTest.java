package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
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

class StructureRenderVerifierTest {
    @Test
    void requiresEveryMaskTileToBeFreshRenderedAndStored() throws Exception {
        StructureCatalog catalog = catalog();
        FakeMap map = new FakeMap("bluemap:rendered");
        StructureRenderSchedule schedule = new StructureRenderSchedule();
        schedule.mapCount = 1;
        schedule.scheduledAtEpochMillis = 1_000_000L;

        StructureRenderVerifier.Result result = StructureRenderVerifier.verify(
                catalog,
                Map.of("minecraft:overworld", map),
                schedule,
                Map.of("minecraft:overworld", Set.of(Vector2i.ZERO))
        );
        assertEquals(4, result.tileCount());
        assertEquals(1, result.regionCount());
        assertEquals(4, result.stateCounts().get("bluemap:rendered"));

        map.internal.tileState.state = "bluemap:render-error";
        assertThrows(
                IllegalArgumentException.class,
                () -> StructureRenderVerifier.verify(
                        catalog,
                        Map.of("minecraft:overworld", map),
                        schedule,
                        Map.of("minecraft:overworld", Set.of(Vector2i.ZERO))
                )
        );
    }

    private static StructureCatalog catalog() {
        StructureCatalog catalog = new StructureCatalog();
        StructureCatalog.StructureEntry entry = new StructureCatalog.StructureEntry();
        entry.selection.status = "located";
        entry.selection.dimension = "minecraft:overworld";
        entry.selection.borderedBounds = new Geometry.BlockBounds(0, 0, 0, 31, 1, 31);
        catalog.structures.add(entry);
        return catalog;
    }

    public static final class FakeMap implements BlueMapMap {
        final FakeInternalMap internal;

        FakeMap(String state) {
            internal = new FakeInternalMap(state);
        }

        public FakeInternalMap map() {
            return internal;
        }

        @Override public String getId() { return "atmons_minecraft_overworld"; }
        @Override public String getName() { return getId(); }
        @Override public BlueMapWorld getWorld() { return null; }
        @Override public AssetStorage getAssetStorage() { return null; }
        @Override public Map<String, MarkerSet> getMarkerSets() { return new HashMap<>(); }
        @Override public Vector2i getTileSize() { return new Vector2i(16, 16); }
        @Override public Vector2i getTileOffset() { return Vector2i.ZERO; }
        @Override public void setFrozen(boolean frozen) { }
        @Override public boolean isFrozen() { return false; }
        @Override @SuppressWarnings("removal")
        public void setTileFilter(Predicate<Vector2i> filter) { }
        @Override @SuppressWarnings("removal")
        public Predicate<Vector2i> getTileFilter() { return ignored -> true; }
    }

    public static final class FakeInternalMap {
        final FakeTileState tileState;
        final FakeStorage storage = new FakeStorage();

        FakeInternalMap(String state) {
            tileState = new FakeTileState(state);
        }

        public FakeTileState getMapTileState() { return tileState; }
        public FakeRegionState getMapRegionState() { return new FakeRegionState(); }
        public FakeStorage getStorage() { return storage; }
    }

    public static final class FakeRegionState {
        public int get(int x, int z) { return 1000; }
    }

    public static final class FakeTileState {
        String state;

        FakeTileState(String state) { this.state = state; }
        public FakeInfo get(int x, int z) { return new FakeInfo(state); }
    }

    public record FakeInfo(String state) {
        public String getState() { return state; }
        public int getRenderTime() { return 1000; }
    }

    public static final class FakeStorage {
        final FakeGrid hires = new FakeGrid();
        public FakeGrid hiresTiles() { return hires; }
    }

    public static final class FakeGrid {
        public FakeMetadata readMetadata(int x, int z) {
            return new FakeMetadata(new FakeCacheMetadata(1_000_001L), 128L);
        }

        public FakeCompressedInput read(int x, int z) {
            return new FakeCompressedInput();
        }
    }

    public static final class FakeCompressedInput extends InputStream {
        @Override public int read() { return -1; }
        public InputStream decompress() {
            return new ByteArrayInputStream(new byte[]{1, 7, 0, 0, 0, 0, 0, 0});
        }
    }

    public record FakeMetadata(FakeCacheMetadata cacheMetadata, long contentLength) { }
    public record FakeCacheMetadata(long updatedAt) { }
}
