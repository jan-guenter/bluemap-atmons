package io.github.janguenter.bluemap.atmons.integration;

import de.bluecolored.bluemap.api.BlueMapAPI;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.LevelChunk;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Owns resumable catalog/generation work and the small synchronous actions. */
final class IntegrationController {
    private static final Logger LOGGER = LoggerFactory.getLogger("BlueMapAtMonsIntegration");

    private final Path directory;
    private final HarnessConfig config;
    private MinecraftServer server;
    private StructureCatalogService catalogService;
    private StructureCatalog catalog;
    private WorkState workState = WorkState.idle();
    private BlueMapAPI blueMapApi;
    private ImmersiveEngineeringGalleryBridge immersiveEngineeringBridge;
    private RuntimeIdentity runtimeIdentity;

    IntegrationController(Path directory, HarnessConfig config) {
        this.directory = directory;
        this.config = config;
    }

    void serverStarted(MinecraftServer startedServer) {
        server = startedServer;
        try {
            runtimeIdentity = RuntimeIdentity.create(
                    directory, config.runtimeAttestationFile
            );
            LOGGER.info(
                    "BlueMap ATMons integration harness boot: bootId={} "
                            + "runtimeAttestationSha256={}",
                    runtimeIdentity.bootId,
                    runtimeIdentity.runtimeAttestationSha256
            );
        } catch (IOException | IllegalArgumentException exception) {
            throw new IllegalStateException(
                    "Could not establish the attested runtime identity", exception
            );
        }
        catalogService = new StructureCatalogService(startedServer, config, directory);
        immersiveEngineeringBridge = new ImmersiveEngineeringGalleryBridge(startedServer);
        try {
            Optional<WorkState> persisted = JsonFiles.readIfExists(
                    workStatePath(), WorkState.class
            );
            if (persisted.isPresent()) {
                workState = persisted.get();
                workState.validate();
                resumePersistedWork();
            }
        } catch (IOException | IllegalArgumentException exception) {
            LOGGER.error("Failed to resume integration harness work", exception);
            workState = WorkState.idle();
            workState.status = "error";
            workState.message = "Resume failed: " + exception.getMessage();
            persistWorkStateQuietly();
        }
        if (blueMapApi != null) {
            publishExistingQuietly();
        }
    }

    void serverStopping() {
        persistWorkStateQuietly();
    }

    void blueMapEnabled(BlueMapAPI api) {
        blueMapApi = api;
        if (server == null) {
            return;
        }
        publishExistingQuietly();
    }

    private void publishExistingQuietly() {
        try {
            MarkerPublisher publisher = new MarkerPublisher(
                    blueMapApi, server, config, directory
            );
            publisher.publishExisting();
        } catch (IOException | IllegalArgumentException exception) {
            LOGGER.warn("Deferred BlueMap marker publication did not complete", exception);
        }
    }

    void tick() {
        if (server == null || !"running".equals(workState.status)) {
            return;
        }
        try {
            switch (workState.operation) {
                case "catalog" -> tickCatalog();
                case "generate" -> tickGenerate();
                default -> failWork("Unknown running operation: " + workState.operation);
            }
        } catch (RuntimeException | IOException exception) {
            LOGGER.error("Integration harness operation failed", exception);
            failWork(exception.getClass().getSimpleName() + ": " + exception.getMessage());
        }
    }

    ActionResult startCatalog() {
        if (server == null) {
            return ActionResult.failure("Server is not ready");
        }
        if ("running".equals(workState.status)) {
            return ActionResult.failure("Another operation is already running: "
                    + workState.operation);
        }
        if (hasOutstandingForceLoads()) {
            return ActionResult.failure(
                    "Harness-owned force-loads remain from prior work; run clean-forceloads first"
            );
        }
        try {
            catalogService = new StructureCatalogService(server, config, directory);
            catalog = catalogService.createCatalog();
            Files.deleteIfExists(directory.resolve(GenerationReceipt.FILE_NAME));
            workState = WorkState.idle();
            workState.operation = "catalog";
            workState.status = "running";
            workState.planFingerprint = catalogService.plan().fingerprint();
            workState.total = catalogService.plan().structures().size();
            workState.message = "Cataloging runtime structures";
            persistCatalogAndState();
            return ActionResult.success(
                    "Started catalog of " + workState.total + " runtime structures",
                    workState.total
            );
        } catch (IOException exception) {
            return ActionResult.failure("Could not start catalog: " + exception.getMessage());
        }
    }

