package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class StructureCatalogTest {
    @Test
    void validatesCompleteLocatedCatalogAndRoundTrip() {
        StructureCatalog catalog = completeCatalog();
        String json = JsonFiles.GSON.toJson(catalog);
        StructureCatalog restored = JsonFiles.GSON.fromJson(
                json, StructureCatalog.class
        );

        assertDoesNotThrow(restored::validateComplete);
    }

    @Test
    void rejectsPendingEntryAndSummaryDrift() {
        StructureCatalog pending = completeCatalog();
        pending.structures.getFirst().selection = StructureCatalog.Selection.pending();
        assertThrows(IllegalArgumentException.class, pending::validateComplete);

        StructureCatalog drift = completeCatalog();
        drift.summary.located = 0;
        assertThrows(IllegalArgumentException.class, drift::validateComplete);
    }

    @Test
    void rejectsEmptyOversizedAndTamperedDerivations() {
        StructureCatalog empty = completeCatalog();
        empty.structures.clear();
        empty.registeredButUnplaced.clear();
        empty.summary.registered = 0;
        empty.summary.placed = 0;
        empty.summary.located = 0;
        empty.summary.unlocated = 0;
        empty.summary.markers = 0;
        empty.summary.uniqueChunks = 0;
        empty.summary.uniqueRegions = 0;
        assertThrows(IllegalArgumentException.class, empty::validateComplete);

        StructureCatalog oversized = completeCatalog();
        oversized.policy.maxChunksPerStructure = 15;
        assertThrows(IllegalArgumentException.class, oversized::validateComplete);

        StructureCatalog border = completeCatalog();
        border.structures.getFirst().selection.borderedBounds =
                new Geometry.BlockBounds(-3, 56, -4, 35, 84, 35);
        assertThrows(IllegalArgumentException.class, border::validateComplete);

        StructureCatalog regions = completeCatalog();
        regions.structures.getFirst().selection.regions = List.of(
                new Geometry.RegionCoordinate(0, 0)
        );
        assertThrows(IllegalArgumentException.class, regions::validateComplete);
    }

    @Test
    void rejectsEligibleSkippedSelectionAndForgedFailureCoverage() {
        StructureCatalog skipped = completeCatalog();
        skipped.structures.getFirst().selection = StructureCatalog.Selection.failure(
                "skipped", "fabricated"
        );
        skipped.summary.located = 2;
        skipped.summary.unlocated = 2;
        skipped.summary.markers = 2;
        assertThrows(IllegalArgumentException.class, skipped::validateComplete);

        StructureCatalog forgedFailure = completeCatalog();
        forgedFailure.failures.add(new StructureCatalog.Failure(
                StructureEligibilityRules.BETTER_DUNGEONS.structures().getFirst(),
                "minecraft:overworld",
                "not-found",
                "fabricated"
        ));
        assertThrows(IllegalArgumentException.class, forgedFailure::validateComplete);

        StructureCatalog inventedStatus = completeCatalog();
        inventedStatus.failures.add(new StructureCatalog.Failure(
                StructureEligibilityRules.BETTER_DUNGEONS.structures().getFirst(),
                "minecraft:overworld",
                "skipped",
                "fabricated"
        ));
        assertThrows(IllegalArgumentException.class, inventedStatus::validateComplete);
    }

    @Test
    void acceptsOnlyDisabledStructuresAndReasonsDerivedFromExactEvidence() {
        StructureCatalog disabled = completeCatalog();
        disabled.structureEligibilityEvidence = exactEvidence(false, true);
        Map<String, String> reasons = StructureEligibilityRules.disabledReasons(
                disabled.structureEligibilityEvidence
        );
        disabled.registeredButUnplaced.clear();
        for (StructureCatalog.StructureEntry structure : disabled.structures) {
            structure.eligibility.clear();
            structure.selection = StructureCatalog.Selection.failure(
                    "registry-only",
                    reasons.get(structure.id)
            );
            disabled.registeredButUnplaced.add(structure.id);
        }
        disabled.summary.placed = 0;
        disabled.summary.located = 0;
        disabled.summary.unlocated = 4;
        disabled.summary.markers = 0;
        disabled.summary.uniqueChunks = 0;
        disabled.summary.uniqueRegions = 0;

        assertDoesNotThrow(disabled::validateComplete);

        StructureCatalog enabledForgery = cloneCatalog(disabled);
        enabledForgery.structureEligibilityEvidence = exactEvidence(true, false);
        assertThrows(IllegalArgumentException.class, enabledForgery::validateComplete);

        StructureCatalog wrongReason = cloneCatalog(disabled);
        wrongReason.structures.getFirst().selection.reason = "Disabled somewhere else";
        assertThrows(IllegalArgumentException.class, wrongReason::validateComplete);

        StructureCatalog wrongMod = completeCatalog();
        StructureCatalog.StructureEligibilityEvidence valid =
                wrongMod.structureEligibilityEvidence;
        StructureCatalog.StructureModRuleEvidence mod = valid.modRules().getFirst();
        wrongMod.structureEligibilityEvidence =
                StructureEligibilityRules.assembleEvidence(
                        valid.configRules(),
                        List.of(new StructureCatalog.StructureModRuleEvidence(
                                mod.ruleId(),
                                mod.modId(),
                                mod.version(),
                                mod.jarPath(),
                                mod.jarSizeBytes(),
                                "a".repeat(64),
                                mod.structures()
                        ))
                );
        assertThrows(IllegalArgumentException.class, wrongMod::validateComplete);
    }

    @Test
    void rejectsMissingDeclaredEligibilityTarget() {
        StructureCatalog missing = completeCatalog();
        missing.structures.remove(1);
        missing.summary.registered = 3;
        missing.summary.placed = 2;
        missing.summary.located = 2;

        assertThrows(IllegalArgumentException.class, missing::validateComplete);
    }

    private static StructureCatalog completeCatalog() {
        StructureCatalog catalog = new StructureCatalog();
        catalog.generatedAt = "2026-08-28T00:00:00Z";
        catalog.worldIdentity = "123e4567-e89b-12d3-a456-426614174000";
        catalog.planFingerprint = "a".repeat(64);
        catalog.runtimeAttestationSha256 = "b".repeat(64);
        catalog.structureEligibilityEvidence = exactEvidence(true, false);
        catalog.runtime = new StructureCatalog.RuntimeInfo();
        catalog.runtime.atmons = "1.2.0";
        catalog.runtime.packCommit = "c7bb230f21d14d26859d0b92548f089b3a493ad9";
        catalog.runtime.minecraft = "1.21.1";
        catalog.runtime.neoforge = "21.1.248";
        catalog.runtime.bluemapApi = "2.8.0";
        catalog.runtime.bluemapVersion = "candidate";
        catalog.runtime.bluemapCommit = "c".repeat(40);
        catalog.runtime.bluemapJarSha256 = "d".repeat(64);
        catalog.policy = new StructureCatalog.Policy();
        catalog.policy.searchRadiusPlacementRings = 100;
        catalog.policy.fallbackRadiusPlacementRings = 2048;
        catalog.policy.customPlacementChunkRadius = 128;
        catalog.policy.customPlacementCandidateBudget = 100_000;
        catalog.policy.customPlacementTimeBudgetMillis = 10_000L;
        catalog.policy.maxChunksPerStructure = 100;
        catalog.policy.borderBlocks = 4;
        catalog.policy.dimensionPriority = List.of("minecraft:overworld");

        StructureCatalog.DimensionInfo dimension = new StructureCatalog.DimensionInfo();
        dimension.id = "minecraft:overworld";
        dimension.safeMapId = BlueMapMapContract.safeMapId(dimension.id);
        dimension.mapConfigFile = BlueMapMapContract.configFile(dimension.id);
        dimension.anchor = new StructureCatalog.Position(0, 64, 0);
        catalog.dimensions.add(dimension);

        List<String> located = List.of(
                StructureEligibilityRules.BETTER_DUNGEONS.structures().getFirst(),
                StructureEligibilityRules.BETTER_MINESHAFTS.structures().get(0),
                StructureEligibilityRules.BETTER_MINESHAFTS.structures().get(1)
        );
        for (String structureId : located) {
            catalog.structures.add(locatedStructure(structureId, dimension.id));
        }

        String stronghold = StructureEligibilityRules.BETTER_STRONGHOLDS
                .structures().getFirst();
        StructureCatalog.StructureEntry disabled = new StructureCatalog.StructureEntry();
        disabled.id = stronghold;
        disabled.selection = StructureCatalog.Selection.failure(
                "registry-only",
                StructureEligibilityRules.disabledReasons(
                        catalog.structureEligibilityEvidence
                ).get(stronghold)
        );
        catalog.structures.add(disabled);
        catalog.registeredButUnplaced.add(stronghold);

        catalog.summary.registered = 4;
        catalog.summary.placed = 3;
        catalog.summary.located = 3;
        catalog.summary.unlocated = 1;
        catalog.summary.markers = 3;
        catalog.summary.uniqueChunks = 16;
        catalog.summary.uniqueRegions = 4;
        return catalog;
    }

    private static StructureCatalog.StructureEntry locatedStructure(
            String structureId,
            String dimensionId
    ) {
        StructureCatalog.StructureEntry structure = new StructureCatalog.StructureEntry();
        structure.id = structureId;
        StructureCatalog.Eligibility eligibility = new StructureCatalog.Eligibility();
        eligibility.dimension = dimensionId;
        eligibility.structureSets = List.of("minecraft:test_set");
        eligibility.placementTypes = List.of("minecraft:random_spread");
        structure.eligibility.add(eligibility);

        StructureCatalog.Selection selection = StructureCatalog.Selection.pending();
        selection.status = "located";
        selection.dimension = dimensionId;
        selection.locatePosition = new StructureCatalog.Position(0, 64, 0);
        selection.startChunk = new StructureCatalog.Chunk(0, 0);
        selection.structureBounds = new Geometry.BlockBounds(0, 60, 0, 31, 80, 31);
        selection.borderedBounds = new Geometry.BlockBounds(-4, 56, -4, 35, 84, 35);
        selection.chunkBounds = new Geometry.ChunkBounds(-1, -1, 2, 2);
        selection.chunkCount = 16;
        selection.regions = List.of(
                new Geometry.RegionCoordinate(-1, -1),
                new Geometry.RegionCoordinate(-1, 0),
                new Geometry.RegionCoordinate(0, -1),
                new Geometry.RegionCoordinate(0, 0)
        );
        selection.markerId = structureId.replace(':', '_');
        structure.selection = selection;
        return structure;
    }

    private static StructureCatalog.StructureEligibilityEvidence exactEvidence(
            boolean betterDungeonsEnabled,
            boolean disableVanillaMineshafts
    ) {
        List<StructureCatalog.StructureConfigRuleEvidence> configs = List.of(
                configEvidence(
                        StructureEligibilityRules.BETTER_DUNGEONS,
                        betterDungeonsEnabled,
                        "e".repeat(64)
                ),
                configEvidence(
                        StructureEligibilityRules.BETTER_MINESHAFTS,
                        disableVanillaMineshafts,
                        "f".repeat(64)
                )
        );
        StructureEligibilityRules.ModRuleSpec rule =
                StructureEligibilityRules.BETTER_STRONGHOLDS;
        List<StructureCatalog.StructureModRuleEvidence> mods = List.of(
                new StructureCatalog.StructureModRuleEvidence(
                        rule.ruleId(),
                        rule.modId(),
                        rule.version(),
                        rule.jarPath(),
                        rule.jarSizeBytes(),
                        rule.jarSha256(),
                        rule.structures()
                )
        );
        return StructureEligibilityRules.assembleEvidence(configs, mods);
    }

    private static StructureCatalog.StructureConfigRuleEvidence configEvidence(
            StructureEligibilityRules.ConfigRuleSpec rule,
            boolean value,
            String sha256
    ) {
        return new StructureCatalog.StructureConfigRuleEvidence(
                rule.ruleId(),
                StructureEligibilityRules.EXPECTED_CONFIG_DIRECTORY
                        .resolve(rule.fileName())
                        .toString(),
                sha256,
                rule.section(),
                rule.key(),
                value,
                rule.disabledWhenValue(),
                rule.structures()
        );
    }

    private static StructureCatalog cloneCatalog(StructureCatalog catalog) {
        return JsonFiles.GSON.fromJson(
                JsonFiles.GSON.toJson(catalog),
                StructureCatalog.class
        );
    }
}
