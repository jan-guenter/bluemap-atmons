package io.github.janguenter.bluemap.atmons.integration;

import com.flowpowered.math.vector.Vector2i;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/** Per-boot receipt binding gallery verification to one exact forced schedule. */
final class GalleryRenderSchedule {
    static final String FILE_NAME = "gallery-render-schedule.json";

    int schemaVersion = 1;
    String scheduledAt;
    long scheduledAtEpochMillis;
    String galleryLayoutSha256;
    String compositionId;
    String dimension;
    String mapId;
    String runtimeAttestationSha256;
    String bootId;
    int mapCount;
    long regionCount;
    String regionDigestSha256;
    long tileCount;
    String tileDigestSha256;
    long previousRegionMaxEpochSecond;
    String previousRegionStateDigestSha256;

    static GalleryRenderSchedule create(
            long scheduledAtEpochMillis,
            Path galleryLayoutPath,
            GalleryLayout layout,
            RuntimeIdentity identity,
            Map<String, Set<Vector2i>> regions,
            Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles,
            Map<String, Long> previousRegionStates
    ) throws IOException {
        GalleryRenderSchedule schedule = new GalleryRenderSchedule();
        schedule.scheduledAtEpochMillis = scheduledAtEpochMillis;
        schedule.scheduledAt = Instant.ofEpochMilli(scheduledAtEpochMillis).toString();
        schedule.galleryLayoutSha256 = RuntimeAttestation.sha256(
                Files.readAllBytes(galleryLayoutPath)
        );
        schedule.compositionId = layout.compositionId;
        schedule.dimension = layout.dimension;
        schedule.mapId = layout.mapId;
        schedule.runtimeAttestationSha256 = identity.runtimeAttestationSha256;
        schedule.bootId = identity.bootId;
        schedule.mapCount = regions.size();
        schedule.regionCount = regionCount(regions);
        schedule.regionDigestSha256 = StructureRenderSchedule.regionDigest(regions);
        schedule.tileCount = tileCount(tiles);
        schedule.tileDigestSha256 = GalleryRenderVerifier.tileDigest(tiles);
        schedule.previousRegionMaxEpochSecond = previousRegionStates.values().stream()
                .mapToLong(Long::longValue).max().orElse(-1L);
        schedule.previousRegionStateDigestSha256 =
                StructureRenderSchedule.regionStateDigest(previousRegionStates);
        schedule.validate(
                galleryLayoutPath,
                layout,
                identity,
                regions,
                tiles,
                previousRegionStates
        );
        return schedule;
    }

    static GalleryRenderSchedule loadAndValidate(
            Path directory,
            Path galleryLayoutPath,
            GalleryLayout layout,
            RuntimeIdentity identity,
            Map<String, Set<Vector2i>> regions,
            Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles
    ) throws IOException {
        GalleryRenderSchedule schedule = JsonFiles.read(
                directory.resolve(FILE_NAME), GalleryRenderSchedule.class
        );
        schedule.validate(
                galleryLayoutPath, layout, identity, regions, tiles, null
        );
        return schedule;
    }

    private void validate(
            Path galleryLayoutPath,
            GalleryLayout layout,
            RuntimeIdentity identity,
            Map<String, Set<Vector2i>> regions,
            Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles,
            Map<String, Long> previousRegionStates
    ) throws IOException {
        GalleryRenderVerifier.requireComposerLayout(layout);
        identity.validate();
        Instant parsed;
        Instant bootStarted;
        try {
            parsed = Instant.parse(scheduledAt);
            bootStarted = Instant.parse(identity.startedAt);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException(
                    "Gallery render schedule time is invalid", exception
            );
        }
        long expectedRegions = regionCount(regions);
        long expectedTiles = tileCount(tiles);
        if (schemaVersion != 1
                || scheduledAtEpochMillis < 1L
                || parsed.toEpochMilli() != scheduledAtEpochMillis
                || scheduledAtEpochMillis < bootStarted.toEpochMilli()
                || !RuntimeAttestation.sha256(Files.readAllBytes(galleryLayoutPath))
                .equals(galleryLayoutSha256)
                || !layout.compositionId.equals(compositionId)
                || !GalleryRenderVerifier.DIMENSION.equals(dimension)
                || !GalleryRenderVerifier.MAP_ID.equals(mapId)
                || !identity.runtimeAttestationSha256.equals(runtimeAttestationSha256)
                || !identity.bootId.equals(bootId)
                || mapCount != 1
                || !regions.keySet().equals(Set.of(mapId))
                || !tiles.keySet().equals(Set.of(mapId))
                || regionCount != expectedRegions
                || expectedRegions < 1L
                || !StructureRenderSchedule.regionDigest(regions).equals(
                        regionDigestSha256
                )
                || tileCount != expectedTiles
                || expectedTiles < 1L
                || !GalleryRenderVerifier.tileDigest(tiles).equals(tileDigestSha256)
                || previousRegionMaxEpochSecond < -1L
                || previousRegionStateDigestSha256 == null
                || !previousRegionStateDigestSha256.matches("[0-9a-f]{64}")
                || Math.floorDiv(scheduledAtEpochMillis, 1000L)
                <= previousRegionMaxEpochSecond
                || (previousRegionStates != null
                && (previousRegionStates.size() != expectedRegions
                || previousRegionStates.values().stream().anyMatch(value -> value < -1L)
                || previousRegionStates.values().stream().mapToLong(Long::longValue)
                .max().orElse(-1L) != previousRegionMaxEpochSecond
                || !StructureRenderSchedule.regionStateDigest(previousRegionStates)
                .equals(previousRegionStateDigestSha256)))) {
            throw new IllegalArgumentException(
                    "Gallery render schedule does not match this boot and exact map bounds"
            );
        }
    }

    private static long regionCount(Map<String, Set<Vector2i>> regions) {
        return regions.values().stream().mapToLong(Set::size).sum();
    }

    private static long tileCount(
            Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles
    ) {
        return tiles.values().stream().mapToLong(Set::size).sum();
    }
}