    ActionResult startGenerate() {
        if (server == null) {
            return ActionResult.failure("Server is not ready");
        }
        if ("running".equals(workState.status)) {
            return ActionResult.failure("Another operation is already running: "
                    + workState.operation);
        }
        if (hasOutstandingForceLoads()) {
            return ActionResult.failure(
                    "Harness-owned force-loads remain from prior work; run clean-forceloads first"
            );
        }
        try {
            StructureCatalog loaded = JsonFiles.read(catalogPath(), StructureCatalog.class);
            catalogService.validateLiveCatalog(loaded);
            List<Geometry.ChunkCoordinate> targets = catalogService
                    .generationTargets(loaded);
            Files.deleteIfExists(directory.resolve(GenerationReceipt.FILE_NAME));
            workState = WorkState.idle();
            workState.operation = "generate";
            workState.status = "running";
            workState.planFingerprint = catalogService.plan().fingerprint();
            workState.targets = new ArrayList<>(targets);
            workState.total = targets.size();
            workState.message = "Generating and flushing catalog chunks";
            catalog = loaded;
            persistWorkState();
            return ActionResult.success(
                    "Started generation of " + targets.size() + " unique chunks",
                    targets.size()
            );
        } catch (IOException | IllegalArgumentException exception) {
            return ActionResult.failure("Could not start generation: " + exception.getMessage());
        }
    }

    ActionResult publishStructures() {
        try {
            requireCompletedGeneration();
            return publisher().publishStructures();
        } catch (IOException | IllegalArgumentException exception) {
            return ActionResult.failure("Structure publication failed: " + exception.getMessage());
        }
    }

    ActionResult publishGalleries() {
        try {
            return publisher().publishGalleries();
        } catch (IOException | IllegalArgumentException exception) {
            return ActionResult.failure("Gallery publication failed: " + exception.getMessage());
        }
    }

    ActionResult renderGalleries() {
        try {
            return publisher().scheduleGalleryRender();
        } catch (IOException | ReflectiveOperationException | RuntimeException exception) {
            return ActionResult.failure("Gallery render scheduling failed: "
                    + exception.getMessage());
        }
    }

    ActionResult verifyGalleryRender() {
        try {
            return publisher().verifyGalleryRender();
        } catch (IOException | ReflectiveOperationException | RuntimeException exception) {
            return ActionResult.failure("Gallery render verification failed: "
                    + exception.getMessage());
        }
    }

    ActionResult renderStructures() {
        try {
            requireCompletedGeneration();
            return publisher().scheduleStructureRenders();
        } catch (IOException | ReflectiveOperationException
                | IllegalArgumentException exception) {
            return ActionResult.failure("Structure render scheduling failed: "
                    + exception.getMessage());
        }
    }

    ActionResult verifyStructureRenders() {
        try {
            requireCompletedGeneration();
            return publisher().verifyStructureRenders();
        } catch (IOException | ReflectiveOperationException
                | IllegalArgumentException exception) {
            return ActionResult.failure("Structure render verification failed: "
                    + exception.getMessage());
        }
    }

