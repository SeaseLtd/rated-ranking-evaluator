package io.sease.rre.maven.plugin.report;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.stream.Stream;
import java.util.stream.StreamSupport;

public abstract class Utility {

    public static String pretty(final JsonNode node) {
        try {
            final ObjectMapper mapper = new ObjectMapper();
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(mapper.readTree(node.asText()));
        } catch (Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    public static Stream<JsonNode> all(final JsonNode parent, final String name) {
        return StreamSupport.stream(parent.get(name).spliterator(), false);
    }
}
