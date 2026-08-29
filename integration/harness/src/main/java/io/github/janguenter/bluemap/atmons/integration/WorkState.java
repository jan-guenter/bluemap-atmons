package io.github.janguenter.bluemap.atmons.integration;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Crash-resumable cursor and harness-owned force-load ledger. */
final class WorkState {
    int schemaVersion = 1;
    String operation = "idle";
    String status = "idle";
    String planFingerprint = "";
    int cursor;
    int total;
    String message = "";
    String updatedAt = Instant.now().toString();
    List<Geometry.ChunkCoordinate> targets = new ArrayList<>();
    List<Geometry.ChunkCoordinate> activeBatch = new ArrayList<>();
    List<Geometry.ChunkCoordinate> ownedForcedChunks = new ArrayList<>();

    static WorkState idle() {
        return new WorkState();
    }

    void touch() {
        updatedAt = Instant.now().toString();
    }

    void validate() {
        if (schemaVersion != 1) {
            throw new IllegalArgumentException("Unsupported work-state schemaVersion");
        }
        if (cursor < 0 || total < 0 || cursor > total) {
            throw new IllegalArgumentException("Invalid work-state cursor");
        }
        if (targets == null || activeBatch == null || ownedForcedChunks == null) {
            throw new IllegalArgumentException("Invalid work-state collections");
        }
        try {
            Instant.parse(updatedAt);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException("Invalid work-state update time", exception);
        }
        if (!Set.of("idle", "catalog", "generate").contains(operation)
                || !Set.of(
                        "idle", "running", "complete", "error", "blocked", "cancelled"
                ).contains(status)
                || (!("idle".equals(operation) && "idle".equals(status))
                && (planFingerprint == null
                || !planFingerprint.matches("[0-9a-f]{64}")))) {
            throw new IllegalArgumentException("Invalid work-state operation/status identity");
        }
        if ("generate".equals(operation) && total != targets.size()) {
            throw new IllegalArgumentException("Generation target count differs from total");
        }
        if ("catalog".equals(operation) && (!targets.isEmpty()
                || !activeBatch.isEmpty() || !ownedForcedChunks.isEmpty())) {
            throw new IllegalArgumentException("Catalog work state contains generation chunks");
        }
        Set<String> targetKeys = uniqueKeys(targets, "targets");
        Set<String> activeKeys = uniqueKeys(activeBatch, "active batch");
        Set<String> ownedKeys = uniqueKeys(ownedForcedChunks, "owned force-loads");
        if (!targetKeys.containsAll(activeKeys) || !activeKeys.containsAll(ownedKeys)) {
            throw new IllegalArgumentException("Generation batch/ownership is outside targets");
        }
        if ("complete".equals(status) && (cursor != total
                || !activeBatch.isEmpty() || !ownedForcedChunks.isEmpty())) {
            throw new IllegalArgumentException("Completed work state is not terminally clean");
        }
    }

    private static Set<String> uniqueKeys(
            List<Geometry.ChunkCoordinate> chunks, String label
    ) {
        Set<String> keys = new HashSet<>();
        for (Geometry.ChunkCoordinate chunk : chunks) {
            if (chunk == null || !keys.add(chunk.key())) {
                throw new IllegalArgumentException("Invalid or duplicate " + label);
            }
        }
        return keys;
    }
}
