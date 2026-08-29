package io.github.janguenter.bluemap.atmons.integration;

import com.flowpowered.math.vector.Vector2i;
import de.bluecolored.bluemap.api.BlueMapMap;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/** Exact render plan and fresh storage verification for the composed gallery map. */
final class GalleryRenderVerifier {
    static final String DIMENSION = "minecraft:overworld";
    static final String MAP_ID = "atmons_integration";

    private static final long MAX_TILES = 10_000_000L;
    private static final long MAX_REGIONS = 1_000_000L;

    private GalleryRenderVerifier() {
    }

    static StructureRenderVerifier.Result verify(
            GalleryLayout layout,
            BlueMapMap map,
            GalleryRenderSchedule schedule,
            Map<String, Set<Vector2i>> regions
    ) throws ReflectiveOperationException, java.io.IOException {
        Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles =
                expectedTiles(layout, map);
        return StructureRenderVerifier.verifyExactTiles(
                "Gallery",
                Map.of(MAP_ID, map),
                schedule.scheduledAtEpochMillis,
                schedule.mapCount,
                tiles,
                regions
        );
    }

    static Map<String, Set<Vector2i>> exactRegions(GalleryLayout layout) {
        requireComposerLayout(layout);
        Geometry.BlockBounds bounds = layout.bounds;
        int minX = Math.floorDiv(bounds.minX(), 512);
        int minZ = Math.floorDiv(bounds.minZ(), 512);
        int maxX = Math.floorDiv(bounds.maxX(), 512);
        int maxZ = Math.floorDiv(bounds.maxZ(), 512);
        long width = (long) maxX - minX + 1L;
        long depth = (long) maxZ - minZ + 1L;
        if (width > MAX_REGIONS || depth > MAX_REGIONS
                || width > MAX_REGIONS / depth) {
            throw new IllegalArgumentException(
                    "Exact gallery bounds exceed the region safety limit"
            );
        }
        Set<Vector2i> regions = new LinkedHashSet<>((int) (width * depth));
        for (long x = minX; x <= maxX; x++) {
            for (long z = minZ; z <= maxZ; z++) {
                regions.add(new Vector2i((int) x, (int) z));
            }
        }
        return Map.of(MAP_ID, Set.copyOf(regions));
    }

    static Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> expectedTiles(
            GalleryLayout layout,
            BlueMapMap map
    ) {
        requireComposerLayout(layout);
        if (map == null || !MAP_ID.equals(map.getId())) {
            throw new IllegalArgumentException(
                    "Gallery render map is not the exact atmons_integration map"
            );
        }
        Vector2i tileSize = map.getTileSize();
        Vector2i tileOffset = map.getTileOffset();
        if (tileSize == null || tileOffset == null
                || tileSize.getX() < 1 || tileSize.getY() < 1) {
            throw new IllegalArgumentException("Gallery map has an invalid tile grid");
        }
        TreeSet<StructureRenderVerifier.TileCoordinate> tiles = new TreeSet<>();
        long visited = 0L;
        for (GalleryLayout.Gallery gallery : layout.galleries) {
            Geometry.BlockBounds bounds = gallery.tileBounds;
            Vector2i first = map.posToTile(bounds.minX(), bounds.minZ());
            Vector2i last = map.posToTile(bounds.maxX(), bounds.maxZ());
            int minX = Math.min(first.getX(), last.getX());
            int minZ = Math.min(first.getY(), last.getY());
            int maxX = Math.max(first.getX(), last.getX());
            int maxZ = Math.max(first.getY(), last.getY());
            long width = (long) maxX - minX + 1L;
            long depth = (long) maxZ - minZ + 1L;
            if (width > MAX_TILES || depth > MAX_TILES
                    || width > MAX_TILES / depth
                    || visited > MAX_TILES - width * depth) {
                throw new IllegalArgumentException(
                        "Exact gallery tile bounds exceed the tile safety limit"
                );
            }
            visited += width * depth;
            for (long x = minX; x <= maxX; x++) {
                for (long z = minZ; z <= maxZ; z++) {
                    tiles.add(new StructureRenderVerifier.TileCoordinate(
                            (int) x, (int) z
                    ));
                }
            }
        }
        if (tiles.isEmpty()) {
            throw new IllegalArgumentException("Exact gallery tile set is empty");
        }
        return Map.of(MAP_ID, tiles);
    }

    static String tileDigest(
            Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles
    ) {
        StringBuilder input = new StringBuilder();
        tiles.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry ->
                entry.getValue().forEach(tile -> input.append(entry.getKey())
                        .append(':').append(tile.x())
                        .append(':').append(tile.z()).append('\n'))
        );
        return RuntimeAttestation.sha256(
                input.toString().getBytes(StandardCharsets.UTF_8)
        );
    }

    static void requireComposerLayout(GalleryLayout layout) {
        layout.validate();
        if (layout.galleries.isEmpty()
                || !DIMENSION.equals(layout.dimension)
                || !MAP_ID.equals(layout.mapId)) {
            throw new IllegalArgumentException(
                    "Gallery render requires the exact composed atmons_integration layout"
            );
        }
    }
}
