package io.github.janguenter.bluemap.atmons.integration;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.JsonOps;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.Registry;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.placement.ConcentricRingsStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacement;
import net.minecraft.world.level.storage.LevelResource;

/** Live-registry structure discovery and authoritative generated-start inspection. */
final class StructureCatalogService {
    private static final String WORLD_ID_FILE = ".bluemap-atmons-integration-world-id";
    private final MinecraftServer server;
    private final HarnessConfig config;
    private final CatalogPlan plan;
    private final RuntimeAttestation.Loaded runtimeAttestation;

    StructureCatalogService(
            MinecraftServer server, HarnessConfig config, java.nio.file.Path directory
    ) {
        this.server = server;
        this.config = config;
        this.runtimeAttestation = loadRuntimeAttestation(
                directory.resolve(config.runtimeAttestationFile)
        );
        this.plan = buildPlan(
                server,
                config,
                runtimeAttestation.sha256(),
                StructureEligibilityRules.loadCanonical()
        );
    }

    CatalogPlan plan() {
        return plan;
    }

    StructureCatalog createCatalog() {
        StructureCatalog catalog = new StructureCatalog();
        catalog.generatedAt = Instant.now().toString();
        catalog.worldIdentity = plan.worldIdentity();
        catalog.planFingerprint = plan.fingerprint();
        catalog.runtimeAttestationSha256 = runtimeAttestation.sha256();
        catalog.structureEligibilityEvidence = plan.structureEligibilityEvidence();
        catalog.runtime = new StructureCatalog.RuntimeInfo();
        RuntimeAttestation attestation = runtimeAttestation.value();
        catalog.runtime.atmons = attestation.atmons;
        catalog.runtime.packCommit = attestation.packCommit;
        catalog.runtime.minecraft = attestation.minecraft;
        catalog.runtime.neoforge = attestation.neoforge;
        catalog.runtime.bluemapApi = config.baseline.bluemapApi();
        catalog.runtime.bluemapVersion = attestation.bluemapVersion;
        catalog.runtime.bluemapCommit = attestation.bluemapCommit;
        catalog.runtime.bluemapJarSha256 = attestation.bluemapJarSha256;
        catalog.policy = new StructureCatalog.Policy();
        catalog.policy.searchRadiusPlacementRings = config.locateRadiusPlacementRings;
        catalog.policy.fallbackRadiusPlacementRings = config.fallbackLocateRadiusPlacementRings;
        catalog.policy.customPlacementChunkRadius = config.customPlacementChunkRadius;
        catalog.policy.customPlacementCandidateBudget = config.customPlacementCandidateBudget;
        catalog.policy.customPlacementTimeBudgetMillis = config.customPlacementTimeBudgetMillis;
        catalog.policy.maxChunksPerStructure = config.maxChunksPerStructure;
        catalog.policy.borderBlocks = config.borderBlocks;
        catalog.policy.dimensionPriority = List.copyOf(config.dimensionPriority);

        for (DimensionPlan dimension : plan.dimensions()) {
            StructureCatalog.DimensionInfo info = new StructureCatalog.DimensionInfo();
            info.id = dimension.id();
            info.safeMapId = BlueMapMapContract.safeMapId(dimension.id());
            info.mapConfigFile = BlueMapMapContract.configFile(dimension.id());
            BlockPos anchor = anchor(dimension.level());
            info.anchor = new StructureCatalog.Position(anchor.getX(), anchor.getY(), anchor.getZ());
            catalog.dimensions.add(info);
        }

        for (PlannedStructure structure : plan.structures()) {
            StructureCatalog.StructureEntry entry = new StructureCatalog.StructureEntry();
            entry.id = structure.id();
            entry.tags = structure.tags();
            for (EligibilityPlan eligibility : structure.eligibility()) {
                StructureCatalog.Eligibility output = new StructureCatalog.Eligibility();
                output.dimension = eligibility.dimension().id();
                output.structureSets = eligibility.structureSets();
                output.placementTypes = eligibility.placementTypes();
                entry.eligibility.add(output);
            }
            catalog.structures.add(entry);
        }
        catalog.summary.registered = plan.registeredCount();
        catalog.summary.placed = (int) plan.structures().stream()
                .filter(structure -> !structure.eligibility().isEmpty())
                .count();
        return catalog;
    }

