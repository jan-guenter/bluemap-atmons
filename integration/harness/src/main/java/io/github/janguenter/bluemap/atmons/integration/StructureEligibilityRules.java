package io.github.janguenter.bluemap.atmons.integration;

import com.electronwill.nightconfig.core.CommentedConfig;
import com.electronwill.nightconfig.toml.TomlParser;
import java.io.IOException;
import java.io.StringReader;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import net.neoforged.fml.ModList;

/** Exact ATMons 1.2.0 rules that remove otherwise-live structure placements. */
final class StructureEligibilityRules {
    static final Path EXPECTED_CONFIG_DIRECTORY = Path.of("/data/config");

    static final ConfigRuleSpec BETTER_DUNGEONS = new ConfigRuleSpec(
            "betterdungeons-small-nether-dungeons",
            "betterdungeons-neoforge-1_21.toml",
            List.of("YUNG's Better Dungeons", "Small Nether Dungeons"),
            "Enable Small Nether Dungeons",
            false,
            List.of("betterdungeons:small_nether_dungeon")
    );
    static final ConfigRuleSpec BETTER_MINESHAFTS = new ConfigRuleSpec(
            "bettermineshafts-disable-vanilla-mineshafts",
            "bettermineshafts-neoforge-1_21.toml",
            List.of("YUNG's Better Mineshafts"),
            "Disable Vanilla Mineshafts",
            true,
            List.of("minecraft:mineshaft", "minecraft:mineshaft_mesa")
    );
    static final ModRuleSpec BETTER_STRONGHOLDS = new ModRuleSpec(
            "betterstrongholds-disable-vanilla-strongholds-mixin",
            "betterstrongholds",
            "1.21.1-NeoForge-5.1.3",
            "/data/mods/YungsBetterStrongholds-1.21.1-NeoForge-5.1.3.jar",
            461_244L,
            "a9cab2fc01538368862365691f7d215309801aed0b390351681b6b60a1db7b58",
            List.of("minecraft:stronghold")
    );

    private static final List<ConfigRuleSpec> CONFIG_RULES = List.of(
            BETTER_DUNGEONS,
            BETTER_MINESHAFTS
    );
    private static final List<ModRuleSpec> MOD_RULES = List.of(BETTER_STRONGHOLDS);

    private StructureEligibilityRules() {
    }

    static StructureCatalog.StructureEligibilityEvidence loadCanonical() {
        try {
            Map<String, ObservedMod> loadedMods = new TreeMap<>();
            for (ModRuleSpec rule : MOD_RULES) {
                var modInfo = ModList.get()
                        .getModContainerById(rule.modId())
                        .orElseThrow(() -> new IllegalArgumentException(
                                "Required exact structure eligibility mod is absent: "
                                        + rule.modId()
                        ))
                        .getModInfo();
                Path jarPath = modInfo.getOwningFile()
                        .getFile()
                        .getFilePath()
                        .toAbsolutePath()
                        .normalize();
                loadedMods.put(rule.modId(), new ObservedMod(
                        modInfo.getVersion().toString(),
                        jarPath.toString(),
                        Files.size(jarPath),
                        RuntimeAttestation.sha256(Files.readAllBytes(jarPath))
                ));
            }
            StructureCatalog.StructureEligibilityEvidence evidence = load(
                    EXPECTED_CONFIG_DIRECTORY,
                    loadedMods
            );
            validateCatalogEvidence(evidence);
            return evidence;
        } catch (IOException | IllegalArgumentException exception) {
            throw new IllegalStateException(
                    "Could not validate exact ATMons structure eligibility evidence",
                    exception
            );
        }
    }

    static StructureCatalog.StructureEligibilityEvidence load(
            Path configDirectory,
            Map<String, ObservedMod> loadedMods
    ) throws IOException {
        Path normalizedDirectory = configDirectory.toAbsolutePath().normalize();
        List<StructureCatalog.StructureConfigRuleEvidence> configs = new ArrayList<>();
        for (ConfigRuleSpec rule : CONFIG_RULES) {
            configs.add(loadConfigRule(normalizedDirectory, rule));
        }

        List<StructureCatalog.StructureModRuleEvidence> mods = new ArrayList<>();
        for (ModRuleSpec rule : MOD_RULES) {
            ObservedMod observed = loadedMods.get(rule.modId());
            if (observed == null
                    || !rule.version().equals(observed.version())
                    || !rule.jarPath().equals(observed.jarPath())
                    || rule.jarSizeBytes() != observed.jarSizeBytes()
                    || !rule.jarSha256().equals(observed.jarSha256())) {
                throw new IllegalArgumentException(
                        "Loaded mod does not match exact artifact rule "
                                + rule.ruleId()
                );
            }
            mods.add(new StructureCatalog.StructureModRuleEvidence(
                    rule.ruleId(),
                    rule.modId(),
                    observed.version(),
                    observed.jarPath(),
                    observed.jarSizeBytes(),
                    observed.jarSha256(),
                    rule.structures()
            ));
        }

        return assembleEvidence(List.copyOf(configs), List.copyOf(mods));
    }

