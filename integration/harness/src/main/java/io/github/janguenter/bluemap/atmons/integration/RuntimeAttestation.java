package io.github.janguenter.bluemap.atmons.integration;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Stream;
import net.minecraft.SharedConstants;
import net.neoforged.fml.ModList;

/** External bootstrap evidence bound to every structure catalog. */
final class RuntimeAttestation {
    private static final String PACK_COMMIT =
            "c7bb230f21d14d26859d0b92548f089b3a493ad9";
    private static final String SERVER_ARCHIVE_SHA256 =
            "de112ed8d79b3ff027e399a5108b706f6a2db3be74b15d0db6f6b9d6ac268e6c";
    private static final Path RUNTIME_MODS_DIRECTORY = Path.of("/data/mods");
    private static final Path CANDIDATE_PACKS_DIRECTORY = Path.of(
            "/data/config/bluemap/packs"
    );
    private static final Map<String, ExpectedBootstrapJar> EXPECTED_BOOTSTRAP_JARS = Map.of(
            "CrashAssistant-neoforge-1.20.6-1.21.4-1.11.11.jar",
            new ExpectedBootstrapJar(
                    3_187_440L,
                    "db1c4fe176bec97268cfed87488c2040f408dbdf024b5173847ed1e39b0f2dd6"
            ),
            "ScalableCatsForce-NeoForge-3.7.1-build-11-with-library.jar",
            new ExpectedBootstrapJar(
                    16_872_119L,
                    "48cc7a8b4448d539aa7f4b56ae899b1484ec40ed8481af56818416726ee01193"
            ),
            "kotlinforforge-5.12.0-all.jar",
            new ExpectedBootstrapJar(
                    7_279_276L,
                    "095aed94f21b4e55895b21ea957750ae3ab829fbcfc6d3c66a3489f5f1128d46"
            )
    );
    private static volatile ObservedModInventory observedModInventory;

    int schemaVersion;
    String atmons;
    String packCommit;
    String minecraft;
    String neoforge;
    String bluemapVersion;
    String bluemapCommit;
    String bluemapJarSha256;
    String candidateManifestSha256;
    String galleryCompositionId;
    String galleryCompositionManifestSha256;
    String galleryLayoutSha256;
    String galleryDatapackSha256;
    String runtimeJarInventorySha256;
    int runtimeJarCount;
    String runtimeModsDirectory;
    String baseRuntimeInventorySha256;
    int baseRuntimeJarCount;
    String candidatePackInventorySha256;
    int candidatePackCount;
    String candidatePacksDirectory;
    String serverArchiveSha256;
    long serverArchiveSizeBytes;

    static Loaded load(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        RuntimeAttestation value = JsonFiles.GSON.fromJson(
                new String(bytes, java.nio.charset.StandardCharsets.UTF_8),
                RuntimeAttestation.class
        );
        if (value == null) {
            throw new IllegalArgumentException("Runtime attestation is null");
        }
        value.validateObservedRuntime();
        return new Loaded(value, sha256(bytes));
    }

    private void validateObservedRuntime() {
        String observedMinecraft = SharedConstants.getCurrentVersion().getName();
        String observedNeoForge = ModList.get()
                .getModContainerById("neoforge")
                .orElseThrow(() -> new IllegalArgumentException("NeoForge mod is absent"))
                .getModInfo().getVersion().toString();
        if (schemaVersion != 1
                || !"1.2.0".equals(atmons)
                || !PACK_COMMIT.equals(packCommit)
                || !"1.21.1".equals(minecraft)
                || !minecraft.equals(observedMinecraft)
                || !"21.1.248".equals(neoforge)
                || !neoforge.equals(observedNeoForge)
                || !hex(bluemapCommit, 40)
                || bluemapVersion == null || bluemapVersion.isBlank()
                || !hex(bluemapJarSha256, 64)
                || !hex(candidateManifestSha256, 64)
                || !hex(galleryCompositionId, 64)
                || !hex(galleryCompositionManifestSha256, 64)
                || !hex(galleryLayoutSha256, 64)
                || !hex(galleryDatapackSha256, 64)
                || !hex(runtimeJarInventorySha256, 64)
                || runtimeJarCount != 377
                || !RUNTIME_MODS_DIRECTORY.toString().equals(runtimeModsDirectory)
                || !hex(baseRuntimeInventorySha256, 64)
                || baseRuntimeJarCount != 375
                || !hex(candidatePackInventorySha256, 64)
                || candidatePackCount != 51
                || !CANDIDATE_PACKS_DIRECTORY.toString().equals(
                        candidatePacksDirectory
                )
                || !SERVER_ARCHIVE_SHA256.equals(serverArchiveSha256)
                || serverArchiveSizeBytes != 1_055_896_389L) {
            throw new IllegalArgumentException(
                    "Runtime attestation does not match the exact observed ATMons baseline"
            );
        }
        ObservedModInventory observed = observedRuntimeMods();
        if (observed.count() != runtimeJarCount
                || !observed.sha256().equals(runtimeJarInventorySha256)) {
            throw new IllegalArgumentException(
                    "NeoForge loaded-file inventory does not match runtime attestation"
            );
        }
    }