    void validateLiveCatalog(StructureCatalog catalog) {
        catalog.validateComplete();
        if (!plan.worldIdentity().equals(catalog.worldIdentity)) {
            throw new IllegalArgumentException(
                    "Structure catalog belongs to a different world identity"
            );
        }
        if (!plan.fingerprint().equals(catalog.planFingerprint)) {
            throw new IllegalArgumentException(
                    "Structure catalog does not match the live world/config/placement plan"
            );
        }
        if (!runtimeAttestation.sha256().equals(catalog.runtimeAttestationSha256)) {
            throw new IllegalArgumentException(
                    "Structure catalog runtime attestation has changed"
            );
        }
        RuntimeAttestation expected = runtimeAttestation.value();
        if (!expected.atmons.equals(catalog.runtime.atmons)
                || !expected.packCommit.equals(catalog.runtime.packCommit)
                || !expected.minecraft.equals(catalog.runtime.minecraft)
                || !expected.neoforge.equals(catalog.runtime.neoforge)
                || !expected.bluemapVersion.equals(catalog.runtime.bluemapVersion)
                || !expected.bluemapCommit.equals(catalog.runtime.bluemapCommit)
                || !expected.bluemapJarSha256.equals(catalog.runtime.bluemapJarSha256)) {
            throw new IllegalArgumentException(
                    "Structure catalog runtime fields do not match its attestation"
            );
        }
        StructureCatalog.StructureEligibilityEvidence liveEvidence =
                StructureEligibilityRules.loadCanonical();
        if (!Objects.equals(
                catalog.structureEligibilityEvidence,
                liveEvidence
        )) {
            throw new IllegalArgumentException(
                    "Structure catalog eligibility evidence does not match the live runtime"
            );
        }
        StructureCatalog live = createCatalog();
        validatePolicy(catalog.policy, live.policy);
        if (catalog.summary.registered != live.summary.registered
                || catalog.summary.placed != live.summary.placed) {
            throw new IllegalArgumentException(
                    "Structure catalog registry summary does not match the live plan"
            );
        }
        if (catalog.dimensions.size() != live.dimensions.size()) {
            throw new IllegalArgumentException(
                    "Structure catalog dimension count does not match the live plan"
            );
        }
        for (int index = 0; index < live.dimensions.size(); index++) {
            StructureCatalog.DimensionInfo actual = catalog.dimensions.get(index);
            StructureCatalog.DimensionInfo planned = live.dimensions.get(index);
            if (!Objects.equals(actual.id, planned.id)
                    || !Objects.equals(actual.safeMapId, planned.safeMapId)
                    || !Objects.equals(actual.mapConfigFile, planned.mapConfigFile)
                    || !Objects.equals(actual.anchor, planned.anchor)) {
                throw new IllegalArgumentException(
                        "Structure catalog dimension plan differs at index " + index
                );
            }
        }
        if (catalog.structures.size() != live.structures.size()) {
            throw new IllegalArgumentException(
                    "Structure catalog structure count does not match the live registry"
            );
        }
        Map<String, DimensionPlan> liveDimensions = plan.dimensions().stream()
                .collect(Collectors.toMap(DimensionPlan::id, dimension -> dimension));
        for (int index = 0; index < live.structures.size(); index++) {
            StructureCatalog.StructureEntry actual = catalog.structures.get(index);
            StructureCatalog.StructureEntry planned = live.structures.get(index);
            PlannedStructure liveStructure = plan.structures().get(index);
            if (!Objects.equals(actual.id, planned.id)
                    || !Objects.equals(actual.tags, planned.tags)
                    || !sameEligibility(actual.eligibility, planned.eligibility)) {
                throw new IllegalArgumentException(
                        "Structure catalog registry plan differs at index " + index
                );
            }
            if ("located".equals(actual.selection.status)) {
                DimensionPlan dimension = liveDimensions.get(actual.selection.dimension);
                if (dimension == null) {
                    throw new IllegalArgumentException(
                            "Located structure refers to a non-live dimension: " + actual.id
                    );
                }
                ServerLevel level = dimension.level();
                Geometry.BlockBounds expectedBorder = actual.selection.structureBounds.inflate(
                        config.borderBlocks,
                        level.getMinBuildHeight(),
                        level.getMaxBuildHeight() - 1
                );
                if (!expectedBorder.equals(actual.selection.borderedBounds)
                        || actual.selection.chunkCount > config.maxChunksPerStructure) {
                    throw new IllegalArgumentException(
                            "Located structure has stale border/chunk policy: " + actual.id
                    );
                }
                ChunkAccess startChunk = level.getChunk(
                        actual.selection.startChunk.x(),
                        actual.selection.startChunk.z(),
                        ChunkStatus.STRUCTURE_STARTS,
                        true
                );
                StructureStart start = level.structureManager().getStartForStructure(
                        SectionPos.bottomOf(startChunk),
                        liveStructure.holder().value(),
                        startChunk
                );
                if (start == null || !start.isValid()
                        || start.getChunkPos().x != actual.selection.startChunk.x()
                        || start.getChunkPos().z != actual.selection.startChunk.z()) {
                    throw new IllegalArgumentException(
                            "Located structure start is absent or changed: " + actual.id
                    );
                }
                var box = start.getBoundingBox();
                Geometry.BlockBounds liveBounds = new Geometry.BlockBounds(
                        box.minX(), box.minY(), box.minZ(),
                        box.maxX(), box.maxY(), box.maxZ()
                ).clampY(
                        level.getMinBuildHeight(),
                        level.getMaxBuildHeight() - 1
                );
                if (!liveBounds.equals(actual.selection.structureBounds)) {
                    throw new IllegalArgumentException(
                            "Located structure bounding box has changed: " + actual.id
                    );
                }
                BlockPos recordedLocate = new BlockPos(
                        actual.selection.locatePosition.x(),
                        actual.selection.locatePosition.y(),
                        actual.selection.locatePosition.z()
                );
                boolean locateMatches = level.getChunkSource().getGeneratorState()
                        .getPlacementsForStructure(liveStructure.holder())
                        .stream()
                        .map(placement -> placement.getLocatePos(start.getChunkPos()))
                        .anyMatch(recordedLocate::equals);
                if (!locateMatches) {
                    throw new IllegalArgumentException(
                            "Located structure position no longer matches its placement: "
                                    + actual.id
                    );
                }
            }
        }
    }

