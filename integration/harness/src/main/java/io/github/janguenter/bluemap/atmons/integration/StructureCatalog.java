package io.github.janguenter.bluemap.atmons.integration;

import java.util.ArrayList;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Versioned machine-readable result of one runtime structure catalog. */
public final class StructureCatalog {
    private static final Set<String> LOCATE_FAILURE_STATUSES = Set.of(
            "invalid-start",
            "not-found",
            "custom-not-found",
            "custom-search-budget-exhausted",
            "custom-search-timeout"
    );
    public int schemaVersion = 1;
    public String generatedAt;
    public String worldIdentity;
    public String planFingerprint;
    public String runtimeAttestationSha256;
    public RuntimeInfo runtime;
    public Policy policy;
    public StructureEligibilityEvidence structureEligibilityEvidence;
    public List<DimensionInfo> dimensions = new ArrayList<>();
    public List<StructureEntry> structures = new ArrayList<>();
    public List<String> registeredButUnplaced = new ArrayList<>();
    public List<Failure> failures = new ArrayList<>();
    public Summary summary = new Summary();

    public static final class RuntimeInfo {
        public String atmons;
        public String packCommit;
        public String minecraft;
        public String neoforge;
        public String bluemapApi;
        public String bluemapVersion;
        public String bluemapCommit;
        public String bluemapJarSha256;
    }

    public static final class Policy {
        public String selectionMode = "one-per-structure";
        public String anchor = "overworld-spawn-xz";
        public int searchRadiusPlacementRings;
        public int fallbackRadiusPlacementRings;
        public int customPlacementChunkRadius;
        public int customPlacementCandidateBudget;
        public long customPlacementTimeBudgetMillis;
        public int maxChunksPerStructure;
        public int borderBlocks;
        public List<String> dimensionPriority = new ArrayList<>();
    }

    public record StructureEligibilityEvidence(
            List<StructureConfigRuleEvidence> configRules,
            List<StructureModRuleEvidence> modRules,
            List<DisabledStructureEvidence> disabledStructures
    ) {
    }

    public record StructureConfigRuleEvidence(
            String ruleId,
            String configPath,
            String configSha256,
            List<String> section,
            String key,
            boolean value,
            boolean disabledWhenValue,
            List<String> structures
    ) {
    }

    public record StructureModRuleEvidence(
            String ruleId,
            String modId,
            String version,
            String jarPath,
            long jarSizeBytes,
            String jarSha256,
            List<String> structures
    ) {
    }

    public record DisabledStructureEvidence(
            String structure,
            String evidenceId,
            String reason
    ) {
    }

    public static final class DimensionInfo {
        public String id;
        public String safeMapId;
        public String mapConfigFile;
        public Position anchor;
        public List<String> mapIds = new ArrayList<>();
    }

    public record Position(int x, int y, int z) {
    }

    public static final class StructureEntry {
        public String id;
        public List<String> tags = new ArrayList<>();
        public List<Eligibility> eligibility = new ArrayList<>();
        public Selection selection = Selection.pending();
    }

    public static final class Eligibility {
        public String dimension;
        public List<String> structureSets = new ArrayList<>();
        public List<String> placementTypes = new ArrayList<>();
    }

    public static final class Selection {
        public String status;
        public String reason;
        public String dimension;
        public Position locatePosition;
        public Chunk startChunk;
        public Geometry.BlockBounds structureBounds;
        public Geometry.BlockBounds borderedBounds;
        public Geometry.ChunkBounds chunkBounds;
        public long chunkCount;
        public List<Geometry.RegionCoordinate> regions = new ArrayList<>();
        public String markerId;
        public int searchRadius;
        public long elapsedMillis;

        static Selection pending() {
            Selection selection = new Selection();
            selection.status = "pending";
            selection.reason = "";
            return selection;
        }

        static Selection failure(String status, String reason) {
            Selection selection = pending();
            selection.status = status;
            selection.reason = reason;
            return selection;
        }
    }

    public record Chunk(int x, int z) {
    }

