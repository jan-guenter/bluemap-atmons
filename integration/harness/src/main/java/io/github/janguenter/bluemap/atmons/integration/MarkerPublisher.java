package io.github.janguenter.bluemap.atmons.integration;

import com.flowpowered.math.vector.Vector2i;
import com.flowpowered.math.vector.Vector3d;
import de.bluecolored.bluemap.api.BlueMapAPI;
import de.bluecolored.bluemap.api.BlueMapMap;
import de.bluecolored.bluemap.api.BlueMapWorld;
import de.bluecolored.bluemap.api.markers.ExtrudeMarker;
import de.bluecolored.bluemap.api.markers.MarkerSet;
import de.bluecolored.bluemap.api.markers.POIMarker;
import de.bluecolored.bluemap.api.math.Color;
import de.bluecolored.bluemap.api.math.Shape;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;

/** Idempotent BlueMap marker publication and exact affected-region scheduling. */
final class MarkerPublisher {
    private final BlueMapAPI api;
    private final MinecraftServer server;
    private final HarnessConfig config;
    private final Path directory;

    MarkerPublisher(
            BlueMapAPI api,
            MinecraftServer server,
            HarnessConfig config,
            Path directory
    ) {
        this.api = api;
        this.server = server;
        this.config = config;
        this.directory = directory;
    }

    void publishExisting() throws IOException {
        if (Files.isRegularFile(galleryPath())) {
            publishGalleries();
        }
    }

    IntegrationController.ActionResult publishStructures() throws IOException {
        StructureCatalog catalog = JsonFiles.read(catalogPath(), StructureCatalog.class);
        new StructureCatalogService(server, config, directory).validateLiveCatalog(catalog);
        validateStructureMaps(catalog);
        Map<String, MarkerSet> sets = new HashMap<>();
        int markers = 0;
        for (StructureCatalog.StructureEntry entry : catalog.structures) {
            StructureCatalog.Selection selection = entry.selection;
            if (!"located".equals(selection.status)) {
                continue;
            }
            MarkerSet set = sets.computeIfAbsent(
                    selection.dimension,
                    ignored -> MarkerSet.builder()
                            .label("ATMons world structures")
                            .toggleable(true)
                            .defaultHidden(false)
                            .sorting(10)
                            .build()
            );
            Geometry.BlockBounds bounds = selection.borderedBounds;
            String detail = "<strong>" + html(entry.id) + "</strong><br>"
                    + "Dimension: " + html(selection.dimension) + "<br>"
                    + "Structure BB: " + html(boundsText(selection.structureBounds)) + "<br>"
                    + "Four-block border: " + html(boundsText(bounds));
            ExtrudeMarker marker = ExtrudeMarker.builder()
                    .label(entry.id)
                    .detail(detail)
                    .shape(
                            Shape.createRect(
                                    bounds.minX(), bounds.minZ(),
                                    (double) bounds.maxX() + 1.0D,
                                    (double) bounds.maxZ() + 1.0D
                            ),
                            bounds.minY(),
                            (float) bounds.maxY() + 1.0F
                    )
                    .lineWidth(2)
                    .lineColor(new Color(255, 170, 0, 0.9F))
                    .fillColor(new Color(255, 170, 0, 0.08F))
                    .build();
            set.put(selection.markerId, marker);
            markers++;
        }

        Map<String, String> expectedMapIds = new HashMap<>();
        sets.keySet().forEach(dimension -> expectedMapIds.put(
                dimension,
                BlueMapMapContract.safeMapId(dimension)
        ));
        Publication publication = publishSets(
                config.structureMarkerSetId,
                sets,
                expectedMapIds
        );
        if (!publication.missingDimensions().isEmpty()) {
            return IntegrationController.ActionResult.failure(
                    "Missing required BlueMap configs/maps for dimensions: "
                            + String.join(", ", publication.missingDimensions())
            );
        }
        return IntegrationController.ActionResult.success(
                "Published " + markers + " structure markers to "
                        + publication.maps() + " maps",
                markers
        );
    }