    private static void validatePolicy(
            StructureCatalog.Policy actual, StructureCatalog.Policy expected
    ) {
        if (!Objects.equals(actual.selectionMode, expected.selectionMode)
                || !Objects.equals(actual.anchor, expected.anchor)
                || actual.searchRadiusPlacementRings != expected.searchRadiusPlacementRings
                || actual.fallbackRadiusPlacementRings
                        != expected.fallbackRadiusPlacementRings
                || actual.customPlacementChunkRadius != expected.customPlacementChunkRadius
                || actual.customPlacementCandidateBudget
                        != expected.customPlacementCandidateBudget
                || actual.customPlacementTimeBudgetMillis
                        != expected.customPlacementTimeBudgetMillis
                || actual.maxChunksPerStructure != expected.maxChunksPerStructure
                || actual.borderBlocks != expected.borderBlocks
                || !Objects.equals(actual.dimensionPriority, expected.dimensionPriority)) {
            throw new IllegalArgumentException(
                    "Structure catalog policy does not match the live configuration"
            );
        }
    }

    private static boolean sameEligibility(
            List<StructureCatalog.Eligibility> actual,
            List<StructureCatalog.Eligibility> expected
    ) {
        if (actual.size() != expected.size()) {
            return false;
        }
        for (int index = 0; index < actual.size(); index++) {
            StructureCatalog.Eligibility left = actual.get(index);
            StructureCatalog.Eligibility right = expected.get(index);
            if (!Objects.equals(left.dimension, right.dimension)
                    || !Objects.equals(left.structureSets, right.structureSets)
                    || !Objects.equals(left.placementTypes, right.placementTypes)) {
                return false;
            }
        }
        return true;
    }

    private static RuntimeAttestation.Loaded loadRuntimeAttestation(
            java.nio.file.Path path
    ) {
        try {
            return RuntimeAttestation.load(path);
        } catch (IOException | IllegalArgumentException exception) {
            throw new IllegalStateException(
                    "Could not validate runtime attestation " + path, exception
            );
        }
    }

    void processEntry(StructureCatalog catalog, int index) {
        PlannedStructure structure = plan.structures().get(index);
        StructureCatalog.StructureEntry output = catalog.structures.get(index);
        long started = System.nanoTime();

        // A crash can persist the catalog before its cursor file. Clear this
        // entry's append-only outputs so replaying the same cursor is harmless.
        catalog.registeredButUnplaced.removeIf(structure.id()::equals);
        catalog.failures.removeIf(failure -> structure.id().equals(failure.structure()));
        output.selection = StructureCatalog.Selection.pending();

        if (structure.eligibility().isEmpty()) {
            String reason = plan.disabledReasons().getOrDefault(
                    structure.id(),
                    "No enabled structure placement is eligible in a loaded dimension"
            );
            output.selection = StructureCatalog.Selection.failure(
                    "registry-only",
                    reason
            );
            catalog.registeredButUnplaced.add(structure.id());
            return;
        }

        List<String> attempts = new ArrayList<>();
        for (EligibilityPlan eligibility : structure.eligibility()) {
            LocateOutcome outcome = locate(structure, eligibility);
            if (outcome.candidate() != null) {
                output.selection = toSelection(
                        structure.id(),
                        eligibility.dimension(),
                        outcome,
                        Duration.ofNanos(System.nanoTime() - started).toMillis()
                );
                return;
            }
            attempts.add(eligibility.dimension().id() + "=" + outcome.status()
                    + "(" + outcome.reason() + ")");
            catalog.failures.add(new StructureCatalog.Failure(
                    structure.id(),
                    eligibility.dimension().id(),
                    outcome.status(),
                    outcome.reason()
            ));
        }

        output.selection = StructureCatalog.Selection.failure(
                "not-found",
                String.join("; ", attempts)
        );
        output.selection.elapsedMillis = Duration.ofNanos(
                System.nanoTime() - started
        ).toMillis();
    }