    public record Failure(String structure, String dimension, String status, String detail) {
    }

    public static final class Summary {
        public int registered;
        public int placed;
        public int located;
        public int unlocated;
        public int markers;
        public long uniqueChunks;
        public long uniqueRegions;
    }

    public void validateComplete() {
        if (schemaVersion != 1 || runtime == null || policy == null || summary == null
                || !validInstant(generatedAt)
                || worldIdentity == null
                || !worldIdentity.matches("[0-9a-f-]{36}")
                || planFingerprint == null
                || !planFingerprint.matches("[0-9a-f]{64}")
                || runtimeAttestationSha256 == null
                || !runtimeAttestationSha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("Catalog header is incomplete");
        }
        if (!"1.2.0".equals(runtime.atmons)
                || !"1.21.1".equals(runtime.minecraft)
                || !"21.1.248".equals(runtime.neoforge)
                || !"2.8.0".equals(runtime.bluemapApi)
                || runtime.packCommit == null
                || !runtime.packCommit.matches("[0-9a-f]{40}")
                || runtime.bluemapVersion == null || runtime.bluemapVersion.isBlank()
                || runtime.bluemapCommit == null
                || !runtime.bluemapCommit.matches("[0-9a-f]{40}")
                || runtime.bluemapJarSha256 == null
                || !runtime.bluemapJarSha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("Catalog runtime baseline is not exact");
        }
        StructureEligibilityRules.validateCatalogEvidence(structureEligibilityEvidence);
        Map<String, String> evidenceDisabledReasons =
                StructureEligibilityRules.disabledReasons(structureEligibilityEvidence);
        Set<String> declaredEligibilityTargets = new HashSet<>(
                StructureEligibilityRules.declaredStructures(
                        structureEligibilityEvidence
                )
        );
        if (structures == null || dimensions == null || failures == null) {
            throw new IllegalArgumentException("Catalog collections are missing");
        }
        if (structures.isEmpty() || dimensions.isEmpty() || registeredButUnplaced == null
                || !"one-per-structure".equals(policy.selectionMode)
                || !"overworld-spawn-xz".equals(policy.anchor)
                || policy.maxChunksPerStructure < 1
                || policy.borderBlocks < 0
                || policy.dimensionPriority == null
                || policy.dimensionPriority.isEmpty()) {
            throw new IllegalArgumentException("Catalog plan is empty or its policy is invalid");
        }
        Set<String> dimensionIds = new HashSet<>();
        for (DimensionInfo dimension : dimensions) {
            if (dimension == null
                    || !ResourceIds.isValid(dimension.id)
                    || !BlueMapMapContract.safeMapId(dimension.id).equals(
                            dimension.safeMapId
                    )
                    || !BlueMapMapContract.configFile(dimension.id).equals(
                            dimension.mapConfigFile
                    )
                    || dimension.anchor == null
                    || dimension.mapIds == null
                    || dimension.mapIds.stream().anyMatch(
                            map -> map == null || map.isBlank()
                    )
                    || dimension.mapIds.size() != new HashSet<>(dimension.mapIds).size()
                    || !dimensionIds.add(dimension.id)) {
                throw new IllegalArgumentException("Catalog has an invalid dimension");
            }
        }
        int located = 0;
        int placed = 0;
        Set<String> structureIds = new HashSet<>();
        Set<String> registryOnly = new HashSet<>();
        Set<String> uniqueChunks = new HashSet<>();
        Set<String> uniqueRegions = new HashSet<>();
        Map<String, List<String>> expectedFailedDimensions = new TreeMap<>();
        for (StructureEntry entry : structures) {
            if (entry == null || entry.id == null || entry.id.isBlank()
                    || entry.tags == null || entry.eligibility == null
                    || entry.selection == null || entry.selection.status == null
                    || "pending".equals(entry.selection.status)
                    || !structureIds.add(entry.id)) {
                throw new IllegalArgumentException("Catalog contains an incomplete structure entry");
            }
            Set<String> eligibleDimensions = new HashSet<>();
            for (Eligibility eligibility : entry.eligibility) {
                if (eligibility == null
                        || !dimensionIds.contains(eligibility.dimension)
                        || eligibility.structureSets == null
                        || eligibility.structureSets.isEmpty()
                        || eligibility.placementTypes == null
                        || eligibility.placementTypes.isEmpty()
                        || !eligibleDimensions.add(eligibility.dimension)) {
                    throw new IllegalArgumentException(
                            "Catalog contains invalid eligibility: " + entry.id
                    );
                }
            }
            if (!entry.eligibility.isEmpty()) {
                placed++;
            }
            if ("located".equals(entry.selection.status)) {
                Selection selection = entry.selection;
                if (!eligibleDimensions.contains(selection.dimension)
                        || selection.locatePosition == null
                        || selection.startChunk == null
                        || selection.structureBounds == null
                        || selection.borderedBounds == null
                        || selection.chunkBounds == null
                        || selection.markerId == null
                        || selection.regions == null
                        || selection.searchRadius < 0
                        || selection.elapsedMillis < 0) {
                    throw new IllegalArgumentException(
                            "Catalog contains an incomplete located selection: " + entry.id
                    );
                }
                validateLocatedDerivations(entry.id, selection, policy, uniqueChunks, uniqueRegions);
                int selectedIndex = eligibleDimensionIndex(
                        entry.eligibility, selection.dimension
                );
                expectedFailedDimensions.put(
                        entry.id,
                        entry.eligibility.subList(0, selectedIndex).stream()
                                .map(eligibility -> eligibility.dimension)
                                .toList()
                );
                located++;
            } else {
                if (entry.selection.status.isBlank()
                        || entry.selection.reason == null
                        || entry.selection.reason.isBlank()) {
                    throw new IllegalArgumentException(
                            "Catalog contains an invalid unlocated selection: " + entry.id
                    );
                }
                if (entry.eligibility.isEmpty()) {
                    if (!"registry-only".equals(entry.selection.status)) {
                        throw new IllegalArgumentException(
                                "Ineligible structure is not registry-only: " + entry.id
                        );
                    }
                    registryOnly.add(entry.id);
                    expectedFailedDimensions.put(entry.id, List.of());
                } else {
                    throw new IllegalArgumentException(
                            "Eligible structure was not located: " + entry.id
                    );
                }
            }
            String evidenceDisabledReason = evidenceDisabledReasons.get(entry.id);
            if (evidenceDisabledReason != null) {
                if (!entry.eligibility.isEmpty()
                        || !"registry-only".equals(entry.selection.status)
                        || !evidenceDisabledReason.equals(entry.selection.reason)) {
                    throw new IllegalArgumentException(
                            "Evidence-disabled structure is not exact registry-only: "
                                    + entry.id
                    );
                }
            } else if (declaredEligibilityTargets.contains(entry.id)
                    && entry.eligibility.isEmpty()) {
                throw new IllegalArgumentException(
                        "Eligibility-rule target lacks live placement: " + entry.id
                );
            }
        }
        if (!structureIds.containsAll(declaredEligibilityTargets)) {
            Set<String> missing = new HashSet<>(declaredEligibilityTargets);
            missing.removeAll(structureIds);
            throw new IllegalArgumentException(
                    "Catalog lacks exact structure eligibility targets: " + missing
            );
        }
        Set<String> recordedRegistryOnly = new HashSet<>(registeredButUnplaced);
        if (recordedRegistryOnly.size() != registeredButUnplaced.size()
                || !recordedRegistryOnly.equals(registryOnly)) {
            throw new IllegalArgumentException(
                    "Catalog registry-only list does not match its structures"
            );
        }
        Map<String, List<String>> actualFailedDimensions = new TreeMap<>();
        Set<String> uniqueFailures = new HashSet<>();
        for (Failure failure : failures) {
            if (failure == null || !structureIds.contains(failure.structure())
                    || !dimensionIds.contains(failure.dimension())
                    || !LOCATE_FAILURE_STATUSES.contains(failure.status())
                    || failure.detail() == null || failure.detail().isBlank()) {
                throw new IllegalArgumentException("Catalog contains an invalid locate failure");
            }
            String key = failure.structure() + "\u0000" + failure.dimension();
            if (!uniqueFailures.add(key)) {
                throw new IllegalArgumentException("Catalog contains duplicate locate failures");
            }
            actualFailedDimensions.computeIfAbsent(
                    failure.structure(), ignored -> new ArrayList<>()
            ).add(failure.dimension());
        }
        for (String structureId : structureIds) {
            if (!expectedFailedDimensions.getOrDefault(structureId, List.of()).equals(
                    actualFailedDimensions.getOrDefault(structureId, List.of())
            )) {
                throw new IllegalArgumentException(
                        "Catalog locate failures do not match attempted dimensions: "
                                + structureId
                );
            }
        }
        if (summary.registered < 1 || summary.registered > structures.size()
                || summary.placed != placed
                || summary.located != located
                || summary.unlocated != structures.size() - located
                || summary.markers != located
                || summary.uniqueChunks != uniqueChunks.size()
                || summary.uniqueRegions != uniqueRegions.size()) {
            throw new IllegalArgumentException("Catalog summary does not match its structures");
        }
    }