    static StructureCatalog.StructureEligibilityEvidence assembleEvidence(
            List<StructureCatalog.StructureConfigRuleEvidence> configs,
            List<StructureCatalog.StructureModRuleEvidence> mods
    ) {
        StructureCatalog.StructureEligibilityEvidence partial =
                new StructureCatalog.StructureEligibilityEvidence(
                        List.copyOf(configs),
                        List.copyOf(mods),
                        List.of()
                );
        return new StructureCatalog.StructureEligibilityEvidence(
                partial.configRules(),
                partial.modRules(),
                deriveDisabledStructures(partial)
        );
    }

    static void validateCatalogEvidence(
            StructureCatalog.StructureEligibilityEvidence evidence
    ) {
        if (evidence == null
                || evidence.configRules() == null
                || evidence.modRules() == null
                || evidence.disabledStructures() == null
                || evidence.configRules().size() != CONFIG_RULES.size()
                || evidence.modRules().size() != MOD_RULES.size()) {
            throw new IllegalArgumentException(
                    "Catalog lacks exact structure eligibility evidence"
            );
        }

        for (int index = 0; index < CONFIG_RULES.size(); index++) {
            ConfigRuleSpec expected = CONFIG_RULES.get(index);
            StructureCatalog.StructureConfigRuleEvidence actual =
                    evidence.configRules().get(index);
            Path expectedPath = EXPECTED_CONFIG_DIRECTORY.resolve(
                    expected.fileName()
            );
            if (actual == null
                    || !expected.ruleId().equals(actual.ruleId())
                    || !expectedPath.toString().equals(actual.configPath())
                    || actual.configSha256() == null
                    || !actual.configSha256().matches("[0-9a-f]{64}")
                    || !expected.section().equals(actual.section())
                    || !expected.key().equals(actual.key())
                    || expected.disabledWhenValue() != actual.disabledWhenValue()
                    || !expected.structures().equals(actual.structures())) {
                throw new IllegalArgumentException(
                        "Catalog has invalid config eligibility rule "
                                + expected.ruleId()
                );
            }
        }

        for (int index = 0; index < MOD_RULES.size(); index++) {
            ModRuleSpec expected = MOD_RULES.get(index);
            StructureCatalog.StructureModRuleEvidence actual =
                    evidence.modRules().get(index);
            if (actual == null
                    || !expected.ruleId().equals(actual.ruleId())
                    || !expected.modId().equals(actual.modId())
                    || !expected.version().equals(actual.version())
                    || !expected.jarPath().equals(actual.jarPath())
                    || expected.jarSizeBytes() != actual.jarSizeBytes()
                    || !expected.jarSha256().equals(actual.jarSha256())
                    || !expected.structures().equals(actual.structures())) {
                throw new IllegalArgumentException(
                        "Catalog has invalid mod eligibility rule " + expected.ruleId()
                );
            }
        }

        List<StructureCatalog.DisabledStructureEvidence> expectedDisabled =
                deriveDisabledStructures(new StructureCatalog.StructureEligibilityEvidence(
                        evidence.configRules(),
                        evidence.modRules(),
                        List.of()
                ));
        if (!expectedDisabled.equals(evidence.disabledStructures())) {
            throw new IllegalArgumentException(
                    "Catalog disabled structures do not match their exact evidence"
            );
        }
    }

    static Map<String, String> disabledReasons(
            StructureCatalog.StructureEligibilityEvidence evidence
    ) {
        validateCatalogEvidence(evidence);
        Map<String, String> reasons = new LinkedHashMap<>();
        for (StructureCatalog.DisabledStructureEvidence disabled
                : evidence.disabledStructures()) {
            if (reasons.put(disabled.structure(), disabled.reason()) != null) {
                throw new IllegalArgumentException(
                        "Structure has duplicate eligibility evidence: "
                                + disabled.structure()
                );
            }
        }
        return Map.copyOf(reasons);
    }

    static List<String> declaredStructures(
            StructureCatalog.StructureEligibilityEvidence evidence
    ) {
        validateCatalogEvidence(evidence);
        return java.util.stream.Stream.concat(
                        evidence.configRules().stream()
                                .flatMap(rule -> rule.structures().stream()),
                        evidence.modRules().stream()
                                .flatMap(rule -> rule.structures().stream())
                )
                .distinct()
                .sorted()
                .toList();
    }

