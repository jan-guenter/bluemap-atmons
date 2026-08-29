package io.github.janguenter.bluemap.atmons.integration;

import java.util.ArrayList;
import java.util.List;

/** Generated BlueMap render-mask source, grouped by dimension. */
final class RenderMasks {
    int schemaVersion = 1;
    String worldIdentity;
    String planFingerprint;
    String runtimeAttestationSha256;
    List<DimensionMasks> dimensions = new ArrayList<>();

    static final class DimensionMasks {
        String dimension;
        List<Mask> renderMask = new ArrayList<>();
    }

    record Mask(int minX, int maxX, int minZ, int maxZ, int minY, int maxY) {
    }
}