    IntegrationController.ActionResult publishGalleries() throws IOException {
        GalleryLayout layout = loadAttestedGallery().layout();
        Map<String, MarkerSet> sets = new HashMap<>();
        Map<String, String> expectedMapIds = new HashMap<>();
        int markers = 0;

        for (GalleryLayout.Gallery gallery : layout.galleries) {
            MarkerSet set = gallerySet(sets, layout.dimension);
            int rgb = GalleryLayout.parseColor("#4da3ff");
            String detail = "<strong>" + html(gallery.marker.label) + "</strong><br>"
                    + "Add-on: " + html(gallery.id)
                    + detailSuffix(gallery.repository)
                    + detailSuffix(gallery.commit);
            Geometry.BlockBounds bounds = gallery.bounds;
            set.put("gallery_area_" + gallery.id, ExtrudeMarker.builder()
                    .label(gallery.marker.label)
                    .detail(detail)
                    .shape(
                            Shape.createRect(
                                    bounds.minX(), bounds.minZ(),
                                    (double) bounds.maxX() + 1.0D,
                                    (double) bounds.maxZ() + 1.0D
                            ),
                            bounds.minY(),
                            (float) bounds.maxY() + 1.0F
                    )
                    .lineWidth(2)
                    .lineColor(new Color(rgb, 0.95F))
                    .fillColor(new Color(rgb, 0.08F))
                    .build());
            set.put("gallery_poi_" + gallery.marker.id, POIMarker.builder()
                    .label(gallery.marker.label)
                    .detail(detail)
                    .position(new Vector3d(
                            gallery.marker.position.x(),
                            gallery.marker.position.y(),
                            gallery.marker.position.z()
                    ))
                    .build());
            expectedMapIds.put(layout.dimension, layout.mapId);
            markers += 2;
        }

        for (GalleryLayout.Area area : layout.areas) {
            MarkerSet set = gallerySet(sets, area.dimension);
            expectedMapIds.put(area.dimension, layout.preferredMapId(area.dimension));
            Geometry.BlockBounds bounds = area.bounds;
            int rgb = GalleryLayout.parseColor(area.color);
            String detail = "<strong>" + html(area.label) + "</strong><br>"
                    + "Add-on: " + html(area.addonId)
                    + detailSuffix(area.detail);
            set.put(area.id, ExtrudeMarker.builder()
                    .label(area.label)
                    .detail(detail)
                    .shape(
                            Shape.createRect(
                                    bounds.minX(), bounds.minZ(),
                                    (double) bounds.maxX() + 1.0D,
                                    (double) bounds.maxZ() + 1.0D
                            ),
                            bounds.minY(),
                            (float) bounds.maxY() + 1.0F
                    )
                    .lineWidth(2)
                    .lineColor(new Color(rgb, 0.95F))
                    .fillColor(new Color(rgb, 0.08F))
                    .build());
            markers++;
        }

        for (GalleryLayout.Point point : layout.points) {
            MarkerSet set = gallerySet(sets, point.dimension);
            expectedMapIds.put(point.dimension, layout.preferredMapId(point.dimension));
            String detail = "<strong>" + html(point.label) + "</strong><br>"
                    + "Add-on: " + html(point.addonId)
                    + detailSuffix(point.detail);
            set.put(point.id, POIMarker.builder()
                    .label(point.label)
                    .detail(detail)
                    .position(new Vector3d(
                            point.position.x(),
                            point.position.y(),
                            point.position.z()
                    ))
                    .build());
            markers++;
        }

        Publication publication = publishSets(
                config.galleryMarkerSetId,
                sets,
                expectedMapIds
        );
        if (!publication.missingDimensions().isEmpty()) {
            return IntegrationController.ActionResult.failure(
                    "Missing required BlueMap configs/maps for gallery dimensions: "
                            + String.join(", ", publication.missingDimensions())
            );
        }
        return IntegrationController.ActionResult.success(
                "Published " + markers + " gallery markers to "
                        + publication.maps() + " maps",
                markers
        );
    }