    ActionResult cleanOwnedForceLoads() {
        if (server == null) {
            return ActionResult.failure("Server is not ready");
        }
        int removed = 0;
        Set<String> seen = new HashSet<>();
        List<Geometry.ChunkCoordinate> retained = new ArrayList<>();
        for (Geometry.ChunkCoordinate chunk
                : new ArrayList<>(workState.ownedForcedChunks)) {
            if (!seen.add(chunk.key())) {
                continue;
            }
            ServerLevel level = level(chunk.dimension());
            if (level == null) {
                retained.add(chunk);
                continue;
            }
            level.setChunkForced(chunk.x(), chunk.z(), false);
            if (!level.getForcedChunks().contains(ChunkPos.asLong(chunk.x(), chunk.z()))) {
                removed++;
            } else {
                retained.add(chunk);
            }
        }
        workState.ownedForcedChunks = retained;
        Set<String> retainedKeys = retained.stream()
                .map(Geometry.ChunkCoordinate::key)
                .collect(java.util.stream.Collectors.toSet());
        workState.activeBatch.removeIf(chunk -> !retainedKeys.contains(chunk.key()));
        if ("running".equals(workState.status) && "generate".equals(workState.operation)) {
            workState.status = retained.isEmpty() ? "cancelled" : "blocked";
            workState.message = retained.isEmpty()
                    ? "Generation cancelled by clean-forceloads"
                    : "Generation blocked; some harness-owned force-loads could not be removed";
        }
        persistWorkStateQuietly();
        if (!retained.isEmpty()) {
            return new ActionResult(
                    false,
                    removed,
                    "Removed " + removed + " harness-owned force-loads; retained "
                            + retained.size()
            );
        }
        return ActionResult.success("Removed " + removed + " harness-owned force-loads", removed);
    }

    ActionResult formImmersiveEngineering(ServerLevel level) {
        if (immersiveEngineeringBridge == null) {
            return ActionResult.failure("Server is not ready");
        }
        return immersiveEngineeringBridge.form(level);
    }

    ActionResult verifyImmersiveEngineering(ServerLevel level) {
        if (immersiveEngineeringBridge == null) {
            return ActionResult.failure("Server is not ready");
        }
        return immersiveEngineeringBridge.verify(level);
    }

    ActionResult status() {
        String status = "operation=" + workState.operation
                + " status=" + workState.status
                + " progress=" + workState.cursor + "/" + workState.total
                + " batch=" + workState.activeBatch.size()
                + " ownedForced=" + workState.ownedForcedChunks.size()
                + " updated=" + workState.updatedAt
                + " message=" + workState.message;
        return ActionResult.success(status, workState.cursor);
    }

    ActionResult runtimeIdentity() {
        if (runtimeIdentity == null) {
            return ActionResult.failure("Runtime identity is not ready");
        }
        return ActionResult.success(runtimeIdentity.commandMessage(), 1);
    }

    private void tickCatalog() throws IOException {
        if (catalog == null) {
            catalog = JsonFiles.read(catalogPath(), StructureCatalog.class);
        }
        if (workState.cursor >= workState.total) {
            catalogService.finalizeSummary(catalog);
            catalogService.validateLiveCatalog(catalog);
            JsonFiles.writeAtomic(catalogPath(), catalog);
            JsonFiles.writeAtomic(
                    directory.resolve(config.renderMasksFile),
                    catalogService.renderMasks(catalog)
            );
            workState.status = "complete";
            workState.message = "Catalog complete: " + catalog.summary.located
                    + " located, " + catalog.summary.unlocated + " unlocated";
            persistWorkState();
            return;
        }

        catalogService.processEntry(catalog, workState.cursor);
        workState.cursor++;
        workState.message = "Cataloged " + workState.cursor + "/" + workState.total;
        persistCatalogAndState();
    }

