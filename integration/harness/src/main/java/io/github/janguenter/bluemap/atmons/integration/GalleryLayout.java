package io.github.janguenter.bluemap.atmons.integration;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Composer and operator gallery layouts used only for BlueMap markers. */
public final class GalleryLayout {
    public int schemaVersion;
    public String compositionId;
    public String composerVersion;

    // Aggregated composer format.
    public String dimension;
    public String mapId;
    public Geometry.BlockBounds bounds;
    public List<Gallery> galleries = List.of();

    // Small operator-authored extension format.
    public List<Area> areas = List.of();
    public List<Point> points = List.of();

    public static final class Gallery {
        public String id;
        public String repository;
        public String commit;
        public String namespace;
        public String surface;
        public Geometry.BlockBounds bounds;
        public Geometry.BlockBounds tileBounds;
        public Marker marker;
        public Functions functions;
        public Completion completion;
    }

    public static final class Completion {
        public String mode;
        public String objective;
        public String player;
        public Integer delayTicks;
        public Integer timeoutTicks;

        void validate(String galleryId) {
            if (!"bma_done".equals(objective)
                    || player == null
                    || !player.matches("#[a-z0-9_]{1,39}")) {
                throw new IllegalArgumentException(
                        "Invalid gallery completion score for " + galleryId
                );
            }
            if ("scheduled-game-tick-barrier".equals(mode)) {
                if (delayTicks == null || delayTicks < 1 || timeoutTicks != null) {
                    throw new IllegalArgumentException(
                            "Invalid scheduled gallery completion for " + galleryId
                    );
                }
            } else if ("terminal-predicate".equals(mode)) {
                if (delayTicks != null || timeoutTicks == null || timeoutTicks < 1) {
                    throw new IllegalArgumentException(
                            "Invalid predicate gallery completion for " + galleryId
                    );
                }
            } else {
                throw new IllegalArgumentException(
                        "Invalid gallery completion mode for " + galleryId
                );
            }
        }
    }

    public static final class Marker {
        public String id;
        public String label;
        public Position position;
    }

    public static final class Functions {
        public String load;
        public String prepare;
        public String build;
        public String verify;
        public String release;
        public String clear;

        void validate(String galleryId) {
            for (String function : new String[]{load, prepare, build, verify, release, clear}) {
                if (!ResourceIds.isValid(function)) {
                    throw new IllegalArgumentException(
                            "Invalid gallery function for " + galleryId + ": " + function
                    );
                }
            }
        }
    }

    public static final class Area {
        public String id;
        public String addonId;
        public String label;
        public String detail = "";
        public String dimension;
        public String color = "#4da3ff";
        public Geometry.BlockBounds bounds;
    }

    public static final class Point {
        public String id;
        public String addonId;
        public String label;
        public String detail = "";
        public String dimension;
        public Position position;
    }

    public record Position(double x, double y, double z) {
        public Position {
            if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) {
                throw new IllegalArgumentException("Gallery position must be finite");
            }
        }
    }

    public void validate() {
        if (schemaVersion != 1) {
            throw new IllegalArgumentException("Unsupported gallery schemaVersion: " + schemaVersion);
        }
        if (galleries == null || areas == null || points == null) {
            throw new IllegalArgumentException("Gallery marker collections are required arrays");
        }
        if (galleries.isEmpty() && areas.isEmpty() && points.isEmpty()) {
            throw new IllegalArgumentException("Gallery layout has no markers");
        }

        Set<String> ids = new HashSet<>();
        if (!galleries.isEmpty()) {
            if (compositionId == null || !compositionId.matches("[0-9a-f]{64}")
                    || !"2.4.0".equals(composerVersion)) {
                throw new IllegalArgumentException(
                        "Composer gallery composition identity is invalid"
                );
            }
            if (!ResourceIds.isValid(dimension) || bounds == null) {
                throw new IllegalArgumentException(
                        "Composer gallery dimension and bounds are required"
                );
            }
            if (mapId == null || !mapId.matches("[a-z0-9][a-z0-9_]{0,127}")) {
                throw new IllegalArgumentException("Composer gallery mapId is not BlueMap-safe");
            }
            for (Gallery gallery : galleries) {
                validateIdentifier(gallery.id);
                if (gallery.bounds == null || gallery.tileBounds == null || gallery.marker == null) {
                    throw new IllegalArgumentException(
                            "Gallery bounds, tileBounds, and marker are required: " + gallery.id
                    );
                }
                validateIdentifier(gallery.marker.id);
                if (!ids.add("gallery_area_" + gallery.id)
                        || !ids.add("gallery_poi_" + gallery.marker.id)) {
                    throw new IllegalArgumentException(
                            "Duplicate gallery marker id: " + gallery.id
                    );
                }
                validateLabel(gallery.marker.label, gallery.marker.id);
                if (gallery.marker.position == null) {
                    throw new IllegalArgumentException(
                            "Gallery marker position is required: " + gallery.id
                    );
                }
                if (gallery.functions != null) {
                    gallery.functions.validate(gallery.id);
                } else {
                    throw new IllegalArgumentException(
                            "Gallery functions are required: " + gallery.id
                    );
                }
                if (gallery.completion == null) {
                    throw new IllegalArgumentException(
                            "Gallery completion is required: " + gallery.id
                    );
                }
                gallery.completion.validate(gallery.id);
            }
        }

        for (Area area : areas) {
            validateCommon(area.id, area.addonId, area.label, area.dimension, ids);
            if (area.bounds == null) {
                throw new IllegalArgumentException("Gallery area bounds are required: " + area.id);
            }
            parseColor(area.color);
        }
        for (Point point : points) {
            validateCommon(point.id, point.addonId, point.label, point.dimension, ids);
            if (point.position == null) {
                throw new IllegalArgumentException("Gallery point position is required: " + point.id);
            }
        }
    }

    String preferredMapId(String markerDimension) {
        if (!galleries.isEmpty() && dimension.equals(markerDimension)) {
            return mapId;
        }
        return BlueMapMapContract.safeMapId(markerDimension);
    }

    static int parseColor(String color) {
        if (color == null || !color.matches("#[0-9a-fA-F]{6}")) {
            throw new IllegalArgumentException("Gallery color must use #RRGGBB");
        }
        return Integer.parseUnsignedInt(color.substring(1), 16);
    }

    private static void validateCommon(
            String id,
            String addonId,
            String label,
            String markerDimension,
            Set<String> ids
    ) {
        validateId(id, ids);
        if (addonId == null || !addonId.matches("[a-z0-9][a-z0-9._-]{0,127}")) {
            throw new IllegalArgumentException("Invalid gallery addonId: " + addonId);
        }
        validateLabel(label, id);
        if (!ResourceIds.isValid(markerDimension)) {
            throw new IllegalArgumentException("Invalid gallery dimension: " + markerDimension);
        }
    }

    private static void validateId(String id, Set<String> ids) {
        validateIdentifier(id);
        if (!ids.add(id)) {
            throw new IllegalArgumentException("Invalid or duplicate gallery id: " + id);
        }
    }

    private static void validateIdentifier(String id) {
        if (id == null || !id.matches("[a-z0-9][a-z0-9._-]{0,127}")) {
            throw new IllegalArgumentException("Invalid gallery id: " + id);
        }
    }

    private static void validateLabel(String label, String id) {
        if (label == null || label.isBlank() || label.length() > 256) {
            throw new IllegalArgumentException("Invalid gallery label: " + id);
        }
    }
}