    static String fingerprintComponent(
            StructureCatalog.StructureEligibilityEvidence evidence
    ) {
        validateCatalogEvidence(evidence);
        List<String> lines = new ArrayList<>();
        for (StructureCatalog.StructureConfigRuleEvidence rule
                : evidence.configRules()) {
            lines.add("config|" + rule.ruleId()
                    + "|path=" + rule.configPath()
                    + "|sha256=" + rule.configSha256()
                    + "|section=" + String.join("/", rule.section())
                    + "|key=" + rule.key()
                    + "|value=" + rule.value()
                    + "|disabled-when=" + rule.disabledWhenValue()
                    + "|structures=" + String.join(",", rule.structures()));
        }
        for (StructureCatalog.StructureModRuleEvidence rule : evidence.modRules()) {
            lines.add("mod|" + rule.ruleId()
                    + "|mod-id=" + rule.modId()
                    + "|version=" + rule.version()
                    + "|jar-path=" + rule.jarPath()
                    + "|jar-size=" + rule.jarSizeBytes()
                    + "|jar-sha256=" + rule.jarSha256()
                    + "|structures=" + String.join(",", rule.structures()));
        }
        for (StructureCatalog.DisabledStructureEvidence disabled
                : evidence.disabledStructures()) {
            lines.add("disabled|" + disabled.structure()
                    + "|evidence=" + disabled.evidenceId()
                    + "|reason=" + disabled.reason());
        }
        return String.join("\n", lines);
    }

    private static StructureCatalog.StructureConfigRuleEvidence loadConfigRule(
            Path configDirectory,
            ConfigRuleSpec rule
    ) throws IOException {
        Path path = configDirectory.resolve(rule.fileName()).normalize();
        if (!path.getParent().equals(configDirectory)
                || !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("Missing exact pack config " + path);
        }
        byte[] bytes = Files.readAllBytes(path);
        String text;
        try {
            text = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes))
                    .toString();
        } catch (CharacterCodingException exception) {
            throw new IllegalArgumentException(
                    "Pack config is not valid UTF-8: " + path,
                    exception
            );
        }

        CommentedConfig parsed;
        try {
            parsed = new TomlParser().parse(new StringReader(text));
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException(
                    "Pack config is malformed TOML: " + path,
                    exception
            );
        }
        List<String> valuePath = new ArrayList<>(rule.section());
        valuePath.add(rule.key());
        Object raw = parsed.getRaw(valuePath);
        if (!(raw instanceof Boolean value)) {
            throw new IllegalArgumentException(
                    "Pack config lacks exact boolean " + sectionText(rule.section())
                            + ".\"" + rule.key() + "\": " + path
            );
        }
        return new StructureCatalog.StructureConfigRuleEvidence(
                rule.ruleId(),
                path.toAbsolutePath().normalize().toString(),
                RuntimeAttestation.sha256(bytes),
                rule.section(),
                rule.key(),
                value,
                rule.disabledWhenValue(),
                rule.structures()
        );
    }

    private static List<StructureCatalog.DisabledStructureEvidence>
            deriveDisabledStructures(
                    StructureCatalog.StructureEligibilityEvidence evidence
            ) {
        TreeMap<String, StructureCatalog.DisabledStructureEvidence> disabled =
                new TreeMap<>();
        for (StructureCatalog.StructureConfigRuleEvidence rule
                : evidence.configRules()) {
            if (rule.value() != rule.disabledWhenValue()) {
                continue;
            }
            for (String structure : rule.structures()) {
                addDisabled(disabled, new StructureCatalog.DisabledStructureEvidence(
                        structure,
                        rule.ruleId(),
                        "Disabled by exact pack config " + rule.configPath() + " "
                                + sectionText(rule.section()) + ".\"" + rule.key()
                                + "\" = " + rule.value()
                ));
            }
        }
        for (StructureCatalog.StructureModRuleEvidence rule : evidence.modRules()) {
            for (String structure : rule.structures()) {
                addDisabled(disabled, new StructureCatalog.DisabledStructureEvidence(
                        structure,
                        rule.ruleId(),
                        "Disabled by exact loaded mod " + rule.modId() + " "
                                + rule.version() + " under the runtime attestation"
                ));
            }
        }
        return List.copyOf(disabled.values());
    }

    private static void addDisabled(
            Map<String, StructureCatalog.DisabledStructureEvidence> disabled,
            StructureCatalog.DisabledStructureEvidence evidence
    ) {
        if (disabled.put(evidence.structure(), evidence) != null) {
            throw new IllegalArgumentException(
                    "Structure has multiple disabling rules: " + evidence.structure()
            );
        }
    }

    private static String sectionText(List<String> section) {
        return "[" + section.stream()
                .map(part -> "\"" + part + "\"")
                .collect(java.util.stream.Collectors.joining(".")) + "]";
    }

    record ConfigRuleSpec(
            String ruleId,
            String fileName,
            List<String> section,
            String key,
            boolean disabledWhenValue,
            List<String> structures
    ) {
    }

    record ModRuleSpec(
            String ruleId,
            String modId,
            String version,
            String jarPath,
            long jarSizeBytes,
            String jarSha256,
            List<String> structures
    ) {
    }

    record ObservedMod(
            String version,
            String jarPath,
            long jarSizeBytes,
            String jarSha256
    ) {
    }
}
