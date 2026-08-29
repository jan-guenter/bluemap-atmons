package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class StructureMapManifestTest {
    @TempDir
    Path temporary;

    @Test
    void bindsCatalogMasksAndConfigBytes() throws Exception {
        Path harness = temporary.resolve("config/bluemap-atmons-integration");
        Path blueMap = temporary.resolve("config/bluemap");
        Path maps = blueMap.resolve("maps");
        Files.createDirectories(harness);
        Files.createDirectories(maps);
        Path catalogPath = harness.resolve("structure-catalog.json");
        Path masksPath = harness.resolve("structure-render-masks.json");
        Files.writeString(catalogPath, "{\"catalog\":1}\n");
        Files.writeString(masksPath, "{\"masks\":1}\n");

        StructureCatalog catalog = new StructureCatalog();
        catalog.worldIdentity = "123e4567-e89b-12d3-a456-426614174000";
        catalog.planFingerprint = "a".repeat(64);
        catalog.runtimeAttestationSha256 = "b".repeat(64);
        StructureCatalog.StructureEntry structure = new StructureCatalog.StructureEntry();
        structure.selection.status = "located";
        structure.selection.dimension = "minecraft:overworld";
        catalog.structures.add(structure);

        RuntimeIdentity identity = new RuntimeIdentity();
        identity.bootId = "123e4567-e89b-42d3-a456-426614174000";
        identity.runtimeAttestationSha256 = catalog.runtimeAttestationSha256;
        identity.startedAt = "2099-01-01T00:00:00Z";
        JsonFiles.writeAtomic(harness.resolve(RuntimeIdentity.FILE_NAME), identity);

        String mapId = BlueMapMapContract.safeMapId("minecraft:overworld");
        Path config = maps.resolve(mapId + ".conf");
        Files.writeString(config, "render-mask: []\n");
        StructureMapManifest manifest = new StructureMapManifest();
        manifest.schemaVersion = 1;
        manifest.catalogSha256 = RuntimeAttestation.sha256(Files.readAllBytes(catalogPath));
        manifest.renderMasksSha256 = RuntimeAttestation.sha256(Files.readAllBytes(masksPath));
        manifest.worldIdentity = catalog.worldIdentity;
        manifest.planFingerprint = catalog.planFingerprint;
        manifest.runtimeAttestationSha256 = catalog.runtimeAttestationSha256;
        manifest.world = "/data/world";
        manifest.storage = "file";
        StructureMapManifest.MapEntry entry = new StructureMapManifest.MapEntry();
        entry.dimension = "minecraft:overworld";
        entry.mapId = mapId;
        entry.configFile = "maps/" + mapId + ".conf";
        entry.maskCount = 1;
        entry.sizeBytes = Files.size(config);
        entry.sha256 = RuntimeAttestation.sha256(Files.readAllBytes(config));
        manifest.maps = List.of(entry);
        JsonFiles.writeAtomic(blueMap.resolve(StructureMapManifest.FILE_NAME), manifest);

        assertDoesNotThrow(() -> StructureMapManifest.loadAndValidate(
                harness, catalogPath, masksPath, catalog
        ));
        Files.writeString(config, "tampered\n");
        assertThrows(IllegalArgumentException.class, () ->
                StructureMapManifest.loadAndValidate(harness, catalogPath, masksPath, catalog)
        );
    }
}
