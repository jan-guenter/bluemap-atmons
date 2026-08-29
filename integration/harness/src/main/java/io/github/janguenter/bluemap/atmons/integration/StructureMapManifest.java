package io.github.janguenter.bluemap.atmons.integration;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Exact generated BlueMap config ledger bound to a completed structure catalog. */
final class StructureMapManifest {
    static final String FILE_NAME = "atmons-structure-maps.json";

    int schemaVersion;
    String catalogSha256;
    String renderMasksSha256;
    String worldIdentity;
    String planFingerprint;
    String runtimeAttestationSha256;
    String world;
    String storage;
    List<MapEntry> maps = List.of();

    static final class MapEntry {
        String dimension;
        String mapId;
        String configFile;
        int maskCount;
        long sizeBytes;
        String sha256;
    }

    static StructureMapManifest loadAndValidate(
            Path harnessDirectory,
            Path catalogPath,
            Path masksPath,
            StructureCatalog catalog
    ) throws IOException {
        Path configRoot = harnessDirectory.getParent().resolve("bluemap").normalize();
        Path manifestPath = configRoot.resolve(FILE_NAME);
        StructureMapManifest manifest = JsonFiles.read(
                manifestPath, StructureMapManifest.class
        );
        byte[] catalogBytes = Files.readAllBytes(catalogPath);
        byte[] maskBytes = Files.readAllBytes(masksPath);
        if (manifest.schemaVersion != 1
                || !RuntimeAttestation.sha256(catalogBytes).equals(manifest.catalogSha256)
                || !RuntimeAttestation.sha256(maskBytes).equals(manifest.renderMasksSha256)
                || !catalog.worldIdentity.equals(manifest.worldIdentity)
                || !catalog.planFingerprint.equals(manifest.planFingerprint)
                || !catalog.runtimeAttestationSha256.equals(
                        manifest.runtimeAttestationSha256
                )
                || manifest.world == null || !Path.of(manifest.world).isAbsolute()
                || manifest.storage == null || manifest.storage.isBlank()
                || manifest.maps == null || manifest.maps.isEmpty()) {
            throw new IllegalArgumentException(
                    "Structure map manifest is stale or incomplete"
            );
        }

        Map<String, Integer> expectedMasks = new HashMap<>();
        for (StructureCatalog.StructureEntry structure : catalog.structures) {
            if ("located".equals(structure.selection.status)) {
                expectedMasks.merge(structure.selection.dimension, 1, Integer::sum);
            }
        }
        Set<String> observed = new HashSet<>();
        RuntimeIdentity runtimeIdentity = JsonFiles.read(
                harnessDirectory.resolve(RuntimeIdentity.FILE_NAME), RuntimeIdentity.class
        );
        runtimeIdentity.validate();
        Instant processStart = Instant.parse(runtimeIdentity.startedAt);
        if (Files.getLastModifiedTime(manifestPath).toInstant().isAfter(processStart)) {
            throw new IllegalArgumentException(
                    "BlueMap must restart after structure map configs are generated"
            );
        }
        for (MapEntry map : manifest.maps) {
            String expectedMapId = BlueMapMapContract.safeMapId(map.dimension);
            String expectedConfig = "maps/" + expectedMapId + ".conf";
            if (!observed.add(map.dimension)
                    || !expectedMasks.containsKey(map.dimension)
                    || !expectedMapId.equals(map.mapId)
                    || !expectedConfig.equals(map.configFile)
                    || map.maskCount != expectedMasks.get(map.dimension)
                    || map.sizeBytes < 1
                    || map.sha256 == null || !map.sha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException(
                        "Structure map entry is invalid: " + map.dimension
                );
            }
            Path configPath = configRoot.resolve(map.configFile).normalize();
            if (!configPath.startsWith(configRoot)
                    || !Files.isRegularFile(configPath)
                    || Files.size(configPath) != map.sizeBytes
                    || !RuntimeAttestation.sha256(Files.readAllBytes(configPath)).equals(
                            map.sha256
                    )
                    || Files.getLastModifiedTime(configPath).toInstant().isAfter(
                            processStart
                    )) {
                throw new IllegalArgumentException(
                        "Structure map config bytes are stale: " + map.configFile
                );
            }
        }
        if (!observed.equals(expectedMasks.keySet())) {
            throw new IllegalArgumentException(
                    "Structure map manifest dimensions do not match located structures"
            );
        }
        return manifest;
    }
}