    private void tickGenerate() throws IOException {
        if (workState.cursor >= workState.total
                && workState.activeBatch.isEmpty()
                && workState.ownedForcedChunks.isEmpty()) {
            requireExactGenerationState(catalog, workState, false);
            JsonFiles.writeAtomic(
                    directory.resolve(GenerationReceipt.FILE_NAME),
                    GenerationReceipt.create(catalogPath(), catalog, workState.targets)
            );
            workState.status = "complete";
            workState.message = "Generated and flushed " + workState.total + " chunks";
            persistWorkState();
            return;
        }

        // Reconcile a write-ahead batch after a process interruption. Every
        // harness-owned force intent is persisted before setChunkForced.
        Set<String> activeKeys = workState.activeBatch.stream()
                .map(Geometry.ChunkCoordinate::key)
                .collect(java.util.stream.Collectors.toSet());
        for (Geometry.ChunkCoordinate owned : workState.ownedForcedChunks) {
            if (activeKeys.add(owned.key())) {
                workState.activeBatch.add(owned);
            }
        }
        ensureActiveBatchLoaded();

        int processed = 0;
        while (processed < config.chunksPerTick
                && workState.cursor < workState.total
                && workState.activeBatch.size() < config.maxForcedBatchChunks) {
            Geometry.ChunkCoordinate target = workState.targets.get(workState.cursor);
            ServerLevel level = level(target.dimension());
            if (level == null) {
                throw new IllegalStateException("Dimension is no longer loaded: "
                        + target.dimension());
            }
            boolean alreadyForced = level.getForcedChunks().contains(
                    ChunkPos.asLong(target.x(), target.z())
            );
            workState.activeBatch.add(target);
            if (!alreadyForced) {
                workState.ownedForcedChunks.add(target);
            }
            workState.cursor++;
            // Write-ahead ownership makes a crash before the mutation
            // recoverable without claiming pre-existing force-loads.
            persistWorkState();
            level.setChunkForced(target.x(), target.z(), true);
            level.getChunk(target.x(), target.z());
            processed++;
        }

        boolean batchReadyToFlush = !workState.activeBatch.isEmpty()
                && (workState.activeBatch.size() >= config.maxForcedBatchChunks
                || workState.cursor >= workState.total);
        if (batchReadyToFlush && batchIsLightCorrect()) {
            server.saveEverything(false, true, true);
            releaseActiveBatch();
        }
        workState.message = "Generated " + workState.cursor + "/" + workState.total
                + "; active flush batch=" + workState.activeBatch.size();
        persistWorkState();
    }

    private boolean batchIsLightCorrect() {
        for (Geometry.ChunkCoordinate target : workState.activeBatch) {
            ServerLevel level = level(target.dimension());
            if (level == null) {
                return false;
            }
            LevelChunk chunk = level.getChunkSource().getChunkNow(target.x(), target.z());
            if (chunk == null || !chunk.isLightCorrect()) {
                return false;
            }
        }
        return true;
    }

    private void ensureActiveBatchLoaded() {
        Set<String> owned = workState.ownedForcedChunks.stream()
                .map(Geometry.ChunkCoordinate::key)
                .collect(java.util.stream.Collectors.toSet());
        for (Geometry.ChunkCoordinate target : workState.activeBatch) {
            ServerLevel level = level(target.dimension());
            if (level == null) {
                throw new IllegalStateException(
                        "Dimension is no longer loaded: " + target.dimension()
                );
            }
            if (owned.contains(target.key())) {
                level.setChunkForced(target.x(), target.z(), true);
            }
            level.getChunk(target.x(), target.z());
        }
    }

    private void releaseActiveBatch() {
        Set<String> active = workState.activeBatch.stream()
                .map(Geometry.ChunkCoordinate::key)
                .collect(java.util.stream.Collectors.toSet());
        List<Geometry.ChunkCoordinate> retained = new ArrayList<>();
        List<Geometry.ChunkCoordinate> retainedActive = new ArrayList<>();
        for (Geometry.ChunkCoordinate owned : workState.ownedForcedChunks) {
            if (!active.contains(owned.key())) {
                retained.add(owned);
                continue;
            }
            ServerLevel level = level(owned.dimension());
            if (level != null) {
                level.setChunkForced(owned.x(), owned.z(), false);
            }
            if (level == null || level.getForcedChunks().contains(
                    ChunkPos.asLong(owned.x(), owned.z())
            )) {
                retained.add(owned);
                retainedActive.add(owned);
            }
        }
        workState.ownedForcedChunks = retained;
        workState.activeBatch = retainedActive;
    }