    void finalizeSummary(StructureCatalog catalog) {
        Set<String> chunks = new LinkedHashSet<>();
        Set<String> regions = new LinkedHashSet<>();
        int located = 0;
        for (StructureCatalog.StructureEntry entry : catalog.structures) {
            StructureCatalog.Selection selection = entry.selection;
            if (!"located".equals(selection.status)) {
                continue;
            }
            located++;
            for (Geometry.ChunkCoordinate chunk
                    : selection.chunkBounds.coordinates(selection.dimension)) {
                chunks.add(chunk.key());
            }
            for (Geometry.RegionCoordinate region : selection.regions) {
                regions.add(selection.dimension + ":" + region.x() + ":" + region.z());
            }
        }
        catalog.summary.located = located;
        catalog.summary.unlocated = catalog.structures.size() - located;
        catalog.summary.markers = located;
        catalog.summary.uniqueChunks = chunks.size();
        catalog.summary.uniqueRegions = regions.size();
        catalog.generatedAt = Instant.now().toString();
    }

    List<Geometry.ChunkCoordinate> generationTargets(StructureCatalog catalog) {
        Map<String, Geometry.ChunkCoordinate> targets = new TreeMap<>();
        for (StructureCatalog.StructureEntry entry : catalog.structures) {
            StructureCatalog.Selection selection = entry.selection;
            if (!"located".equals(selection.status)) {
                continue;
            }
            for (Geometry.ChunkCoordinate chunk
                    : selection.chunkBounds.coordinates(selection.dimension)) {
                targets.put(chunk.key(), chunk);
            }
        }
        return List.copyOf(targets.values());
    }

    RenderMasks renderMasks(StructureCatalog catalog) {
        Map<String, RenderMasks.DimensionMasks> dimensions = new TreeMap<>();
        for (StructureCatalog.StructureEntry entry : catalog.structures) {
            StructureCatalog.Selection selection = entry.selection;
            if (!"located".equals(selection.status)) {
                continue;
            }
            RenderMasks.DimensionMasks output = dimensions.computeIfAbsent(
                    selection.dimension,
                    ignored -> {
                        RenderMasks.DimensionMasks value = new RenderMasks.DimensionMasks();
                        value.dimension = selection.dimension;
                        return value;
                    }
            );
            Geometry.BlockBounds bounds = selection.borderedBounds;
            output.renderMask.add(new RenderMasks.Mask(
                    bounds.minX(), bounds.maxX(), bounds.minZ(), bounds.maxZ(),
                    bounds.minY(), bounds.maxY()
            ));
        }
        RenderMasks masks = new RenderMasks();
        masks.worldIdentity = catalog.worldIdentity;
        masks.planFingerprint = catalog.planFingerprint;
        masks.runtimeAttestationSha256 = catalog.runtimeAttestationSha256;
        masks.dimensions = List.copyOf(dimensions.values());
        return masks;
    }

    private LocateOutcome locate(
            PlannedStructure structure,
            EligibilityPlan eligibility
    ) {
        ServerLevel level = eligibility.dimension().level();
        Holder<Structure> holder = eligibility.holder();
        BlockPos anchor = anchor(level);
        ChunkGeneratorStructureState state = level.getChunkSource().getGeneratorState();
        List<StructurePlacement> placements = state.getPlacementsForStructure(holder);
        List<StructurePlacement> standard = placements.stream()
                .filter(StructureCatalogService::isStandardPlacement)
                .toList();
        List<StructurePlacement> custom = placements.stream()
                .filter(placement -> !isStandardPlacement(placement))
                .toList();

        Candidate standardCandidate = null;
        int usedRadius = config.locateRadiusPlacementRings;
        if (!standard.isEmpty()) {
            Pair<BlockPos, Holder<Structure>> located = level.getChunkSource()
                    .getGenerator()
                    .findNearestMapStructure(
                            level,
                            HolderSet.direct(holder),
                            anchor,
                            config.locateRadiusPlacementRings,
                            false
                    );
            if (located == null
                    && config.fallbackLocateRadiusPlacementRings
                    > config.locateRadiusPlacementRings) {
                usedRadius = config.fallbackLocateRadiusPlacementRings;
                located = level.getChunkSource()
                        .getGenerator()
                        .findNearestMapStructure(
                                level,
                                HolderSet.direct(holder),
                                anchor,
                                usedRadius,
                                false
                        );
            }
            if (located != null) {
                standardCandidate = recoverStart(
                        level,
                        holder,
                        standard,
                        located.getFirst(),
                        anchor
                );
                if (standardCandidate == null) {
                    return LocateOutcome.failure(
                            "invalid-start",
                            "Locator returned a position without a matching valid StructureStart"
                    );
                }
            }
        }

        CustomSearchResult customResult = custom.isEmpty()
                ? CustomSearchResult.complete(null)
                : searchCustom(level, holder, custom, anchor);
        if (!customResult.complete()) {
            return LocateOutcome.failure(customResult.status(), customResult.reason());
        }

        Candidate selected = closer(standardCandidate, customResult.candidate());
        if (selected == null) {
            String status = custom.isEmpty() ? "not-found" : "custom-not-found";
            return LocateOutcome.failure(status, "No valid start was found within configured budgets");
        }
        return new LocateOutcome("located", "", selected, usedRadius);
    }

