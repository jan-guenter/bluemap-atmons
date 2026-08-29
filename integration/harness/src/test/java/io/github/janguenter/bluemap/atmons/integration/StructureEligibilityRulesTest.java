package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class StructureEligibilityRulesTest {
    private static final String DUNGEONS_DISABLED = """
            ["YUNG's Better Dungeons"."Small Nether Dungeons"]
            "Enable Small Nether Dungeons" = false
            """;
    private static final String DUNGEONS_ENABLED = """
            ["YUNG's Better Dungeons"."Small Nether Dungeons"]
            "Enable Small Nether Dungeons" = true
            """;
    private static final String MINESHAFTS_DISABLED = """
            ["YUNG's Better Mineshafts"]
            "Disable Vanilla Mineshafts" = true
            """;
    private static final String MINESHAFTS_ENABLED = """
            ["YUNG's Better Mineshafts"]
            "Disable Vanilla Mineshafts" = false
            """;

    @TempDir
    Path temporary;

    private Path configRoot;

    @BeforeEach
    void prepareConfigs() throws IOException {
        configRoot = temporary.resolve("config");
        Files.createDirectories(configRoot);
        writeConfig(StructureEligibilityRules.BETTER_DUNGEONS, DUNGEONS_DISABLED);
        writeConfig(StructureEligibilityRules.BETTER_MINESHAFTS, MINESHAFTS_DISABLED);
    }

    @Test
    void recordsExactConfigAndLoadedModEvidenceForAllDisabledStructures()
            throws IOException {
        StructureCatalog.StructureEligibilityEvidence evidence =
                StructureEligibilityRules.load(configRoot, exactMods());

        assertEquals(2, evidence.configRules().size());
        assertEquals(1, evidence.modRules().size());
        assertEquals(
                List.of(
                        "betterdungeons:small_nether_dungeon",
                        "minecraft:mineshaft",
                        "minecraft:mineshaft_mesa",
                        "minecraft:stronghold"
                ),
                evidence.disabledStructures().stream()
                        .map(StructureCatalog.DisabledStructureEvidence::structure)
                        .toList()
        );

        StructureCatalog.StructureConfigRuleEvidence mineshafts =
                evidence.configRules().get(1);
        Path mineshaftsPath = configRoot.resolve(
                StructureEligibilityRules.BETTER_MINESHAFTS.fileName()
        );
        assertEquals(mineshaftsPath.toAbsolutePath().normalize().toString(),
                mineshafts.configPath());
        assertEquals(RuntimeAttestation.sha256(Files.readAllBytes(mineshaftsPath)),
                mineshafts.configSha256());
        assertEquals(List.of("YUNG's Better Mineshafts"), mineshafts.section());
        assertEquals("Disable Vanilla Mineshafts", mineshafts.key());
        assertEquals(true, mineshafts.value());
        assertEquals(true, mineshafts.disabledWhenValue());

        StructureCatalog.StructureModRuleEvidence strongholds =
                evidence.modRules().getFirst();
        assertEquals(StructureEligibilityRules.BETTER_STRONGHOLDS.modId(),
                strongholds.modId());
        assertEquals(StructureEligibilityRules.BETTER_STRONGHOLDS.version(),
                strongholds.version());
        assertEquals(StructureEligibilityRules.BETTER_STRONGHOLDS.jarPath(),
                strongholds.jarPath());
        assertEquals(StructureEligibilityRules.BETTER_STRONGHOLDS.jarSizeBytes(),
                strongholds.jarSizeBytes());
        assertEquals(StructureEligibilityRules.BETTER_STRONGHOLDS.jarSha256(),
                strongholds.jarSha256());
    }

    @Test
    void configValuesSelectOnlyTheRulesThatCurrentlyDisablePlacements()
            throws IOException {
        StructureCatalog.StructureEligibilityEvidence disabled =
                StructureEligibilityRules.load(configRoot, exactMods());

        writeConfig(StructureEligibilityRules.BETTER_DUNGEONS, DUNGEONS_ENABLED);
        writeConfig(StructureEligibilityRules.BETTER_MINESHAFTS, MINESHAFTS_ENABLED);
        StructureCatalog.StructureEligibilityEvidence enabled =
                StructureEligibilityRules.load(configRoot, exactMods());

        assertEquals(
                List.of("minecraft:stronghold"),
                enabled.disabledStructures().stream()
                        .map(StructureCatalog.DisabledStructureEvidence::structure)
                        .toList()
        );
        assertNotEquals(
                JsonFiles.GSON.toJson(disabled),
                JsonFiles.GSON.toJson(enabled)
        );
    }

    @Test
    void rejectsMissingRenamedSymlinkedMalformedAndNonBooleanConfigs()
            throws IOException {
        Path mineshafts = configRoot.resolve(
                StructureEligibilityRules.BETTER_MINESHAFTS.fileName()
        );
        Files.delete(mineshafts);
        assertThrows(
                IOException.class,
                () -> StructureEligibilityRules.load(configRoot, exactMods())
        );

        Path alternate = configRoot.resolve("bettermineshafts.toml");
        Files.writeString(alternate, MINESHAFTS_DISABLED);
        Files.createSymbolicLink(mineshafts, alternate);
        assertThrows(
                IOException.class,
                () -> StructureEligibilityRules.load(configRoot, exactMods())
        );
        Files.delete(mineshafts);

        List<String> rejected = List.of(
                "[\"YUNG's Better Mineshafts\"\n",
                "[\"YUNG's Better Mineshafts\"]\n",
                """
                        ["YUNG's Better Mineshafts"]
                        "Disable Vanilla Mineshafts" = "true"
                        """,
                MINESHAFTS_DISABLED + "\"Disable Vanilla Mineshafts\" = true\n"
        );
        for (String contents : rejected) {
            Files.writeString(mineshafts, contents);
            assertThrows(
                    IllegalArgumentException.class,
                    () -> StructureEligibilityRules.load(configRoot, exactMods())
            );
        }

        Files.write(mineshafts, new byte[]{(byte) 0xc3, (byte) 0x28});
        assertThrows(
                IllegalArgumentException.class,
                () -> StructureEligibilityRules.load(configRoot, exactMods())
        );
    }

    @Test
    void rejectsWrongStrongholdsVersionPathSizeAndHash() {
        StructureEligibilityRules.ObservedMod exact = exactMod();
        List<StructureEligibilityRules.ObservedMod> wrong = List.of(
                new StructureEligibilityRules.ObservedMod(
                        "5.1.3", exact.jarPath(), exact.jarSizeBytes(), exact.jarSha256()
                ),
                new StructureEligibilityRules.ObservedMod(
                        exact.version(), "/data/mods/renamed.jar",
                        exact.jarSizeBytes(), exact.jarSha256()
                ),
                new StructureEligibilityRules.ObservedMod(
                        exact.version(), exact.jarPath(),
                        exact.jarSizeBytes() + 1L, exact.jarSha256()
                ),
                new StructureEligibilityRules.ObservedMod(
                        exact.version(), exact.jarPath(), exact.jarSizeBytes(), "a".repeat(64)
                )
        );

        for (StructureEligibilityRules.ObservedMod observed : wrong) {
            assertThrows(
                    IllegalArgumentException.class,
                    () -> StructureEligibilityRules.load(
                            configRoot,
                            Map.of(StructureEligibilityRules.BETTER_STRONGHOLDS.modId(), observed)
                    )
            );
        }
    }

    private void writeConfig(
            StructureEligibilityRules.ConfigRuleSpec rule,
            String contents
    ) throws IOException {
        Files.writeString(configRoot.resolve(rule.fileName()), contents);
    }

    private static Map<String, StructureEligibilityRules.ObservedMod> exactMods() {
        return Map.of(
                StructureEligibilityRules.BETTER_STRONGHOLDS.modId(),
                exactMod()
        );
    }

    private static StructureEligibilityRules.ObservedMod exactMod() {
        StructureEligibilityRules.ModRuleSpec rule =
                StructureEligibilityRules.BETTER_STRONGHOLDS;
        return new StructureEligibilityRules.ObservedMod(
                rule.version(),
                rule.jarPath(),
                rule.jarSizeBytes(),
                rule.jarSha256()
        );
    }
}