    private void resumePersistedWork() throws IOException {
        if (!"running".equals(workState.status)) {
            return;
        }
        if (!catalogService.plan().fingerprint().equals(workState.planFingerprint)) {
            workState.status = "blocked";
            workState.message = "Runtime registry plan changed; start a fresh catalog";
            persistWorkState();
            return;
        }
        if ("catalog".equals(workState.operation)) {
            catalog = JsonFiles.read(catalogPath(), StructureCatalog.class);
        } else if ("generate".equals(workState.operation)) {
            catalog = JsonFiles.read(catalogPath(), StructureCatalog.class);
            catalogService.validateLiveCatalog(catalog);
            requireExactGenerationState(catalog, workState, false);
        } else {
            workState.status = "error";
            workState.message = "Unknown persisted operation: " + workState.operation;
            persistWorkState();
        }
    }

    private void requireCompletedGeneration() throws IOException {
        StructureCatalog loaded = JsonFiles.read(catalogPath(), StructureCatalog.class);
        catalogService.validateLiveCatalog(loaded);
        WorkState persisted = JsonFiles.read(workStatePath(), WorkState.class);
        persisted.validate();
        requireExactGenerationState(loaded, persisted, true);
        GenerationReceipt.loadAndValidate(
                directory,
                catalogPath(),
                loaded,
                persisted.targets
        );
    }

    private void requireExactGenerationState(
            StructureCatalog loaded,
            WorkState state,
            boolean requireComplete
    ) {
        state.validate();
        List<Geometry.ChunkCoordinate> expected = catalogService
                .generationTargets(loaded);
        if (!"generate".equals(state.operation)
                || !catalogService.plan().fingerprint().equals(state.planFingerprint)
                || state.total != expected.size()
                || !state.targets.equals(expected)
                || (requireComplete && (!"complete".equals(state.status)
                || state.cursor != state.total
                || !state.activeBatch.isEmpty()
                || !state.ownedForcedChunks.isEmpty()))) {
            throw new IllegalArgumentException(
                    "Generation state does not match the exact catalog-derived target set"
            );
        }
    }

    private MarkerPublisher publisher() {
        if (server == null) {
            throw new IllegalStateException("Server is not ready");
        }
        BlueMapAPI api = blueMapApi != null
                ? blueMapApi
                : BlueMapAPI.getInstance().orElseThrow(
                        () -> new IllegalStateException("BlueMap API is not enabled")
                );
        return new MarkerPublisher(api, server, config, directory);
    }

    private ServerLevel level(String dimension) {
        ResourceLocation id = ResourceLocation.tryParse(dimension);
        if (id == null) {
            return null;
        }
        ResourceKey<Level> key = ResourceKey.create(Registries.DIMENSION, id);
        return server.getLevel(key);
    }

    private void persistCatalogAndState() throws IOException {
        workState.touch();
        JsonFiles.writeAtomic(catalogPath(), catalog);
        JsonFiles.writeAtomic(workStatePath(), workState);
    }

    private void persistWorkState() throws IOException {
        workState.touch();
        JsonFiles.writeAtomic(workStatePath(), workState);
    }

    private void persistWorkStateQuietly() {
        try {
            persistWorkState();
        } catch (IOException exception) {
            LOGGER.error("Could not persist integration harness work state", exception);
        }
    }

    private void failWork(String message) {
        workState.status = "error";
        workState.message = message;
        persistWorkStateQuietly();
    }

    private boolean hasOutstandingForceLoads() {
        return !workState.ownedForcedChunks.isEmpty() || !workState.activeBatch.isEmpty();
    }

    private Path catalogPath() {
        return directory.resolve(config.catalogFile);
    }

    private Path workStatePath() {
        return directory.resolve(config.workStateFile);
    }

    record ActionResult(boolean successful, int count, String message) {
        static ActionResult success(String message, int count) {
            return new ActionResult(true, count, message);
        }

        static ActionResult failure(String message) {
            return new ActionResult(false, 0, message);
        }
    }
}
