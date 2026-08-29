package io.github.janguenter.bluemap.atmons.integration;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.UUID;

/** Per-process nonce proving the command and filesystem transports meet one server. */
final class RuntimeIdentity {
    static final String FILE_NAME = "runtime-identity.json";

    int schemaVersion = 1;
    String bootId;
    String runtimeAttestationSha256;
    String startedAt;

    static RuntimeIdentity create(Path directory, String attestationFile) throws IOException {
        RuntimeAttestation.Loaded attestation = RuntimeAttestation.load(
                directory.resolve(attestationFile)
        );
        RuntimeIdentity identity = new RuntimeIdentity();
        identity.bootId = UUID.randomUUID().toString();
        identity.runtimeAttestationSha256 = attestation.sha256();
        identity.startedAt = Instant.now().toString();
        JsonFiles.writeAtomic(directory.resolve(FILE_NAME), identity);
        return identity;
    }

    String commandMessage() {
        validate();
        return "bootId=" + bootId
                + " runtimeAttestationSha256=" + runtimeAttestationSha256;
    }

    void validate() {
        try {
            UUID.fromString(bootId);
            Instant.parse(startedAt);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException("Runtime identity is malformed", exception);
        }
        if (schemaVersion != 1
                || runtimeAttestationSha256 == null
                || !runtimeAttestationSha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("Runtime identity is incomplete");
        }
    }
}
