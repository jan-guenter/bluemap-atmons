package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import org.junit.jupiter.api.Test;

class WorkStateTest {
    @Test
    void completedGenerationRequiresExactCleanTargetCardinality() {
        Geometry.ChunkCoordinate target = new Geometry.ChunkCoordinate(
                "minecraft:overworld", 1, 2
        );
        WorkState complete = WorkState.idle();
        complete.operation = "generate";
        complete.status = "complete";
        complete.planFingerprint = "a".repeat(64);
        complete.targets = List.of(target);
        complete.total = 1;
        complete.cursor = 1;
        assertDoesNotThrow(complete::validate);

        WorkState truncated = copy(complete);
        truncated.total = 0;
        assertThrows(IllegalArgumentException.class, truncated::validate);

        WorkState incomplete = copy(complete);
        incomplete.cursor = 0;
        assertThrows(IllegalArgumentException.class, incomplete::validate);

        WorkState dirty = copy(complete);
        dirty.ownedForcedChunks = List.of(target);
        assertThrows(IllegalArgumentException.class, dirty::validate);
    }

    private static WorkState copy(WorkState source) {
        WorkState copy = WorkState.idle();
        copy.operation = source.operation;
        copy.status = source.status;
        copy.planFingerprint = source.planFingerprint;
        copy.targets = source.targets;
        copy.total = source.total;
        copy.cursor = source.cursor;
        return copy;
    }
}
