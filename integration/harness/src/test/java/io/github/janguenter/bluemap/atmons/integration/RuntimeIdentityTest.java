package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class RuntimeIdentityTest {
    @Test
    void validatesAndFormatsExactBootIdentity() {
        RuntimeIdentity identity = new RuntimeIdentity();
        identity.bootId = "123e4567-e89b-42d3-a456-426614174000";
        identity.runtimeAttestationSha256 = "a".repeat(64);
        identity.startedAt = "2026-08-28T11:00:00Z";
        assertDoesNotThrow(identity::validate);
        assertTrue(identity.commandMessage().contains("bootId=" + identity.bootId));

        identity.runtimeAttestationSha256 = "bad";
        assertThrows(IllegalArgumentException.class, identity::validate);
    }
}
