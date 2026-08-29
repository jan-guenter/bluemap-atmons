package io.github.janguenter.bluemap.atmons.integration;

import java.util.regex.Pattern;

/** Minecraft identifier checks that remain usable in plain JVM tests. */
final class ResourceIds {
    private static final Pattern RESOURCE_LOCATION = Pattern.compile(
            "[a-z0-9_.-]+:[a-z0-9/._-]+"
    );

    private ResourceIds() {
    }

    static boolean isValid(String value) {
        return value != null && RESOURCE_LOCATION.matcher(value).matches();
    }
}
