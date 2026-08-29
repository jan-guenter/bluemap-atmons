package io.github.janguenter.bluemap.atmons.integration;

import com.flowpowered.math.vector.Vector2i;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Set;

/** Per-boot receipt binding render verification to one exact forced schedule. */
final class StructureRenderSchedule {
    static final String FILE_NAME = "structure-render-schedule.json";

    int schemaVersion = 1;
    String scheduledAt;
    long scheduledAtEpochMillis;
    String catalogSha256;
    String mapManifestSha256;
    String worldIdentity;
    String planFingerprint;
    String runtimeAttestationSha256;
    String bootId;
    int mapCount;
    int regionCount;
    String regionDigestSha256;
    long previousRegionMaxEpochSecond;
    String previousRegionStateDigestSha256;

    static StructureRenderSchedule create(
            long scheduledAtEpochMillis,
            Path catalogPath,
            Path mapManifestPath,
            StructureCatalog catalog,
            StructureMapManifest manifest,
            RuntimeIdentity identity,
            Map<String, Set<Vector2i>> regions,
            Map<String, Long> previousRegionStates
    ) throws IOException {
        StructureRenderSchedule schedule = new StructureRenderSchedule();
        schedule.scheduledAtEpochMillis = scheduledAtEpochMillis;
        schedule.scheduledAt = Instant.ofEpochMilli(scheduledAtEpochMillis).toString();
        schedule.catalogSha256 = RuntimeAttestation.sha256(
                Files.readAllBytes(catalogPath)
        );
        schedule.mapManifestSha256 = RuntimeAttestation.sha256(
                Files.readAllBytes(mapManifestPath)
        );
        schedule.worldIdentity = catalog.worldIdentity;
        schedule.planFingerprint = catalog.planFingerprint;
        schedule.runtimeAttestationSha256 = catalog.runtimeAttestationSha256;
        schedule.bootId = identity.bootId;
        schedule.mapCount = regions.size();
        schedule.regionCount = regions.values().stream().mapToInt(Set::size).sum();
        schedule.regionDigestSha256 = regionDigest(regions);
        schedule.previousRegionMaxEpochSecond = previousRegionStates.values().stream()
                .mapToLong(Long::longValue).max().orElse(-1L);
        schedule.previousRegionStateDigestSha256 = regionStateDigest(
                previousRegionStates
        );
        schedule.validate(
                catalogPath, mapManifestPath, catalog, manifest, identity, regions,
                previousRegionStates
        );
        return schedule;
    }

    static StructureRenderSchedule loadAndValidate(
            Path directory,
            Path catalogPath,
            Path mapManifestPath,
            StructureCatalog catalog,
            StructureMapManifest manifest,
            RuntimeIdentity identity,
            Map<String, Set<Vector2i>> regions
    ) throws IOException {
        StructureRenderSchedule schedule = JsonFiles.read(
                directory.resolve(FILE_NAME), StructureRenderSchedule.class
        );
        schedule.validate(
                catalogPath, mapManifestPath, catalog, manifest, identity, regions,
                null
        );
        return schedule;
    }

    private void validate(
            Path catalogPath,
            Path mapManifestPath,
            StructureCatalog catalog,
            StructureMapManifest manifest,
            RuntimeIdentity identity,
            Map<String, Set<Vector2i>> regions,
            Map<String, Long> previousRegionStates
    ) throws IOException {
        identity.validate();
        Instant parsed;
        try {
            parsed = Instant.parse(scheduledAt);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException(
                    "Structure render schedule time is invalid", exception
            );
        }
        int expectedRegions = regions.values().stream().mapToInt(Set::size).sum();
        if (schemaVersion != 1
                || scheduledAtEpochMillis < 1
                || parsed.toEpochMilli() != scheduledAtEpochMillis
                || !RuntimeAttestation.sha256(Files.readAllBytes(catalogPath)).equals(
                        catalogSha256
                )
                || !RuntimeAttestation.sha256(Files.readAllBytes(mapManifestPath)).equals(
                        mapManifestSha256
                )
                || !catalog.worldIdentity.equals(worldIdentity)
                || !catalog.planFingerprint.equals(planFingerprint)
                || !catalog.runtimeAttestationSha256.equals(runtimeAttestationSha256)
                || !manifest.catalogSha256.equals(catalogSha256)
                || !identity.runtimeAttestationSha256.equals(runtimeAttestationSha256)
                || !identity.bootId.equals(bootId)
                || mapCount != regions.size()
                || regionCount != expectedRegions
                || !regionDigest(regions).equals(regionDigestSha256)
                || previousRegionMaxEpochSecond < -1L
                || previousRegionStateDigestSha256 == null
                || !previousRegionStateDigestSha256.matches("[0-9a-f]{64}")
                || Math.floorDiv(scheduledAtEpochMillis, 1000L)
                <= previousRegionMaxEpochSecond
                || (previousRegionStates != null
                && (previousRegionStates.size() != expectedRegions
                || previousRegionStates.values().stream().mapToLong(Long::longValue)
                .max().orElse(-1L) != previousRegionMaxEpochSecond
                || !regionStateDigest(previousRegionStates).equals(
                        previousRegionStateDigestSha256
                )))) {
            throw new IllegalArgumentException(
                    "Structure render schedule does not match this boot and exact regions"
            );
        }
    }

    static String regionDigest(Map<String, Set<Vector2i>> regions) {
        StringBuilder input = new StringBuilder();
        regions.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry ->
                entry.getValue().stream()
                        .sorted((left, right) -> {
                            int x = Integer.compare(left.getX(), right.getX());
                            return x != 0 ? x : Integer.compare(left.getY(), right.getY());
                        })
                        .forEach(region -> input.append(entry.getKey())
                                .append(':').append(region.getX())
                                .append(':').append(region.getY()).append('\n'))
        );
        return RuntimeAttestation.sha256(
                input.toString().getBytes(StandardCharsets.UTF_8)
        );
    }

    static String regionStateDigest(Map<String, Long> states) {
        StringBuilder input = new StringBuilder();
        states.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry ->
                input.append(entry.getKey()).append(':').append(entry.getValue())
                        .append('\n')
        );
        return RuntimeAttestation.sha256(
                input.toString().getBytes(StandardCharsets.UTF_8)
        );
    }
}
