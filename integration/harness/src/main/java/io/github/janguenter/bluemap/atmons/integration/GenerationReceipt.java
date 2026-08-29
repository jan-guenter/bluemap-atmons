package io.github.janguenter.bluemap.atmons.integration;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;

/** Immutable completion evidence for the exact catalog-derived chunk set. */
final class GenerationReceipt {
    static final String FILE_NAME = "structure-generation-receipt.json";

    int schemaVersion = 1;
    String completedAt;
    String catalogSha256;
    String worldIdentity;
    String planFingerprint;
    String runtimeAttestationSha256;
    int targetCount;
    String targetDigestSha256;

    static GenerationReceipt create(
            Path catalogPath,
            StructureCatalog catalog,
            List<Geometry.ChunkCoordinate> targets
    ) throws IOException {
        GenerationReceipt receipt = new GenerationReceipt();
        receipt.completedAt = Instant.now().toString();
        receipt.catalogSha256 = RuntimeAttestation.sha256(
                Files.readAllBytes(catalogPath)
        );
        receipt.worldIdentity = catalog.worldIdentity;
        receipt.planFingerprint = catalog.planFingerprint;
        receipt.runtimeAttestationSha256 = catalog.runtimeAttestationSha256;
        receipt.targetCount = targets.size();
        receipt.targetDigestSha256 = targetDigest(targets);
        receipt.validate(catalogPath, catalog, targets);
        return receipt;
    }

    static GenerationReceipt loadAndValidate(
            Path directory,
            Path catalogPath,
            StructureCatalog catalog,
            List<Geometry.ChunkCoordinate> targets
    ) throws IOException {
        GenerationReceipt receipt = JsonFiles.read(
                directory.resolve(FILE_NAME), GenerationReceipt.class
        );
        receipt.validate(catalogPath, catalog, targets);
        return receipt;
    }

    private void validate(
            Path catalogPath,
            StructureCatalog catalog,
            List<Geometry.ChunkCoordinate> targets
    ) throws IOException {
        try {
            Instant.parse(completedAt);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException(
                    "Generation receipt completion time is invalid", exception
            );
        }
        if (schemaVersion != 1
                || !RuntimeAttestation.sha256(Files.readAllBytes(catalogPath)).equals(
                        catalogSha256
                )
                || !catalog.worldIdentity.equals(worldIdentity)
                || !catalog.planFingerprint.equals(planFingerprint)
                || !catalog.runtimeAttestationSha256.equals(runtimeAttestationSha256)
                || targetCount != targets.size()
                || !targetDigest(targets).equals(targetDigestSha256)) {
            throw new IllegalArgumentException(
                    "Generation receipt does not match the exact live catalog targets"
            );
        }
    }

    static String targetDigest(List<Geometry.ChunkCoordinate> targets) {
        StringBuilder input = new StringBuilder();
        for (Geometry.ChunkCoordinate target : targets) {
            input.append(target.key()).append('\n');
        }
        return RuntimeAttestation.sha256(
                input.toString().getBytes(StandardCharsets.UTF_8)
        );
    }
}
