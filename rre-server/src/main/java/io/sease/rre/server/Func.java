package io.sease.rre.server;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.util.UUID;

public class Func {
    final ObjectMapper mapper = new ObjectMapper();

    public boolean isZero(final BigDecimal v) {
        return v != null && v.doubleValue() == 0;
    }

    public boolean isPositive(final BigDecimal v) {
        return v.compareTo(BigDecimal.ZERO) > 0;
    }

    /**
     * Returns the input JSON payload as a pretty formatted string.
     *
     * @param payload the JSON object.
     * @return the input JSON payload as a pretty formatted string.
     */
    public String pretty(final String payload) {
        try {
            final String q = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(mapper.readTree(payload)).replaceFirst("\\{", "");
            return q.substring(0, q.length()-1).trim().replace("\n", "<br/>");
        } catch (final Exception exception) {
            return payload;
        }
    }

    public String id(final String value) {
        return UUID.nameUUIDFromBytes(value.getBytes()).toString();
    }
}