    IntegrationController.ActionResult scheduleGalleryRender()
            throws IOException, ReflectiveOperationException {
        Files.deleteIfExists(directory.resolve(GalleryRenderSchedule.FILE_NAME));
        AttestedGallery attested = loadAttestedGallery();
        GalleryLayout layout = attested.layout();
        GalleryRenderVerifier.requireComposerLayout(layout);
        requireExactGalleryCount(attested);
        RuntimeIdentity identity = loadGalleryRuntimeIdentity(attested.attestation());
        Map<String, Set<Vector2i>> regions = GalleryRenderVerifier.exactRegions(layout);
        BlueMapMap map = exactGalleryMap(layout);
        Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles =
                GalleryRenderVerifier.expectedTiles(layout, map);

        var renderManager = api.getRenderManager();
        if (!renderManager.isRunning()) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap gallery render threads are stopped"
            );
        }
        if (renderManager.renderQueueSize() != 0) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap gallery render queue is not idle"
            );
        }
        Map<String, BlueMapMap> maps = Map.of(GalleryRenderVerifier.MAP_ID, map);
        Map<String, Long> previousRegionStates =
                StructureRenderVerifier.regionUpdateSeconds(maps, regions);
        long previousRegionMaximum = previousRegionStates.values().stream()
                .mapToLong(Long::longValue).max().orElse(-1L);
        long requiredEpochMillis;
        try {
            requiredEpochMillis = Math.multiplyExact(
                    Math.addExact(previousRegionMaximum, 1L), 1000L
            );
        } catch (ArithmeticException exception) {
            throw new IllegalArgumentException(
                    "Existing BlueMap gallery region timestamps are invalid", exception
            );
        }
        long delay = requiredEpochMillis - System.currentTimeMillis();
        if (delay > 2000L) {
            return IntegrationController.ActionResult.failure(
                    "Existing BlueMap gallery region timestamps are too far ahead "
                            + "of the server clock"
            );
        }
        if (delay > 0L) {
            try {
                Thread.sleep(delay);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                return IntegrationController.ActionResult.failure(
                        "Interrupted while separating the exact gallery render epoch"
                );
            }
        }
        long scheduledAtEpochMillis = System.currentTimeMillis();
        if (Math.floorDiv(scheduledAtEpochMillis, 1000L) <= previousRegionMaximum) {
            return IntegrationController.ActionResult.failure(
                    "Could not separate the exact gallery render epoch from prior region state"
            );
        }
        if (!renderManager.scheduleMapUpdateTask(
                map, regions.get(GalleryRenderVerifier.MAP_ID), true
        )) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap rejected the exact atmons_integration gallery render task"
            );
        }
        GalleryRenderSchedule schedule = GalleryRenderSchedule.create(
                scheduledAtEpochMillis,
                galleryPath(),
                layout,
                identity,
                regions,
                tiles,
                previousRegionStates
        );
        JsonFiles.writeAtomic(
                directory.resolve(GalleryRenderSchedule.FILE_NAME), schedule
        );
        int regionCount = regions.get(GalleryRenderVerifier.MAP_ID).size();
        return IntegrationController.ActionResult.success(
                "Queued exact BlueMap gallery render for atmons_integration covering "
                        + regionCount + " regions; completion and storage output remain pending",
                regionCount
        );
    }

    IntegrationController.ActionResult verifyGalleryRender()
            throws IOException, ReflectiveOperationException {
        AttestedGallery attested = loadAttestedGallery();
        GalleryLayout layout = attested.layout();
        GalleryRenderVerifier.requireComposerLayout(layout);
        requireExactGalleryCount(attested);
        RuntimeIdentity identity = loadGalleryRuntimeIdentity(attested.attestation());
        Map<String, Set<Vector2i>> regions = GalleryRenderVerifier.exactRegions(layout);
        BlueMapMap map = exactGalleryMap(layout);
        Map<String, TreeSet<StructureRenderVerifier.TileCoordinate>> tiles =
                GalleryRenderVerifier.expectedTiles(layout, map);
        GalleryRenderSchedule schedule = GalleryRenderSchedule.loadAndValidate(
                directory, galleryPath(), layout, identity, regions, tiles
        );
        var renderManager = api.getRenderManager();
        if (!renderManager.isRunning() || renderManager.renderQueueSize() != 0) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap gallery renderer is not running and idle"
            );
        }
        StructureRenderVerifier.Result result = GalleryRenderVerifier.verify(
                layout, map, schedule, regions
        );
        if (result.tileCount() > Integer.MAX_VALUE) {
            return IntegrationController.ActionResult.failure(
                    "Rendered gallery tile count exceeds the command result range"
            );
        }
        return IntegrationController.ActionResult.success(
                "Verified " + result.tileCount()
                        + " freshly rendered gallery tiles for atmons_integration across "
                        + result.regionCount() + " regions; evidenceSha256="
                        + result.evidenceSha256(),
                (int) result.tileCount()
        );
    }

    IntegrationController.ActionResult scheduleStructureRenders()
            throws IOException, ReflectiveOperationException {
        Files.deleteIfExists(directory.resolve(StructureRenderSchedule.FILE_NAME));
        StructureCatalog catalog = JsonFiles.read(catalogPath(), StructureCatalog.class);
        new StructureCatalogService(server, config, directory).validateLiveCatalog(catalog);
        StructureMapManifest manifest = validateStructureMaps(catalog);
        Map<String, Set<Vector2i>> regions = exactRegions(catalog);

        var renderManager = api.getRenderManager();
        if (!renderManager.isRunning()) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap render threads are stopped"
            );
        }
        if (renderManager.renderQueueSize() != 0) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap render queue is not idle; refusing ambiguous region coverage"
            );
        }
        Map<String, BlueMapMap> maps = exactMaps(regions.keySet());
        if (maps.size() != regions.size()) {
            Set<String> missing = new java.util.TreeSet<>(regions.keySet());
            missing.removeAll(maps.keySet());
            return IntegrationController.ActionResult.failure(
                    "Missing required BlueMap configs/maps for render dimensions: "
                            + String.join(", ", missing)
            );
        }
        RuntimeIdentity identity = JsonFiles.read(
                directory.resolve(RuntimeIdentity.FILE_NAME), RuntimeIdentity.class
        );
        identity.validate();
        Map<String, Long> previousRegionStates =
                StructureRenderVerifier.regionUpdateSeconds(maps, regions);
        long previousRegionMaximum = previousRegionStates.values().stream()
                .mapToLong(Long::longValue).max().orElse(-1L);
        long requiredEpochMillis = Math.multiplyExact(
                Math.addExact(previousRegionMaximum, 1L), 1000L
        );
        long delay = requiredEpochMillis - System.currentTimeMillis();
        if (delay > 2000L) {
            return IntegrationController.ActionResult.failure(
                    "Existing BlueMap region timestamps are too far ahead of the server clock"
            );
        }
        if (delay > 0L) {
            try {
                Thread.sleep(delay);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                return IntegrationController.ActionResult.failure(
                        "Interrupted while separating the exact render epoch"
                );
            }
        }
        long scheduledAtEpochMillis = System.currentTimeMillis();
        if (Math.floorDiv(scheduledAtEpochMillis, 1000L) <= previousRegionMaximum) {
            return IntegrationController.ActionResult.failure(
                    "Could not separate the exact render epoch from prior region state"
            );
        }
        int scheduled = 0;
        for (Map.Entry<String, Set<Vector2i>> entry : regions.entrySet()) {
            BlueMapMap map = maps.get(entry.getKey());
            if (renderManager.scheduleMapUpdateTask(
                    map,
                    entry.getValue(),
                    true
            )) {
                scheduled++;
            } else {
                return IntegrationController.ActionResult.failure(
                        "BlueMap rejected exact region-update task for map "
                                + map.getId() + " after " + scheduled + " queued tasks"
                );
            }
        }
        StructureRenderSchedule schedule = StructureRenderSchedule.create(
                scheduledAtEpochMillis,
                catalogPath(),
                mapManifestPath(),
                catalog,
                manifest,
                identity,
                regions,
                previousRegionStates
        );
        JsonFiles.writeAtomic(
                directory.resolve(StructureRenderSchedule.FILE_NAME), schedule
        );
        return IntegrationController.ActionResult.success(
                "Queued " + scheduled + " exact BlueMap region-update tasks; "
                        + "completion and storage output remain pending",
                scheduled
        );
    }

    IntegrationController.ActionResult verifyStructureRenders()
            throws IOException, ReflectiveOperationException {
        StructureCatalog catalog = JsonFiles.read(catalogPath(), StructureCatalog.class);
        new StructureCatalogService(server, config, directory).validateLiveCatalog(catalog);
        StructureMapManifest manifest = validateStructureMaps(catalog);
        Map<String, Set<Vector2i>> regions = exactRegions(catalog);
        RuntimeIdentity identity = JsonFiles.read(
                directory.resolve(RuntimeIdentity.FILE_NAME), RuntimeIdentity.class
        );
        identity.validate();
        StructureRenderSchedule schedule = StructureRenderSchedule.loadAndValidate(
                directory,
                catalogPath(),
                mapManifestPath(),
                catalog,
                manifest,
                identity,
                regions
        );
        var renderManager = api.getRenderManager();
        if (!renderManager.isRunning() || renderManager.renderQueueSize() != 0) {
            return IntegrationController.ActionResult.failure(
                    "BlueMap renderer is not running and idle"
            );
        }
        Map<String, BlueMapMap> maps = exactMaps(regions.keySet());
        if (maps.size() != regions.size()) {
            Set<String> missing = new java.util.TreeSet<>(regions.keySet());
            missing.removeAll(maps.keySet());
            return IntegrationController.ActionResult.failure(
                    "Missing required BlueMap configs/maps for render dimensions: "
                            + String.join(", ", missing)
            );
        }
        StructureRenderVerifier.Result result = StructureRenderVerifier.verify(
                catalog, maps, schedule, regions
        );
        if (result.tileCount() > Integer.MAX_VALUE) {
            return IntegrationController.ActionResult.failure(
                    "Rendered structure tile count exceeds the command result range"
            );
        }
        return IntegrationController.ActionResult.success(
                "Verified " + result.tileCount()
                        + " freshly rendered structure tiles across "
                        + result.mapCount() + " maps; evidenceSha256="
                        + result.evidenceSha256(),
                (int) result.tileCount()
        );
    }

    private Publication publishSets(
            String markerSetId,
            Map<String, MarkerSet> sets,
            Map<String, String> expectedMapIds
    ) {
        int maps = 0;
        List<String> missingDimensions = new java.util.ArrayList<>();
        for (Map.Entry<String, MarkerSet> entry : sets.entrySet()) {
            ServerLevel level = level(entry.getKey());
            if (level == null) {
                missingDimensions.add(entry.getKey());
                continue;
            }
            BlueMapWorld world = api.getWorld(level).orElse(null);
            if (world == null) {
                missingDimensions.add(entry.getKey());
                continue;
            }
            BlueMapMap map = expectedMap(world, expectedMapIds.get(entry.getKey()));
            if (map == null) {
                missingDimensions.add(entry.getKey());
                continue;
            }
            map.getMarkerSets().put(markerSetId, entry.getValue());
            maps++;
        }
        return new Publication(maps, List.copyOf(missingDimensions));
    }

    private AttestedGallery loadAttestedGallery() throws IOException {
        byte[] layoutBytes = Files.readAllBytes(galleryPath());
        GalleryLayout layout = JsonFiles.read(
                layoutBytes, GalleryLayout.class, galleryPath()
        );
        layout.validate();
        RuntimeAttestation.Loaded attestation = RuntimeAttestation.load(
                directory.resolve(config.runtimeAttestationFile)
        );
        if (!attestation.value().galleryCompositionId.equals(layout.compositionId)
                || !attestation.value().galleryLayoutSha256.equals(
                        RuntimeAttestation.sha256(layoutBytes)
                )) {
            throw new IllegalArgumentException(
                    "Gallery layout bytes do not match the runtime-attested composition"
            );
        }
        return new AttestedGallery(layout, attestation);
    }

    private static void requireExactGalleryCount(AttestedGallery attested) {
        if (attested.layout().galleries.size()
                != attested.attestation().value().candidatePackCount) {
            throw new IllegalArgumentException(
                    "Gallery layout does not contain every runtime-attested candidate"
            );
        }
    }

    private RuntimeIdentity loadGalleryRuntimeIdentity(
            RuntimeAttestation.Loaded attestation
    ) throws IOException {
        RuntimeIdentity identity = JsonFiles.read(
                directory.resolve(RuntimeIdentity.FILE_NAME), RuntimeIdentity.class
        );
        identity.validate();
        if (!identity.runtimeAttestationSha256.equals(attestation.sha256())) {
            throw new IllegalArgumentException(
                    "Gallery runtime identity does not match the live attestation"
            );
        }
        return identity;
    }

    private BlueMapMap exactGalleryMap(GalleryLayout layout) {
        ServerLevel galleryLevel = level(layout.dimension);
        if (galleryLevel == null) {
            throw new IllegalArgumentException(
                    "Gallery dimension is not loaded: " + layout.dimension
            );
        }
        BlueMapWorld galleryWorld = api.getWorld(galleryLevel).orElseThrow(
                () -> new IllegalArgumentException(
                        "BlueMap gallery world is not loaded: " + layout.dimension
                )
        );
        BlueMapMap map = expectedMap(galleryWorld, layout.mapId);
        if (map == null) {
            throw new IllegalArgumentException(
                    "Missing exact BlueMap gallery map: " + layout.mapId
            );
        }
        if (map.isFrozen()) {
            throw new IllegalArgumentException(
                    "Exact BlueMap gallery map is frozen: " + layout.mapId
            );
        }
        return map;
    }

    private StructureMapManifest validateStructureMaps(StructureCatalog catalog)
            throws IOException {
        return StructureMapManifest.loadAndValidate(
                directory,
                catalogPath(),
                directory.resolve(config.renderMasksFile),
                catalog
        );
    }

    private Map<String, Set<Vector2i>> exactRegions(StructureCatalog catalog) {
        Map<String, Set<Vector2i>> regions = new TreeMap<>();
        for (StructureCatalog.StructureEntry entry : catalog.structures) {
            StructureCatalog.Selection selection = entry.selection;
            if (!"located".equals(selection.status)) {
                continue;
            }
            Set<Vector2i> dimensionRegions = regions.computeIfAbsent(
                    selection.dimension, ignored -> new LinkedHashSet<>()
            );
            for (Geometry.RegionCoordinate region : selection.regions) {
                dimensionRegions.add(new Vector2i(region.x(), region.z()));
            }
        }
        return regions;
    }

    private Map<String, BlueMapMap> exactMaps(Set<String> dimensions) {
        Map<String, BlueMapMap> maps = new TreeMap<>();
        for (String dimension : dimensions) {
            ServerLevel level = level(dimension);
            if (level == null) {
                continue;
            }
            BlueMapWorld world = api.getWorld(level).orElse(null);
            if (world == null) {
                continue;
            }
            BlueMapMap map = expectedMap(
                    world, BlueMapMapContract.safeMapId(dimension)
            );
            if (map != null) {
                maps.put(dimension, map);
            }
        }
        return maps;
    }

    private MarkerSet gallerySet(Map<String, MarkerSet> sets, String dimension) {
        return sets.computeIfAbsent(
                dimension,
                ignored -> MarkerSet.builder()
                        .label("BlueMap add-on galleries")
                        .toggleable(true)
                        .defaultHidden(false)
                        .sorting(0)
                        .build()
        );
    }

    private static BlueMapMap expectedMap(BlueMapWorld world, String expectedId) {
        return world.getMaps().stream()
                .filter(map -> expectedId.equals(map.getId()))
                .findFirst()
                .orElse(null);
    }

    private ServerLevel level(String dimension) {
        ResourceLocation id = ResourceLocation.tryParse(dimension);
        if (id == null) {
            return null;
        }
        ResourceKey<Level> key = ResourceKey.create(Registries.DIMENSION, id);
        return server.getLevel(key);
    }

    private Path catalogPath() {
        return directory.resolve(config.catalogFile);
    }

    private Path galleryPath() {
        return directory.resolve(config.galleryLayoutFile);
    }

    private Path mapManifestPath() {
        return directory.getParent().resolve("bluemap")
                .resolve(StructureMapManifest.FILE_NAME).normalize();
    }

    private static String boundsText(Geometry.BlockBounds bounds) {
        return "[" + bounds.minX() + "," + bounds.minY() + "," + bounds.minZ()
                + "]..[" + bounds.maxX() + "," + bounds.maxY() + ","
                + bounds.maxZ() + "]";
    }

    private static String detailSuffix(String detail) {
        return detail == null || detail.isBlank() ? "" : "<br>" + html(detail);
    }

    private static String html(String input) {
        if (input == null) {
            return "";
        }
        return input.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }

    private record AttestedGallery(
            GalleryLayout layout,
            RuntimeAttestation.Loaded attestation
    ) {
    }

    private record Publication(int maps, List<String> missingDimensions) {
    }
}