    private Candidate recoverStart(
            ServerLevel level,
            Holder<Structure> holder,
            List<StructurePlacement> placements,
            BlockPos locatePosition,
            BlockPos anchor
    ) {
        int centerX = SectionPos.blockToSectionCoord(locatePosition.getX());
        int centerZ = SectionPos.blockToSectionCoord(locatePosition.getZ());
        Candidate closest = null;
        for (int radius = 1; radius <= 4; radius++) {
            for (int chunkX = centerX - radius; chunkX <= centerX + radius; chunkX++) {
                for (int chunkZ = centerZ - radius; chunkZ <= centerZ + radius; chunkZ++) {
                    ChunkAccess chunk = level.getChunk(
                            chunkX, chunkZ, ChunkStatus.STRUCTURE_STARTS, true
                    );
                    StructureStart start = level.structureManager().getStartForStructure(
                            SectionPos.bottomOf(chunk), holder.value(), chunk
                    );
                    if (start == null || !start.isValid()) {
                        continue;
                    }
                    boolean exact = placements.stream()
                            .map(placement -> placement.getLocatePos(start.getChunkPos()))
                            .anyMatch(locatePosition::equals);
                    if (!exact) {
                        continue;
                    }
                    Candidate candidate = new Candidate(
                            locatePosition,
                            start,
                            distanceSquared(anchor, locatePosition)
                    );
                    closest = closer(closest, candidate);
                }
            }
            if (closest != null) {
                return closest;
            }
        }
        return null;
    }

    private CustomSearchResult searchCustom(
            ServerLevel level,
            Holder<Structure> holder,
            List<StructurePlacement> placements,
            BlockPos anchor
    ) {
        int anchorChunkX = SectionPos.blockToSectionCoord(anchor.getX());
        int anchorChunkZ = SectionPos.blockToSectionCoord(anchor.getZ());
        ChunkGeneratorStructureState state = level.getChunkSource().getGeneratorState();
        long deadline = System.nanoTime()
                + Duration.ofMillis(config.customPlacementTimeBudgetMillis).toNanos();
        int tested = 0;
        Candidate best = null;

        for (int radius = 0; radius <= config.customPlacementChunkRadius; radius++) {
            int minX = anchorChunkX - radius;
            int maxX = anchorChunkX + radius;
            int minZ = anchorChunkZ - radius;
            int maxZ = anchorChunkZ + radius;
            for (int chunkX = minX; chunkX <= maxX; chunkX++) {
                for (int chunkZ = minZ; chunkZ <= maxZ; chunkZ++) {
                    if (radius != 0
                            && chunkX != minX && chunkX != maxX
                            && chunkZ != minZ && chunkZ != maxZ) {
                        continue;
                    }
                    for (StructurePlacement placement : placements) {
                        tested++;
                        if (tested > config.customPlacementCandidateBudget) {
                            return CustomSearchResult.incomplete(
                                    "custom-search-budget-exhausted",
                                    "Tested more than " + config.customPlacementCandidateBudget
                                            + " custom placement candidates"
                            );
                        }
                        if (System.nanoTime() > deadline) {
                            return CustomSearchResult.incomplete(
                                    "custom-search-timeout",
                                    "Exceeded " + config.customPlacementTimeBudgetMillis
                                            + " ms custom placement budget"
                            );
                        }
                        if (!placement.isStructureChunk(state, chunkX, chunkZ)) {
                            continue;
                        }
                        ChunkAccess chunk = level.getChunk(
                                chunkX, chunkZ, ChunkStatus.STRUCTURE_STARTS, true
                        );
                        StructureStart start = level.structureManager().getStartForStructure(
                                SectionPos.bottomOf(chunk), holder.value(), chunk
                        );
                        if (start == null || !start.isValid()) {
                            continue;
                        }
                        BlockPos locatePosition = placement.getLocatePos(start.getChunkPos());
                        Candidate candidate = new Candidate(
                                locatePosition,
                                start,
                                distanceSquared(anchor, locatePosition)
                        );
                        best = closer(best, candidate);
                    }
                }
            }
        }
        return CustomSearchResult.complete(best);
    }

