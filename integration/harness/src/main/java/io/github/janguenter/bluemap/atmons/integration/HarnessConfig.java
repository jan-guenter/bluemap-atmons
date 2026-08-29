package io.github.janguenter.bluemap.atmons.integration;

import com.google.gson.Gson;
import com.google.gson.JsonParseException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Fail-closed operator configuration for the disposable integration harness. */
public final class HarnessConfig {
    static final String DEFAULT_RESOURCE =
            "/bluemap-atmons/default-integration-harness.json";
    static final String CONFIG_FILE = "integration-harness.json";

    public int schemaVersion;
    public Baseline baseline;
    public int borderBlocks;
    public int locateRadiusPlacementRings;
    public int fallbackLocateRadiusPlacementRings;
    public int customPlacementChunkRadius;
    public int customPlacementCandidateBudget;
    public long customPlacementTimeBudgetMillis;
    public int maxChunksPerStructure;
    public int chunksPerTick;
    public int maxForcedBatchChunks;
    public List<String> dimensionPriority;
    public String catalogFile;
    public String workStateFile;
    public String galleryLayoutFile;
    public String renderMasksFile;
    public String runtimeAttestationFile;
    public String structureMarkerSetId;
    public String galleryMarkerSetId;

    public record Baseline(
            String atmons,
            String minecraft,
            String neoforge,
            String bluemapApi
    ) {
    }

    public static HarnessConfig loadOrCreate(Path directory) throws IOException {
        Files.createDirectories(directory);
        Path configPath = directory.resolve(CONFIG_FILE);
        if (!Files.exists(configPath)) {
            try (InputStream input = HarnessConfig.class.getResourceAsStream(DEFAULT_RESOURCE)) {
                if (input == null) {
                    throw new IOException("Bundled default configuration is missing");
                }
                Files.copy(input, configPath);
            }
        }
        HarnessConfig config = JsonFiles.read(configPath, HarnessConfig.class);
        config.validate();
        return config;
    }

    static HarnessConfig fromReader(Reader reader) {
        try {
            HarnessConfig config = new Gson().fromJson(reader, HarnessConfig.class);
            if (config == null) {
                throw new IllegalArgumentException("Configuration is null");
            }
            config.validate();
            return config;
        } catch (JsonParseException exception) {
            throw new IllegalArgumentException("Malformed configuration JSON", exception);
        }
    }

    static HarnessConfig bundledDefault() throws IOException {
        try (InputStream input = HarnessConfig.class.getResourceAsStream(DEFAULT_RESOURCE)) {
            if (input == null) {
                throw new IOException("Bundled default configuration is missing");
            }
            return fromReader(new InputStreamReader(input, StandardCharsets.UTF_8));
        }
    }

    public void validate() {
        if (schemaVersion != 1) {
            throw new IllegalArgumentException("Unsupported config schemaVersion: " + schemaVersion);
        }
        if (baseline == null
                || !"1.2.0".equals(baseline.atmons())
                || !"1.21.1".equals(baseline.minecraft())
                || !"21.1.248".equals(baseline.neoforge())
                || !"2.8.0".equals(baseline.bluemapApi())) {
            throw new IllegalArgumentException("Configuration baseline is not exact ATMons 1.2.0");
        }
        requireRange("borderBlocks", borderBlocks, 0, 64);
        requireRange("locateRadiusPlacementRings", locateRadiusPlacementRings, 1, 4096);
        requireRange(
                "fallbackLocateRadiusPlacementRings",
                fallbackLocateRadiusPlacementRings,
                locateRadiusPlacementRings,
                4096
        );
        requireRange("customPlacementChunkRadius", customPlacementChunkRadius, 1, 4096);
        requireRange(
                "customPlacementCandidateBudget",
                customPlacementCandidateBudget,
                1,
                10_000_000
        );
        if (customPlacementTimeBudgetMillis < 1L
                || customPlacementTimeBudgetMillis > 300_000L) {
            throw new IllegalArgumentException("customPlacementTimeBudgetMillis is out of range");
        }
        requireRange("maxChunksPerStructure", maxChunksPerStructure, 1, 1_000_000);
        requireRange("chunksPerTick", chunksPerTick, 1, 64);
        requireRange("maxForcedBatchChunks", maxForcedBatchChunks, 1, 256);

        if (dimensionPriority == null || dimensionPriority.isEmpty()) {
            throw new IllegalArgumentException("dimensionPriority must not be empty");
        }
        Set<String> dimensions = new HashSet<>();
        for (String dimension : dimensionPriority) {
            if (!ResourceIds.isValid(dimension) || !dimensions.add(dimension)) {
                throw new IllegalArgumentException("Invalid or duplicate dimension priority: " + dimension);
            }
        }

        validateFileName(catalogFile, "catalogFile");
        validateFileName(workStateFile, "workStateFile");
        validateFileName(galleryLayoutFile, "galleryLayoutFile");
        validateFileName(renderMasksFile, "renderMasksFile");
        validateFileName(runtimeAttestationFile, "runtimeAttestationFile");
        requireIdentifier(structureMarkerSetId, "structureMarkerSetId");
        requireIdentifier(galleryMarkerSetId, "galleryMarkerSetId");
    }

    private static void requireRange(String name, int value, int minimum, int maximum) {
        if (value < minimum || value > maximum) {
            throw new IllegalArgumentException(name + " is out of range");
        }
    }

    private static void validateFileName(String value, String name) {
        if (value == null || value.isBlank()
                || !Path.of(value).getFileName().toString().equals(value)) {
            throw new IllegalArgumentException(name + " must be a plain file name");
        }
    }

    private static void requireIdentifier(String value, String name) {
        if (value == null || !value.matches("[a-z0-9][a-z0-9._-]{0,127}")) {
            throw new IllegalArgumentException(name + " is invalid");
        }
    }
}
