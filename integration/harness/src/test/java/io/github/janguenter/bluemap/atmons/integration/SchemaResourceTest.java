package io.github.janguenter.bluemap.atmons.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class SchemaResourceTest {
    @Test
    void structureCatalogSchemaPinsVersionAndLocatedFields() throws IOException {
        JsonObject schema = resource("/bluemap-atmons/structure-catalog.schema.json");

        assertEquals("object", schema.get("type").getAsString());
        assertEquals(
                1,
                schema.getAsJsonObject("properties")
                        .getAsJsonObject("schemaVersion")
                        .get("const")
                        .getAsInt()
        );
        JsonObject selection = schema.getAsJsonObject("$defs")
                .getAsJsonObject("selection");
        assertTrue(selection.has("allOf"));
        JsonObject definitions = schema.getAsJsonObject("$defs");
        JsonObject mineshafts = definitions.getAsJsonObject(
                "betterMineshaftsConfigRule"
        );
        assertEquals(
                "/data/config/bettermineshafts-neoforge-1_21.toml",
                mineshafts.getAsJsonObject("properties")
                        .getAsJsonObject("configPath")
                        .get("const")
                        .getAsString()
        );
        JsonObject strongholds = definitions.getAsJsonObject(
                "betterStrongholdsModRule"
        );
        assertEquals(
                "a9cab2fc01538368862365691f7d215309801aed0b390351681b6b60a1db7b58",
                strongholds.getAsJsonObject("properties")
                        .getAsJsonObject("jarSha256")
                        .get("const")
                        .getAsString()
        );
    }

    @Test
    void gallerySchemaAcceptsComposerFunctionsAddedByTheAggregator() throws IOException {
        JsonObject schema = resource("/bluemap-atmons/gallery-layout.schema.json");

        JsonObject functions = schema.getAsJsonObject("$defs")
                .getAsJsonObject("functions");
        String required = functions.getAsJsonArray("required").toString();
        assertTrue(required.contains("load"));
        assertTrue(required.contains("release"));
    }

    private static JsonObject resource(String path) throws IOException {
        try (InputStream input = SchemaResourceTest.class.getResourceAsStream(path)) {
            if (input == null) {
                throw new IOException("Missing resource " + path);
            }
            return JsonParser.parseReader(
                    new InputStreamReader(input, StandardCharsets.UTF_8)
            ).getAsJsonObject();
        }
    }
}