    private StructureCatalog.Selection toSelection(
            String structureId,
            DimensionPlan dimension,
            LocateOutcome outcome,
            long elapsedMillis
    ) {
        Candidate candidate = outcome.candidate();
        ServerLevel level = dimension.level();
        var box = candidate.start().getBoundingBox();
        Geometry.BlockBounds structureBounds = new Geometry.BlockBounds(
                box.minX(), box.minY(), box.minZ(),
                box.maxX(), box.maxY(), box.maxZ()
        ).clampY(
                level.getMinBuildHeight(),
                level.getMaxBuildHeight() - 1
        );
        Geometry.BlockBounds bordered = structureBounds.inflate(
                config.borderBlocks,
                level.getMinBuildHeight(),
                level.getMaxBuildHeight() - 1
        );
        Geometry.ChunkBounds chunks = bordered.chunks();
        if (chunks.count() > config.maxChunksPerStructure) {
            return StructureCatalog.Selection.failure(
                    "oversized",
                    "Bordered structure needs " + chunks.count()
                            + " chunks; configured maximum is " + config.maxChunksPerStructure
            );
        }

        StructureCatalog.Selection selection = StructureCatalog.Selection.pending();
        selection.status = "located";
        selection.reason = "";
        selection.dimension = dimension.id();
        BlockPos locate = candidate.locatePosition();
        selection.locatePosition = new StructureCatalog.Position(
                locate.getX(), locate.getY(), locate.getZ()
        );
        ChunkPos startChunk = candidate.start().getChunkPos();
        selection.startChunk = new StructureCatalog.Chunk(startChunk.x, startChunk.z);
        selection.structureBounds = structureBounds;
        selection.borderedBounds = bordered;
        selection.chunkBounds = chunks;
        selection.chunkCount = chunks.count();
        selection.regions = chunks.regions().stream()
                .sorted(Comparator.comparingInt(Geometry.RegionCoordinate::x)
                        .thenComparingInt(Geometry.RegionCoordinate::z))
                .toList();
        selection.markerId = markerId(structureId);
        selection.searchRadius = outcome.searchRadius();
        selection.elapsedMillis = elapsedMillis;
        return selection;
    }

    private BlockPos anchor(ServerLevel level) {
        return anchor(server, level);
    }

    private static BlockPos anchor(MinecraftServer server, ServerLevel level) {
        BlockPos spawn = server.overworld().getSharedSpawnPos();
        int y = Math.max(
                level.getMinBuildHeight(),
                Math.min(level.getMaxBuildHeight() - 1, level.getSeaLevel())
        );
        return new BlockPos(spawn.getX(), y, spawn.getZ());
    }

    private static CatalogPlan buildPlan(
            MinecraftServer server,
            HarnessConfig config,
            String runtimeAttestationSha256,
            StructureCatalog.StructureEligibilityEvidence structureEligibilityEvidence
    ) {
        Registry<Structure> structureRegistry = server.registryAccess()
                .registryOrThrow(Registries.STRUCTURE);
        Registry<StructureSet> setRegistry = server.registryAccess()
                .registryOrThrow(Registries.STRUCTURE_SET);
        List<DimensionPlan> dimensions = sortedDimensions(server, config);
        Map<String, MutableStructure> structures = new TreeMap<>();

        structureRegistry.holders().forEach(holder -> {
            String id = holder.key().location().toString();
            structures.computeIfAbsent(id, ignored -> new MutableStructure(id, holder))
                    .tags.addAll(tags(holder));
        });

        for (DimensionPlan dimension : dimensions) {
            ChunkGeneratorStructureState state = dimension.level()
                    .getChunkSource().getGeneratorState();
            int inlineSetIndex = 0;
            for (Holder<StructureSet> setHolder : state.possibleStructureSets()) {
                ResourceLocation registeredSetId = setRegistry.getKey(setHolder.value());
                String setId = registeredSetId == null
                        ? "inline-set:" + dimension.id() + ":" + inlineSetIndex
                        : registeredSetId.toString();
                inlineSetIndex++;
                int entryIndex = 0;
                for (StructureSet.StructureSelectionEntry entry
                        : setHolder.value().structures()) {
                    Holder<Structure> holder = entry.structure();
                    List<StructurePlacement> placements = state
                            .getPlacementsForStructure(holder);
                    if (placements.isEmpty()) {
                        entryIndex++;
                        continue;
                    }
                    ResourceLocation registeredId = structureRegistry.getKey(holder.value());
                    String id = registeredId == null
                            ? "inline:" + setId + "#" + entryIndex
                            : registeredId.toString();
                    MutableStructure structure = structures.computeIfAbsent(
                            id,
                            ignored -> new MutableStructure(id, holder)
                    );
                    structure.tags.addAll(tags(holder));
                    MutableEligibility eligibility = structure.eligibility.computeIfAbsent(
                            dimension.id(),
                            ignored -> new MutableEligibility(dimension, holder)
                    );
                    eligibility.structureSets.add(setId);
                    placements.stream().forEach(placement -> {
                        eligibility.placementTypes.add(placementType(placement));
                        eligibility.placementDescriptors.add(
                                placementDescriptor(server, placement)
                        );
                    });
                    entryIndex++;
                }
            }
        }

        Map<String, String> disabledReasons = StructureEligibilityRules.disabledReasons(
                structureEligibilityEvidence
        );
        for (String target : StructureEligibilityRules.declaredStructures(
                structureEligibilityEvidence
        )) {
            MutableStructure structure = structures.get(target);
            if (structure == null) {
                throw new IllegalStateException(
                        "Exact structure eligibility target is absent from the live registry: "
                                + target
                );
            }
            if (disabledReasons.containsKey(target)) {
                structure.eligibility.clear();
            } else if (structure.eligibility.isEmpty()) {
                throw new IllegalStateException(
                        "Enabled structure eligibility target lacks a live placement: "
                                + target
                );
            }
        }

        List<PlannedStructure> planned = structures.values().stream()
                .map(MutableStructure::freeze)
                .toList();
        String worldIdentity = worldIdentity(server);
        String fingerprint = fingerprint(
                server,
                config,
                planned,
                dimensions,
                worldIdentity,
                runtimeAttestationSha256,
                structureEligibilityEvidence
        );
        return new CatalogPlan(
                planned,
                dimensions,
                structureRegistry.size(),
                worldIdentity,
                fingerprint,
                structureEligibilityEvidence,
                disabledReasons
        );
    }

