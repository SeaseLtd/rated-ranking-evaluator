package io.sease.rre.server;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

/**
 * Shared utilities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class Utility {
    /**
     * Returns the input JSON payload as a pretty formatted string.
     *
     * @param payload the JSON object.
     * @return the input JSON payload as a pretty formatted string.
     */
    public static String pretty(final JsonNode payload) {
        try {
            final ObjectMapper mapper = new ObjectMapper();
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(mapper.readTree(payload.asText()));
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }
}