    private static int eligibleDimensionIndex(
            List<Eligibility> eligibility,
            String selectedDimension
    ) {
        for (int index = 0; index < eligibility.size(); index++) {
            if (eligibility.get(index).dimension.equals(selectedDimension)) {
                return index;
            }
        }
        throw new IllegalArgumentException(
                "Located selection is outside the eligible dimension order"
        );
    }

    private static void validateLocatedDerivations(
            String structureId,
            Selection selection,
            Policy policy,
            Set<String> uniqueChunks,
            Set<String> uniqueRegions
    ) {
        Geometry.BlockBounds source = selection.structureBounds;
        Geometry.BlockBounds bordered = selection.borderedBounds;
        int border = policy.borderBlocks;
        if (bordered.minX() != Math.subtractExact(source.minX(), border)
                || bordered.minZ() != Math.subtractExact(source.minZ(), border)
                || bordered.maxX() != Math.addExact(source.maxX(), border)
                || bordered.maxZ() != Math.addExact(source.maxZ(), border)
                || bordered.minY() > source.minY()
                || bordered.maxY() < source.maxY()
                || (long) source.minY() - bordered.minY() > border
                || (long) bordered.maxY() - source.maxY() > border) {
            throw new IllegalArgumentException(
                    "Catalog border derivation is invalid: " + structureId
            );
        }
        Geometry.ChunkBounds expectedChunks = bordered.chunks();
        long expectedCount = expectedChunks.count();
        if (!expectedChunks.equals(selection.chunkBounds)
                || selection.chunkCount != expectedCount
                || expectedCount < 1
                || expectedCount > policy.maxChunksPerStructure) {
            throw new IllegalArgumentException(
                    "Catalog chunk derivation is invalid or oversized: " + structureId
            );
        }
        Set<Geometry.RegionCoordinate> expectedRegions = expectedChunks.regions();
        Set<Geometry.RegionCoordinate> actualRegions = new HashSet<>(selection.regions);
        if (actualRegions.size() != selection.regions.size()
                || !actualRegions.equals(expectedRegions)
                || !markerId(structureId).equals(selection.markerId)) {
            throw new IllegalArgumentException(
                    "Catalog region/marker derivation is invalid: " + structureId
            );
        }
        for (Geometry.ChunkCoordinate chunk : expectedChunks.coordinates(selection.dimension)) {
            uniqueChunks.add(chunk.key());
        }
        for (Geometry.RegionCoordinate region : expectedRegions) {
            uniqueRegions.add(selection.dimension + ":" + region.x() + ":" + region.z());
        }
    }

    private static boolean validInstant(String value) {
        try {
            Instant.parse(value);
            return true;
        } catch (RuntimeException exception) {
            return false;
        }
    }

    private static String markerId(String structureId) {
        return structureId.toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9._-]", "_");
    }
}