    private static ObservedModInventory observedRuntimeMods() {
        ObservedModInventory cached = observedModInventory;
        if (cached != null) {
            return cached;
        }
        synchronized (RuntimeAttestation.class) {
            cached = observedModInventory;
            if (cached != null) {
                return cached;
            }
            try {
                Path directory = RUNTIME_MODS_DIRECTORY.toAbsolutePath().normalize();
                TreeMap<String, Path> diskFiles = new TreeMap<>();
                try (Stream<Path> entries = Files.list(directory)) {
                    entries.filter(Files::isRegularFile)
                            .filter(path -> path.getFileName().toString().endsWith(".jar"))
                            .forEach(path -> diskFiles.put(
                                    path.getFileName().toString(),
                                    path.toAbsolutePath().normalize()
                            ));
                }
                Set<String> loadedFiles = new HashSet<>();
                ModList.get().getModFiles().forEach(fileInfo -> {
                    Path path = fileInfo.getFile().getFilePath().toAbsolutePath().normalize();
                    if (directory.equals(path.getParent())) {
                        loadedFiles.add(path.getFileName().toString());
                    }
                });
                if (!diskFiles.keySet().containsAll(EXPECTED_BOOTSTRAP_JARS.keySet())) {
                    throw new IllegalArgumentException(
                            "Exact ATMons bootstrap JAR set is incomplete"
                    );
                }
                Set<String> expectedLoadedFiles = new HashSet<>(diskFiles.keySet());
                expectedLoadedFiles.removeAll(EXPECTED_BOOTSTRAP_JARS.keySet());
                if (!loadedFiles.equals(expectedLoadedFiles)) {
                    Set<String> notLoaded = new HashSet<>(expectedLoadedFiles);
                    notLoaded.removeAll(loadedFiles);
                    Set<String> notOnDisk = new HashSet<>(loadedFiles);
                    notOnDisk.removeAll(expectedLoadedFiles);
                    throw new IllegalArgumentException(
                            "Runtime mods directory and expected NeoForge mod files differ; "
                                    + "notLoaded="
                                    + notLoaded + ", notOnDisk=" + notOnDisk
                    );
                }
                MessageDigest inventoryDigest = MessageDigest.getInstance("SHA-256");
                for (var entry : diskFiles.entrySet()) {
                    Path path = entry.getValue();
                    long size = Files.size(path);
                    String fileSha256 = sha256(path);
                    ExpectedBootstrapJar bootstrap = EXPECTED_BOOTSTRAP_JARS.get(
                            entry.getKey()
                    );
                    if (bootstrap != null && (bootstrap.sizeBytes() != size
                            || !bootstrap.sha256().equals(fileSha256))) {
                        throw new IllegalArgumentException(
                                "Exact ATMons bootstrap JAR differs: " + entry.getKey()
                        );
                    }
                    String row = entry.getKey() + "\t" + size + "\t"
                            + fileSha256 + "\n";
                    inventoryDigest.update(row.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                }
                cached = new ObservedModInventory(
                        diskFiles.size(),
                        java.util.HexFormat.of().formatHex(inventoryDigest.digest())
                );
                observedModInventory = cached;
                return cached;
            } catch (IOException | NoSuchAlgorithmException exception) {
                throw new IllegalArgumentException(
                        "Could not attest NeoForge loaded files", exception
                );
            }
        }
    }

    private static boolean hex(String value, int length) {
        return value != null && value.matches("[0-9a-f]{" + length + "}");
    }

    static String sha256(byte[] input) {
        try {
            return java.util.HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(input)
            );
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }

    private static String sha256(Path path) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (var input = Files.newInputStream(path)) {
                byte[] buffer = new byte[1024 * 1024];
                for (int read = input.read(buffer); read >= 0; read = input.read(buffer)) {
                    if (read > 0) {
                        digest.update(buffer, 0, read);
                    }
                }
            }
            return java.util.HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }

    private record ObservedModInventory(int count, String sha256) {
    }

    private record ExpectedBootstrapJar(long sizeBytes, String sha256) {
    }

    record Loaded(RuntimeAttestation value, String sha256) {
    }
}
