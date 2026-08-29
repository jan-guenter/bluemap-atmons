package io.github.janguenter.bluemap.atmons.integration;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Locale;

/** Deterministic collision-resistant BlueMap map IDs for runtime dimensions. */
final class BlueMapMapContract {
    private static final int MAX_SLUG_LENGTH = 64;

    private BlueMapMapContract() {
    }

    static String safeMapId(String dimension) {
        if (dimension == null || dimension.isBlank()) {
            throw new IllegalArgumentException("dimension is required");
        }
        String slug = dimension.toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9]+", "_")
                .replaceAll("^_+|_+$", "");
        if (slug.isBlank()) {
            slug = "dimension";
        }
        if (slug.length() > MAX_SLUG_LENGTH) {
            slug = slug.substring(0, MAX_SLUG_LENGTH).replaceAll("_+$", "");
        }
        return "atmons_" + slug + "_" + sha256(dimension).substring(0, 12);
    }

    static String configFile(String dimension) {
        return "maps/" + safeMapId(dimension) + ".conf";
    }

    private static String sha256(String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }
}
