package io.github.janguenter.bluemap.atmons.integration;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/** Coordinate conversions shared by cataloging, generation, rendering, and tests. */
public final class Geometry {
    private Geometry() {
    }

    public record BlockBounds(
            int minX,
            int minY,
            int minZ,
            int maxX,
            int maxY,
            int maxZ
    ) {
        public BlockBounds {
            if (minX > maxX || minY > maxY || minZ > maxZ) {
                throw new IllegalArgumentException("Inverted block bounds");
            }
        }

        public BlockBounds inflate(int border, int minBuildY, int maxBuildYInclusive) {
            if (border < 0) {
                throw new IllegalArgumentException("border must not be negative");
            }
            return new BlockBounds(
                    Math.subtractExact(minX, border),
                    Math.max(minBuildY, Math.subtractExact(minY, border)),
                    Math.subtractExact(minZ, border),
                    Math.addExact(maxX, border),
                    Math.min(maxBuildYInclusive, Math.addExact(maxY, border)),
                    Math.addExact(maxZ, border)
            );
        }

        public BlockBounds clampY(int minBuildY, int maxBuildYInclusive) {
            if (minBuildY > maxBuildYInclusive) {
                throw new IllegalArgumentException("Inverted build-height range");
            }
            int clampedMinY = Math.max(minY, minBuildY);
            int clampedMaxY = Math.min(maxY, maxBuildYInclusive);
            if (clampedMinY > clampedMaxY) {
                throw new IllegalArgumentException(
                        "Block bounds are outside the dimension build height"
                );
            }
            return new BlockBounds(
                    minX, clampedMinY, minZ,
                    maxX, clampedMaxY, maxZ
            );
        }

        public ChunkBounds chunks() {
            return new ChunkBounds(
                    Math.floorDiv(minX, 16),
                    Math.floorDiv(minZ, 16),
                    Math.floorDiv(maxX, 16),
                    Math.floorDiv(maxZ, 16)
            );
        }
    }

    public record ChunkBounds(int minX, int minZ, int maxX, int maxZ) {
        public ChunkBounds {
            if (minX > maxX || minZ > maxZ) {
                throw new IllegalArgumentException("Inverted chunk bounds");
            }
        }

        public long count() {
            return Math.multiplyExact(
                    (long) maxX - minX + 1L,
                    (long) maxZ - minZ + 1L
            );
        }

        public List<ChunkCoordinate> coordinates(String dimension) {
            long count = count();
            if (count > Integer.MAX_VALUE) {
                throw new IllegalArgumentException("Chunk bounds are too large to materialize");
            }
            List<ChunkCoordinate> coordinates = new ArrayList<>((int) count);
            for (long chunkX = minX; chunkX <= maxX; chunkX++) {
                for (long chunkZ = minZ; chunkZ <= maxZ; chunkZ++) {
                    coordinates.add(new ChunkCoordinate(
                            dimension, (int) chunkX, (int) chunkZ
                    ));
                }
            }
            return List.copyOf(coordinates);
        }

        public Set<RegionCoordinate> regions() {
            Set<RegionCoordinate> regions = new LinkedHashSet<>();
            for (long chunkX = minX; chunkX <= maxX; chunkX++) {
                for (long chunkZ = minZ; chunkZ <= maxZ; chunkZ++) {
                    regions.add(new RegionCoordinate(
                            (int) Math.floorDiv(chunkX, 32L),
                            (int) Math.floorDiv(chunkZ, 32L)
                    ));
                }
            }
            return Set.copyOf(regions);
        }
    }

    public record ChunkCoordinate(String dimension, int x, int z) {
        public ChunkCoordinate {
            if (dimension == null || dimension.isBlank()) {
                throw new IllegalArgumentException("dimension is required");
            }
        }

        public String key() {
            return dimension + ":" + x + ":" + z;
        }
    }

    public record RegionCoordinate(int x, int z) {
    }
}