    private static List<DimensionPlan> sortedDimensions(
            MinecraftServer server,
            HarnessConfig config
    ) {
        Map<String, Integer> priority = new HashMap<>();
        for (int index = 0; index < config.dimensionPriority.size(); index++) {
            priority.put(config.dimensionPriority.get(index), index);
        }
        return StreamSupport.stream(server.getAllLevels().spliterator(), false)
                .map(level -> new DimensionPlan(level.dimension().location().toString(), level))
                .sorted(Comparator
                        .comparingInt((DimensionPlan dimension) -> priority.getOrDefault(
                                dimension.id(), Integer.MAX_VALUE
                        ))
                        .thenComparing(DimensionPlan::id))
                .toList();
    }

    private static List<String> tags(Holder<Structure> holder) {
        return holder.tags()
                .map(tag -> "#" + tag.location())
                .sorted()
                .toList();
    }

    private static String placementType(StructurePlacement placement) {
        ResourceLocation id = BuiltInRegistries.STRUCTURE_PLACEMENT.getKey(
                placement.type()
        );
        return id == null ? placement.getClass().getName() : id.toString();
    }

    private static String placementDescriptor(
            MinecraftServer server, StructurePlacement placement
    ) {
        return StructurePlacement.CODEC.encodeStart(
                server.registryAccess().createSerializationContext(JsonOps.INSTANCE),
                placement
        ).getOrThrow().toString();
    }

    private static String worldIdentity(MinecraftServer server) {
        java.nio.file.Path path = server.getWorldPath(LevelResource.ROOT)
                .resolve(WORLD_ID_FILE);
        try {
            if (!Files.exists(path)) {
                Files.writeString(
                        path,
                        UUID.randomUUID().toString() + "\n",
                        StandardCharsets.UTF_8,
                        StandardOpenOption.CREATE_NEW,
                        StandardOpenOption.WRITE
                );
            }
            String value = Files.readString(path, StandardCharsets.UTF_8).trim();
            return UUID.fromString(value).toString();
        } catch (IOException | IllegalArgumentException exception) {
            throw new IllegalStateException(
                    "Could not establish the integration world identity", exception
            );
        }
    }

    private static boolean isStandardPlacement(StructurePlacement placement) {
        return placement instanceof RandomSpreadStructurePlacement
                || placement instanceof ConcentricRingsStructurePlacement;
    }

    private static Candidate closer(Candidate first, Candidate second) {
        if (first == null) {
            return second;
        }
        if (second == null) {
            return first;
        }
        return second.distanceSquared() < first.distanceSquared() ? second : first;
    }

    private static long distanceSquared(BlockPos first, BlockPos second) {
        long x = (long) second.getX() - first.getX();
        long z = (long) second.getZ() - first.getZ();
        return x * x + z * z;
    }

