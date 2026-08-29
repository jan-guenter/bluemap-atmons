package io.github.janguenter.bluemap.atmons.integration;

import com.flowpowered.math.vector.Vector2i;
import de.bluecolored.bluemap.api.BlueMapMap;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

/** Verifies every exact render-mask tile against BlueMap's live state and storage. */
final class StructureRenderVerifier {
    private static final Set<String> COMPLETE_STATES = Set.of(
            "bluemap:rendered", "bluemap:rendered-edge"
    );
    private static final long MAX_TILES = 10_000_000L;

    private StructureRenderVerifier() {
    }

    static Result verify(
            StructureCatalog catalog,
            Map<String, BlueMapMap> maps,
            StructureRenderSchedule schedule,
            Map<String, Set<Vector2i>> regions
    ) throws ReflectiveOperationException, java.io.IOException {
        Map<String, TreeSet<TileCoordinate>> expected = expectedTiles(catalog, maps);
        return verifyExactTiles(
                "Structure",
                maps,
                schedule.scheduledAtEpochMillis,
                schedule.mapCount,
                expected,
                regions
        );
    }

    static Result verifyExactTiles(
            String subject,
            Map<String, BlueMapMap> maps,
            long scheduledAtEpochMillis,
            int scheduledMapCount,
            Map<String, TreeSet<TileCoordinate>> expected,
            Map<String, Set<Vector2i>> regions
    ) throws ReflectiveOperationException, java.io.IOException {
        String lowerSubject = subject.toLowerCase(Locale.ROOT);
        if (expected.size() != scheduledMapCount
                || !expected.keySet().equals(maps.keySet())
                || !expected.keySet().equals(regions.keySet())) {
            throw new IllegalArgumentException(
                    subject + " render maps differ from the exact schedule"
            );
        }
        java.security.MessageDigest digest;
        try {
            digest = java.security.MessageDigest.getInstance("SHA-256");
        } catch (java.security.NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
        Map<String, Integer> states = new TreeMap<>();
        long total = 0;
        long minimumRenderSecond = Math.floorDiv(
                scheduledAtEpochMillis, 1000L
        );
        long verifiedRegions = 0;
        for (Map.Entry<String, TreeSet<TileCoordinate>> entry : expected.entrySet()) {
            BlueMapMap map = maps.get(entry.getKey());
            Inspector inspector = new Inspector(map, lowerSubject);
            for (TileCoordinate tile : entry.getValue()) {
                TileEvidence evidence = inspector.inspect(tile);
                if (!COMPLETE_STATES.contains(evidence.state())) {
                    throw new IllegalArgumentException(
                            subject + " tile is not rendered: " + map.getId() + ":"
                                    + tile.key() + " state=" + evidence.state()
                    );
                }
                if (evidence.renderTime() < minimumRenderSecond
                        || evidence.storageUpdatedAt()
                        < scheduledAtEpochMillis
                        || evidence.contentLength() < 1) {
                    throw new IllegalArgumentException(
                            subject + " tile lacks fresh render/storage evidence: "
                                    + map.getId() + ":" + tile.key()
                    );
                }
                states.merge(evidence.state(), 1, Integer::sum);
                String row = map.getId() + ":" + tile.key() + ":"
                        + evidence.state() + ":" + evidence.renderTime() + ":"
                        + evidence.contentLength() + ":"
                        + evidence.storageUpdatedAt() + ":"
                        + evidence.decodedLength() + "\n";
                digest.update(row.getBytes(StandardCharsets.UTF_8));
                total++;
            }
            Set<Vector2i> expectedRegions = regions.get(entry.getKey());
            if (expectedRegions == null || expectedRegions.isEmpty()) {
                throw new IllegalArgumentException(
                        subject + " map has no exact scheduled regions: " + entry.getKey()
                );
            }
            for (Vector2i region : expectedRegions.stream()
                    .sorted((left, right) -> {
                        int x = Integer.compare(left.getX(), right.getX());
                        return x != 0 ? x : Integer.compare(left.getY(), right.getY());
                    }).toList()) {
                long updatedAt = inspector.regionUpdatedAt(region);
                if (updatedAt < minimumRenderSecond) {
                    throw new IllegalArgumentException(
                            subject + " region task did not complete freshly: "
                                    + map.getId() + ":" + region.getX() + ":"
                                    + region.getY()
                    );
                }
                digest.update((map.getId() + ":region:" + region.getX() + ":"
                        + region.getY() + ":" + updatedAt + "\n")
                        .getBytes(StandardCharsets.UTF_8));
                verifiedRegions++;
            }
        }
        if (total < 1 || total > MAX_TILES) {
            throw new IllegalArgumentException(
                    "Invalid exact " + lowerSubject + " tile total: " + total
            );
        }
        return new Result(
                expected.size(), total, verifiedRegions, Map.copyOf(states),
                HexFormat.of().formatHex(digest.digest())
        );
    }

    static Map<String, Long> regionUpdateSeconds(
            Map<String, BlueMapMap> maps,
            Map<String, Set<Vector2i>> regions
    ) throws ReflectiveOperationException {
        Map<String, Long> states = new TreeMap<>();
        for (Map.Entry<String, Set<Vector2i>> entry : regions.entrySet()) {
            BlueMapMap map = maps.get(entry.getKey());
            if (map == null) {
                throw new IllegalArgumentException(
                        "Missing exact structure map for " + entry.getKey()
                );
            }
            Inspector inspector = new Inspector(map);
            for (Vector2i region : entry.getValue()) {
                states.put(
                        entry.getKey() + ":" + region.getX() + ":" + region.getY(),
                        inspector.regionUpdatedAt(region)
                );
            }
        }
        return states;
    }

    static Map<String, TreeSet<TileCoordinate>> expectedTiles(
            StructureCatalog catalog,
            Map<String, BlueMapMap> maps
    ) {
        Map<String, TreeSet<TileCoordinate>> expected = new TreeMap<>();
        long total = 0;
        for (StructureCatalog.StructureEntry entry : catalog.structures) {
            StructureCatalog.Selection selection = entry.selection;
            if (!"located".equals(selection.status)) {
                continue;
            }
            BlueMapMap map = maps.get(selection.dimension);
            if (map == null) {
                throw new IllegalArgumentException(
                        "Missing exact structure map for " + selection.dimension
                );
            }
            Geometry.BlockBounds bounds = selection.borderedBounds;
            Vector2i first = map.posToTile(bounds.minX(), bounds.minZ());
            Vector2i last = map.posToTile(bounds.maxX(), bounds.maxZ());
            int minX = Math.min(first.getX(), last.getX());
            int maxX = Math.max(first.getX(), last.getX());
            int minZ = Math.min(first.getY(), last.getY());
            int maxZ = Math.max(first.getY(), last.getY());
            long count = Math.multiplyExact(
                    (long) maxX - minX + 1L,
                    (long) maxZ - minZ + 1L
            );
            total = Math.addExact(total, count);
            if (total > MAX_TILES) {
                throw new IllegalArgumentException(
                        "Exact structure render masks exceed the tile safety limit"
                );
            }
            TreeSet<TileCoordinate> tiles = expected.computeIfAbsent(
                    selection.dimension, ignored -> new TreeSet<>()
            );
            for (long x = minX; x <= maxX; x++) {
                for (long z = minZ; z <= maxZ; z++) {
                    tiles.add(new TileCoordinate((int) x, (int) z));
                }
            }
        }
        return expected;
    }

    record TileCoordinate(int x, int z) implements Comparable<TileCoordinate> {
        String key() {
            return x + ":" + z;
        }

        @Override
        public int compareTo(TileCoordinate other) {
            int byX = Integer.compare(x, other.x);
            return byX != 0 ? byX : Integer.compare(z, other.z);
        }
    }

    record TileEvidence(
            String state,
            long renderTime,
            long contentLength,
            long storageUpdatedAt,
            long decodedLength
    ) {
    }

    record Result(
            int mapCount,
            long tileCount,
            long regionCount,
            Map<String, Integer> stateCounts,
            String evidenceSha256
    ) {
    }

    private static final class Inspector {
        private final String subject;
        private final Object tileState;
        private final Object regionState;
        private final Object hiresStorage;
        private final Method getTile;
        private final Method getRegion;
        private final Method readMetadata;
        private final Method readTile;

        private Inspector(BlueMapMap map) throws ReflectiveOperationException {
            this(map, "structure");
        }

        private Inspector(BlueMapMap map, String subject)
                throws ReflectiveOperationException {
            this.subject = subject;
            Object internalMap = map.getClass().getMethod("map").invoke(map);
            tileState = internalMap.getClass().getMethod("getMapTileState")
                    .invoke(internalMap);
            regionState = internalMap.getClass().getMethod("getMapRegionState")
                    .invoke(internalMap);
            Object storage = internalMap.getClass().getMethod("getStorage")
                    .invoke(internalMap);
            hiresStorage = storage.getClass().getMethod("hiresTiles").invoke(storage);
            getTile = tileState.getClass().getMethod("get", int.class, int.class);
            getRegion = regionState.getClass().getMethod("get", int.class, int.class);
            readMetadata = hiresStorage.getClass().getMethod(
                    "readMetadata", int.class, int.class
            );
            readTile = hiresStorage.getClass().getMethod(
                    "read", int.class, int.class
            );
        }

        private TileEvidence inspect(TileCoordinate tile)
                throws ReflectiveOperationException, java.io.IOException {
            Object info = getTile.invoke(tileState, tile.x(), tile.z());
            Object state = info.getClass().getMethod("getState").invoke(info);
            long renderTime = ((Number) info.getClass().getMethod("getRenderTime")
                    .invoke(info)).longValue();
            Object metadata = readMetadata.invoke(hiresStorage, tile.x(), tile.z());
            if (metadata == null) {
                throw new IllegalArgumentException(
                        "Rendered " + subject
                                + " tile is absent from BlueMap storage: " + tile.key()
                );
            }
            long contentLength = ((Number) metadata.getClass()
                    .getMethod("contentLength").invoke(metadata)).longValue();
            Object cacheMetadata = metadata.getClass().getMethod("cacheMetadata")
                    .invoke(metadata);
            long updatedAt = ((Number) cacheMetadata.getClass()
                    .getMethod("updatedAt").invoke(cacheMetadata)).longValue();
            Object storedInput = readTile.invoke(hiresStorage, tile.x(), tile.z());
            if (!(storedInput instanceof InputStream compressedInput)) {
                throw new IllegalArgumentException(
                        "Rendered " + subject
                                + " tile cannot be read from BlueMap storage: "
                                + tile.key()
                );
            }
            long decodedLength = 0;
            Object decodedObject = storedInput.getClass()
                    .getMethod("decompress").invoke(storedInput);
            if (!(decodedObject instanceof InputStream decoded)) {
                throw new IllegalArgumentException(
                        "Rendered " + subject
                                + " tile cannot be decompressed from BlueMap storage: "
                                + tile.key()
                );
            }
            try (compressedInput; decoded) {
                int version = decoded.read();
                int header = decoded.read();
                if (version != 1 || header != 0x07) {
                    throw new IllegalArgumentException(
                            "Rendered " + subject
                                    + " tile has an invalid PRBM header: "
                                    + tile.key()
                    );
                }
                decodedLength = 2;
                byte[] buffer = new byte[8192];
                for (int read = decoded.read(buffer); read >= 0; read = decoded.read(buffer)) {
                    decodedLength += read;
                }
            }
            if (decodedLength < 8) {
                throw new IllegalArgumentException(
                        "Rendered " + subject
                                + " tile has a truncated PRBM payload: " + tile.key()
                );
            }
            return new TileEvidence(
                    state.toString(), renderTime, contentLength, updatedAt,
                    decodedLength
            );
        }

        private long regionUpdatedAt(Vector2i region)
                throws ReflectiveOperationException {
            return ((Number) getRegion.invoke(
                    regionState, region.getX(), region.getY()
            )).longValue();
        }
    }
}
