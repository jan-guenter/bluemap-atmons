package io.github.janguenter.bluemap.atmons.integration;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Optional;

/** UTF-8 JSON persistence with same-directory atomic replacement. */
final class JsonFiles {
    static final Gson GSON = new GsonBuilder()
            .setPrettyPrinting()
            .disableHtmlEscaping()
            .create();

    private JsonFiles() {
    }

    static <T> T read(Path path, Class<T> type) throws IOException {
        try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            T value = GSON.fromJson(reader, type);
            if (value == null) {
                throw new IOException("JSON document is null: " + path);
            }
            return value;
        } catch (JsonParseException exception) {
            throw new IOException("Invalid JSON: " + path, exception);
        }
    }

    static <T> T read(byte[] bytes, Class<T> type, Path source) throws IOException {
        try {
            T value = GSON.fromJson(new String(bytes, StandardCharsets.UTF_8), type);
            if (value == null) {
                throw new IOException("JSON document is null: " + source);
            }
            return value;
        } catch (JsonParseException exception) {
            throw new IOException("Invalid JSON: " + source, exception);
        }
    }

    static <T> Optional<T> readIfExists(Path path, Class<T> type) throws IOException {
        if (!Files.isRegularFile(path)) {
            return Optional.empty();
        }
        return Optional.of(read(path, type));
    }

    static void writeAtomic(Path path, Object value) throws IOException {
        Files.createDirectories(path.getParent());
        Path temporary = path.resolveSibling(path.getFileName() + ".tmp");
        try (Writer writer = Files.newBufferedWriter(temporary, StandardCharsets.UTF_8)) {
            GSON.toJson(value, writer);
        }
        try {
            Files.move(
                    temporary,
                    path,
                    StandardCopyOption.ATOMIC_MOVE,
                    StandardCopyOption.REPLACE_EXISTING
            );
        } catch (AtomicMoveNotSupportedException exception) {
            Files.move(temporary, path, StandardCopyOption.REPLACE_EXISTING);
        }
    }
}