    private static String markerId(String structureId) {
        return structureId.toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9._-]", "_");
    }

    private static String fingerprint(
            MinecraftServer server,
            HarnessConfig config,
            List<PlannedStructure> structures,
            List<DimensionPlan> dimensions,
            String worldIdentity,
            String runtimeAttestationSha256,
            StructureCatalog.StructureEligibilityEvidence structureEligibilityEvidence
    ) {
        String input = "world=" + worldIdentity
                + "\nruntime-attestation=" + runtimeAttestationSha256
                + "\npolicy=" + config.borderBlocks
                + "," + config.locateRadiusPlacementRings
                + "," + config.fallbackLocateRadiusPlacementRings
                + "," + config.customPlacementChunkRadius
                + "," + config.customPlacementCandidateBudget
                + "," + config.customPlacementTimeBudgetMillis
                + "," + config.maxChunksPerStructure
                + "," + String.join(",", config.dimensionPriority)
                + "\nstructure-eligibility-evidence="
                + StructureEligibilityRules.fingerprintComponent(
                        structureEligibilityEvidence
                )
                + "\n--dimensions--\n"
                + dimensions.stream().map(dimension -> {
                    ServerLevel level = dimension.level();
                    BlockPos anchor = anchor(server, level);
                    return dimension.id() + "|seed=" + level.getSeed()
                            + "|generator=" + level.getChunkSource().getGenerator()
                                    .getClass().getName()
                            + "|height=" + level.getMinBuildHeight() + ":"
                                    + level.getMaxBuildHeight()
                            + "|sea=" + level.getSeaLevel()
                            + "|anchor=" + anchor.getX() + ":" + anchor.getY()
                                    + ":" + anchor.getZ();
                })
                .collect(Collectors.joining("\n"))
                + "\n--structures--\n"
                + structures.stream().map(structure -> structure.id() + "|tags="
                        + String.join(",", structure.tags()) + "|eligibility="
                        + structure.eligibility().stream()
                                .map(eligibility -> eligibility.dimension().id()
                                        + "[sets="
                                        + String.join(",", eligibility.structureSets())
                                        + ";types="
                                        + String.join(",", eligibility.placementTypes())
                                        + ";placements="
                                        + String.join(",", eligibility.placementDescriptors())
                                        + "]")
                                .collect(Collectors.joining(",")))
                        .collect(Collectors.joining("\n"));
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(input.getBytes(StandardCharsets.UTF_8));
            return java.util.HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }

    record CatalogPlan(
            List<PlannedStructure> structures,
            List<DimensionPlan> dimensions,
            int registeredCount,
            String worldIdentity,
            String fingerprint,
            StructureCatalog.StructureEligibilityEvidence structureEligibilityEvidence,
            Map<String, String> disabledReasons
    ) {
    }

    record PlannedStructure(
            String id,
            Holder<Structure> holder,
            List<String> tags,
            List<EligibilityPlan> eligibility
    ) {
    }

    record EligibilityPlan(
            DimensionPlan dimension,
            Holder<Structure> holder,
            List<String> structureSets,
            List<String> placementTypes,
            List<String> placementDescriptors
    ) {
    }

    record DimensionPlan(String id, ServerLevel level) {
    }

    private static final class MutableStructure {
        private final String id;
        private final Holder<Structure> holder;
        private final Set<String> tags = new LinkedHashSet<>();
        private final Map<String, MutableEligibility> eligibility = new LinkedHashMap<>();

        private MutableStructure(String id, Holder<Structure> holder) {
            this.id = id;
            this.holder = holder;
        }

        private PlannedStructure freeze() {
            return new PlannedStructure(
                    id,
                    holder,
                    tags.stream().sorted().toList(),
                    eligibility.values().stream().map(MutableEligibility::freeze).toList()
            );
        }
    }

    private static final class MutableEligibility {
        private final DimensionPlan dimension;
        private final Holder<Structure> holder;
        private final Set<String> structureSets = new LinkedHashSet<>();
        private final Set<String> placementTypes = new LinkedHashSet<>();
        private final Set<String> placementDescriptors = new LinkedHashSet<>();

        private MutableEligibility(DimensionPlan dimension, Holder<Structure> holder) {
            this.dimension = dimension;
            this.holder = holder;
        }

        private EligibilityPlan freeze() {
            return new EligibilityPlan(
                    dimension,
                    holder,
                    structureSets.stream().sorted().toList(),
                    placementTypes.stream().sorted().toList(),
                    placementDescriptors.stream().sorted().toList()
            );
        }
    }

    private record Candidate(
            BlockPos locatePosition,
            StructureStart start,
            long distanceSquared
    ) {
    }

    private record LocateOutcome(
            String status,
            String reason,
            Candidate candidate,
            int searchRadius
    ) {
        private static LocateOutcome failure(String status, String reason) {
            return new LocateOutcome(status, reason, null, 0);
        }
    }

    private record CustomSearchResult(
            boolean complete,
            String status,
            String reason,
            Candidate candidate
    ) {
        private static CustomSearchResult complete(Candidate candidate) {
            return new CustomSearchResult(true, "complete", "", candidate);
        }

        private static CustomSearchResult incomplete(String status, String reason) {
            return new CustomSearchResult(false, status, reason, null);
        }
    }
}
